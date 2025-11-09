const API_BASE_URL = 'https://hjbdhmmzi2.us-east-1.awsapprunner.com';

// Global state
let productData = null;

// Auto-fetch product info when extension opens
document.addEventListener('DOMContentLoaded', async function() {
  setupTabHandlers();
  await autoFetchProductInfo();
});

// Setup tab switching
function setupTabHandlers() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabName = btn.dataset.tab;
      switchTab(tabName);
    });
  });
}

// Switch between tabs
function switchTab(tabName) {
  // Update tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabName);
  });

  // Update tab content
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('active', content.id === tabName);
  });
}

// Show error message
function showError(message) {
  document.getElementById('loading').classList.add('hidden');
  document.getElementById('content').classList.add('hidden');
  const errorDiv = document.getElementById('error');
  errorDiv.textContent = message;
  errorDiv.classList.remove('hidden');
}

// Auto-fetch product info on load
async function autoFetchProductInfo() {
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});

    // Step 1: Extract UPC from page
    const result = await chrome.scripting.executeScript({
      target: {tabId: tab.id},
      func: extractUPC
    });

    const upc = result[0].result;
    console.log('Extracted UPC:', upc);

    if (!upc) {
      showError('Could not find product UPC on this page.');
      return;
    }

    // Step 2: Fetch only sustainability score first (fast!)
    await fetchProductData(upc);

    // Step 3: Show content immediately
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('content').classList.remove('hidden');

    // Step 4: Load other tabs in background (deferred)
    // Order: ingredients -> recommendations -> summary
    fetchIngredients(upc).then(() => {
      console.log('Ingredients loaded in background');
    });

    // Recommendations are already loaded with sustainability_score
    // No need for separate call

    // Load summary last (slowest due to AI)
    fetchSummary(upc).then(() => {
      console.log('Summary loaded in background');
    });

  } catch (error) {
    console.error('Error:', error);
    showError('Error loading product information: ' + error.message);
  }
}

// Extract UPC from Walmart page (runs in page context)
async function extractUPC() {
  // Helper: Wait for element
  function waitForElement(selector, timeout = 5000) {
    return new Promise((resolve) => {
      if (document.querySelector(selector)) {
        return resolve(document.querySelector(selector));
      }
      const observer = new MutationObserver(() => {
        if (document.querySelector(selector)) {
          observer.disconnect();
          resolve(document.querySelector(selector));
        }
      });
      observer.observe(document.body, { childList: true, subtree: true });
      setTimeout(() => { observer.disconnect(); resolve(null); }, timeout);
    });
  }

  // Helper: Click button by text
  function clickButtonByText(text) {
    const buttons = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
    const button = buttons.find(btn => btn.textContent.includes(text));
    if (button) { button.click(); return true; }
    return false;
  }

  // Helper: Extract from modal
  function extractFromModal() {
    // Method 1: XPath
    const xpathResult = document.evaluate(
      '//h3[contains(text(), "Universal Product Code")]/following-sibling::div/span',
      document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
    );
    if (xpathResult.singleNodeValue) {
      const text = xpathResult.singleNodeValue.textContent.trim();
      if (/\d{8,}/.test(text)) return text.match(/\d{8,}/)[0];
    }

    // Method 2: h3 search
    const h3s = document.querySelectorAll('h3');
    for (let h3 of h3s) {
      if (h3.textContent.includes('Universal Product Code')) {
        const sibling = h3.nextElementSibling;
        if (sibling) {
          const span = sibling.querySelector('span');
          if (span && /\d{8,}/.test(span.textContent)) {
            return span.textContent.trim().match(/\d{8,}/)[0];
          }
        }
      }
    }
    return null;
  }

  // Try structured data first
  const scripts = document.querySelectorAll('script[type="application/ld+json"]');
  for (let script of scripts) {
    try {
      const data = JSON.parse(script.textContent);
      const upc = data.gtin || data.gtin12 || data.gtin13 || data.upc;
      if (upc && /\d{8,}/.test(upc)) return upc;
    } catch (e) {}
  }

  // Try window data
  if (window.__NEXT_DATA__) {
    const jsonStr = JSON.stringify(window.__NEXT_DATA__);
    const match = jsonStr.match(/"gtin(?:12|13)?"\s*:\s*"(\d{8,})"/);
    if (match) return match[1];
  }

  // Check if already visible
  let upc = extractFromModal();
  if (upc) return upc;

  // Open modal as last resort
  clickButtonByText('View full item details') || clickButtonByText('full item details');
  await new Promise(r => setTimeout(r, 500));
  clickButtonByText('More details');
  await new Promise(r => setTimeout(r, 800));

  return extractFromModal();
}

