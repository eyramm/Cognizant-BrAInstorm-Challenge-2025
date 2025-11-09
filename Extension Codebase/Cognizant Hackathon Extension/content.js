// Helper function to wait for element to appear
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

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    setTimeout(() => {
      observer.disconnect();
      resolve(null);
    }, timeout);
  });
}

// Helper function to find and click button by text content
function clickButtonByText(text) {
  const buttons = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
  const button = buttons.find(btn => btn.textContent.includes(text));
  if (button) {
    button.click();
    return true;
  }
  return false;
}

// Extract UPC from the modal
function extractUPCFromModal() {
  // Method 1: Use XPath to find UPC heading and get sibling value (most robust)
  const xpathResult = document.evaluate(
    '//h3[contains(text(), "Universal Product Code")]/following-sibling::div/span',
    document,
    null,
    XPathResult.FIRST_ORDERED_NODE_TYPE,
    null
  );

  if (xpathResult.singleNodeValue) {
    const upcText = xpathResult.singleNodeValue.textContent.trim();
    if (/\d{8,}/.test(upcText)) {
      return upcText.match(/\d{8,}/)[0];
    }
  }

  // Method 2: Look for any h3 element containing UPC text and get following sibling
  const h3Elements = document.querySelectorAll('h3');
  for (let h3 of h3Elements) {
    if (h3.textContent.includes('Universal Product Code') || h3.textContent.includes('UPC')) {
      let valueNode = h3.nextElementSibling;
      if (valueNode) {
        const upcSpan = valueNode.querySelector('span');
        if (upcSpan && /\d{8,}/.test(upcSpan.textContent)) {
          return upcSpan.textContent.trim().match(/\d{8,}/)[0];
        }
        if (/\d{8,}/.test(valueNode.textContent)) {
          return valueNode.textContent.trim().match(/\d{8,}/)[0];
        }
      }
    }
  }

  // Method 3: Search all elements for exact label match
  const elements = document.querySelectorAll('div, span, p, li, strong, b, h3');
  for (let el of elements) {
    const text = el.textContent.trim();
    if (text === 'Universal Product Code (UPC check)' || text.includes('Universal Product Code')) {
      let valueNode = el.nextElementSibling;
      if (valueNode && /\d{8,}/.test(valueNode.textContent)) {
        return valueNode.textContent.match(/\d{8,}/)[0];
      }
      if (el.parentNode && el.parentNode.childNodes.length >= 2) {
        let s = Array.from(el.parentNode.childNodes)
          .map(n => n.textContent)
          .join(' ');
        let match = s.match(/Universal Product Code[^\d]*(\d{8,})/);
        if (match) return match[1];
      }
    }
  }

  return null;
}

async function scrapeUPC() {
  // First, check if UPC is already visible (maybe modal is open)
  let upc = extractUPCFromModal();
  if (upc) return upc;

  // Step 1: Click "View full item details" or similar button
  const detailsClicked = clickButtonByText('View full item details') ||
                         clickButtonByText('full item details') ||
                         clickButtonByText('Item details');

  if (detailsClicked) {
    await new Promise(resolve => setTimeout(resolve, 500)); // Wait for content to load
  }

  // Step 2: Click "More details" button
  const moreDetailsClicked = clickButtonByText('More details');

  if (moreDetailsClicked) {
    await new Promise(resolve => setTimeout(resolve, 800)); // Wait for modal to appear
  }

  // Step 3: Try to extract UPC from the now-visible modal
  upc = extractUPCFromModal();
  if (upc) return upc;

  // Step 4: If modal has specific selectors, wait for it
  const modal = await waitForElement('[role="dialog"], .modal, [class*="modal"]', 2000);
  if (modal) {
    upc = extractUPCFromModal();
    if (upc) return upc;
  }

  // Fallback: search entire page text
  const upcFallback = document.body.innerText.match(/UPC[^\d]*(\d{8,})/);
  if (upcFallback) return upcFallback[1];

  return null;
}


chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getUPC") {
    scrapeUPC().then(upc => {
      sendResponse({ upc });
    });
    return true; // Required for async sendResponse
  }
});