// Fetch product data and sustainability scores
async function fetchProductData(upc) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/products/${upc}?sustainability_score=true&recommendations=true`);
    if (!response.ok) throw new Error(`API returned ${response.status}`);

    const data = await response.json();
    console.log('Product data:', data);

    if (data.status === 'success' && data.data) {
      productData = data.data;
      displayOverview(data.data);
      displayRecommendations(data.data.recommendations || [], data.data.similar_products || []);
    } else {
      throw new Error('Product not found');
    }
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
}

// Fetch ingredients
async function fetchIngredients(upc) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/products/${upc}?ingredients=true`);
    if (!response.ok) return;

    const data = await response.json();
    console.log('Ingredients data:', data);

    if (data.status === 'success' && data.data) {
      // Ingredients analysis is at data.ingredients_analysis level
      if (data.data.ingredients_analysis) {
        displayIngredients(data.data.ingredients_analysis);
      } else {
        // No ingredients available
        document.getElementById('noIngredients').classList.remove('hidden');
      }
    }
  } catch (error) {
    console.error('Ingredients fetch error:', error);
    document.getElementById('noIngredients').classList.remove('hidden');
  }
}

// Fetch summary
async function fetchSummary(upc) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/products/${upc}?summary=true`);
    if (!response.ok) return;

    const data = await response.json();
    console.log('Summary data:', data);

    if (data.status === 'success' && data.data && data.data.ai_summary) {
      displaySummary(data.data.ai_summary);
    }
  } catch (error) {
    console.error('Summary fetch error:', error);
  }
}

// Display Overview Tab
function displayOverview(data) {
  const product = data.product;
  const sustainability = data.sustainability_scores;

  // Product info
  document.getElementById('productName').textContent = product.product_name || 'Unknown Product';
  document.getElementById('productBrand').textContent = product.brand || 'Unknown Brand';
  document.getElementById('productQuantity').textContent = product.quantity || '';
  document.getElementById('productPrice').textContent = product.price ? `$${product.price}` : '';

  const imageUrl = product.image_url || product.image_small_url;
  if (imageUrl) {
    document.getElementById('productImage').src = imageUrl;
    document.getElementById('productImage').style.display = 'block';
  }

  // Sustainability score
  if (sustainability) {
    const grade = sustainability.grade || 'N/A';
    const score = sustainability.total_score || 0;

    document.getElementById('sustainabilityGrade').textContent = grade;
    document.getElementById('sustainabilityGrade').className = 'grade-letter grade-' + grade.toLowerCase();
    document.getElementById('sustainabilityScore').textContent = Math.round(score);

    // Display metrics - pass product data for manufacturing location
    if (sustainability.metrics) {
      displayMetrics(sustainability.metrics, product.manufacturing_places);
    }
  }

  // Ecoscore - removed, not displaying
}

// Display sustainability metrics
function displayMetrics(metrics, manufacturingPlaces) {
  const container = document.getElementById('metricsContainer');
  container.innerHTML = '';

  for (const [key, metric] of Object.entries(metrics)) {
    const metricDiv = document.createElement('div');
    metricDiv.className = 'metric-item';

    const name = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    const score = metric.score || 0;
    const scoreColor = score >= 0 ? '#2ecc71' : '#ff5722';

    let details = '';

    // CO2 details
    if (metric.co2_kg_per_kg !== undefined && metric.co2_kg_per_kg !== null) {
      details += `<div class="metric-detail">CO<sub>2</sub>: ${metric.co2_kg_per_kg} kg/kg</div>`;
    }
    if (metric.co2_kg !== undefined && metric.co2_kg !== null) {
      details += `<div class="metric-detail">CO<sub>2</sub>: ${metric.co2_kg} kg</div>`;
    }
    if (metric.co2_per_100_calories !== undefined && metric.co2_per_100_calories !== null) {
      details += `<div class="metric-detail">CO<sub>2</sub> per 100 cal: ${metric.co2_per_100_calories}</div>`;
    }

    // Other details
    // For transportation, show manufacturing location instead of distance
    if (key === 'transportation' && manufacturingPlaces) {
      details += `<div class="metric-detail">From: ${manufacturingPlaces}</div>`;
    } else if (metric.distance_km) {
      details += `<div class="metric-detail">Distance: ${Math.round(metric.distance_km)} km</div>`;
    }

    if (metric.transport_mode) {
      const mode = metric.transport_mode.replace(/_/g, ' + ').replace(/\b\w/g, l => l.toUpperCase());
      details += `<div class="metric-detail">Transport: ${mode}</div>`;
    }
    if (metric.calories_100g) {
      details += `<div class="metric-detail">Calories: ${metric.calories_100g} per 100g</div>`;
    }
    if (metric.efficiency_rating) {
      details += `<div class="metric-detail">Rating: ${metric.efficiency_rating}</div>`;
    }
    if (metric.confidence) {
      details += `<div class="metric-detail">Confidence: ${metric.confidence}</div>`;
    }

    metricDiv.innerHTML = `
      <div class="metric-header">
        <span class="metric-name">${name}</span>
        <span class="metric-score" style="color: ${scoreColor}">${score > 0 ? '+' : ''}${score} pts</span>
      </div>
      ${details}
    `;

    container.appendChild(metricDiv);
  }
}

// Display Ingredients Tab
function displayIngredients(ingredientsData) {
  if (!ingredientsData.data_available || ingredientsData.ingredients.length === 0) {
    document.getElementById('noIngredients').classList.remove('hidden');
    return;
  }

  const list = document.getElementById('ingredientsList');
  list.innerHTML = '';

  ingredientsData.ingredients.forEach(ingredient => {
    const item = document.createElement('div');
    item.className = `ingredient-item ${ingredient.classification}`;

    const icon = ingredient.classification === 'good' ? '&check;' : '?';
    const iconClass = ingredient.classification === 'good' ? 'check-icon' : 'question-icon';

    item.innerHTML = `
      <div class="ingredient-header">
        <span class="${iconClass}">${icon}</span>
        <span class="ingredient-name">${ingredient.name}</span>
      </div>
      ${ingredient.health_concerns ? `
        <div class="ingredient-concerns hidden">
          <strong>Concerns:</strong> ${ingredient.health_concerns}
        </div>
      ` : ''}
    `;

    // Make concerns expandable on click
    if (ingredient.health_concerns) {
      item.style.cursor = 'pointer';
      item.addEventListener('click', () => {
        const concerns = item.querySelector('.ingredient-concerns');
        concerns.classList.toggle('hidden');
      });
    }

    list.appendChild(item);
  });
}

// Display Recommendations Tab
function displayRecommendations(recommendations, similarProducts) {
  const list = document.getElementById('recommendationsList');
  list.innerHTML = '';

  // Show recommendations first (better alternatives)
  if (recommendations && recommendations.length > 0) {
    const recSection = document.createElement('div');
    recSection.className = 'rec-section';
    recSection.innerHTML = '<h3 class="rec-section-title">Better Alternatives</h3>';

    recommendations.forEach(rec => {
      const product = rec.product;
      const card = document.createElement('div');
      card.className = 'recommendation-card';

      const imageUrl = product.image_small_url || '';
      const hasBrand = product.brand && product.brand.trim();
      const hasPrice = product.price !== null && product.price !== undefined;

      card.innerHTML = `
        ${imageUrl ? `<img src="${imageUrl}" alt="${product.product_name}" class="rec-image">` : '<div class="rec-image-placeholder"></div>'}
        <div class="rec-details">
          <h3>${product.product_name}</h3>
          ${hasBrand ? `<p class="rec-brand">${product.brand}</p>` : ''}
          ${hasPrice ? `<p class="rec-price">$${product.price}</p>` : ''}
          <div class="rec-score">
            <span class="rec-grade grade-${rec.grade.toLowerCase()}">${rec.grade}</span>
            <span class="rec-improvement">+${rec.score_improvement} pts</span>
          </div>
          <p class="rec-reason">${rec.reason}</p>
        </div>
      `;

      recSection.appendChild(card);
    });

    list.appendChild(recSection);
  }

  // Show similar products (same category)
  if (similarProducts && similarProducts.length > 0) {
    const simSection = document.createElement('div');
    simSection.className = 'rec-section';
    simSection.innerHTML = '<h3 class="rec-section-title">Similar Products</h3>';

    similarProducts.forEach(product => {
      const card = document.createElement('div');
      card.className = 'recommendation-card similar';

      const imageUrl = product.image_small_url || '';
      const hasBrand = product.brand && product.brand.trim();
      const hasPrice = product.price !== null && product.price !== undefined;

      card.innerHTML = `
        ${imageUrl ? `<img src="${imageUrl}" alt="${product.product_name}" class="rec-image">` : ''}
        <div class="rec-details">
          <h3>${product.product_name}</h3>
          ${hasBrand ? `<p class="rec-brand">${product.brand}</p>` : ''}
          ${hasPrice ? `<p class="rec-price">$${product.price}</p>` : ''}
          ${product.category ? `<p class="rec-category">${product.category}</p>` : ''}
        </div>
      `;

      simSection.appendChild(card);
    });

    list.appendChild(simSection);
  }

  // Show message if no data
  if ((!recommendations || recommendations.length === 0) && (!similarProducts || similarProducts.length === 0)) {
    document.getElementById('noRecommendations').classList.remove('hidden');
  } else {
    document.getElementById('noRecommendations').classList.add('hidden');
  }
}

// Display Summary Tab
function displaySummary(summary) {
  if (!summary) {
    document.getElementById('noSummary').textContent = 'Summary not available';
    document.getElementById('noSummary').classList.remove('hidden');
    return;
  }

  const content = document.getElementById('summaryContent');
  content.textContent = summary;
  content.classList.remove('hidden');
  document.getElementById('noSummary').classList.add('hidden');
}
