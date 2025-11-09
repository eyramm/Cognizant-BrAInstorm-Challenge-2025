import { View, Text, ScrollView, ActivityIndicator, StyleSheet, Image, TouchableOpacity, Dimensions } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { API_BASE_URL } from '../../config/constants';

const { width } = Dimensions.get('window');

interface Product {
  brand: string;
  ecoscore_grade: string | null;
  ecoscore_score: number | null;
  image_small_url: string;
  image_url: string;
  manufacturing_places: string;
  nova_group: number;
  product_name: string;
  quantity: string;
  upc: string;
  primary_category: string;
}

interface SustainabilityScores {
  grade: string;
  total_score: number;
  metrics: {
    climate_efficiency?: {
      score: number;
      efficiency_rating: string;
      co2_per_100g_protein: number;
      confidence: string;
    };
    packaging?: {
      score: number;
      co2_kg_per_kg: number;
      confidence: string;
    };
    raw_materials?: {
      score: number;
      co2_kg_per_kg: number;
      confidence: string;
    };
  };
}

interface SimilarProduct {
  brand: string | null;
  category: string;
  image_small_url: string;
  product_name: string;
  upc: string;
}

interface Ingredient {
  classification: 'good' | 'caution' | 'harmful';
  name: string;
  percent: number;
  rank: number;
  vegan?: string;
  vegetarian?: string;
}

interface IngredientsAnalysis {
  data_available: boolean;
  ingredients: Ingredient[];
  summary: {
    caution: number;
    good: number;
    harmful: number;
    total: number;
  };
}

interface Recommendation {
  grade: string;
  harmful_ingredients: number;
  product: {
    brand: string;
    category: string;
    image_small_url: string;
    product_name: string;
    upc: string;
    price: number | null;
  };
  reason: string;
  score_improvement: number;
  sustainability_score: number;
}

type TabType = 'score' | 'ingredients' | 'recommendations' | 'summary';

export default function ProductDetailsScreen() {
  const { barcode } = useLocalSearchParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [sustainabilityScores, setSustainabilityScores] = useState<SustainabilityScores | null>(null);
  const [similarProducts, setSimilarProducts] = useState<SimilarProduct[]>([]);
  const [ingredientsAnalysis, setIngredientsAnalysis] = useState<IngredientsAnalysis | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [aiSummary, setAiSummary] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('score');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabLoading, setTabLoading] = useState<{[key in TabType]?: boolean}>({});

  useEffect(() => {
    fetchProductDetails();
  }, [barcode]);

  useEffect(() => {
    // Fetch data when tab changes
    if (activeTab === 'ingredients' && !ingredientsAnalysis && !tabLoading.ingredients) {
      fetchIngredients();
    } else if (activeTab === 'recommendations' && recommendations.length === 0 && !tabLoading.recommendations) {
      fetchRecommendations();
    } else if (activeTab === 'summary' && !aiSummary && !tabLoading.summary) {
      fetchSummary();
    }
  }, [activeTab]);

  const fetchProductDetails = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch sustainability score first
      const response = await axios.get(
        `${API_BASE_URL}/api/products/${barcode}?sustainability_score=true`
      );

      if (response.data.status === 'success' && response.data.data) {
        setProduct(response.data.data.product);
        setSustainabilityScores(response.data.data.sustainability_scores);
        setSimilarProducts(response.data.data.similar_products || []);
      } else {
        setError('Product not found');
      }
    } catch (err: any) {
      console.error('Error fetching product:', err);
      if (err.code === 'ERR_NETWORK' || err.message === 'Network Error') {
        setError('Cannot connect to server. Please ensure:\n• Your device and server are on the same WiFi network\n• The API server is running at ' + API_BASE_URL);
      } else {
        setError(err.response?.data?.message || err.message || 'Failed to fetch product details');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchIngredients = async () => {
    try {
      setTabLoading(prev => ({ ...prev, ingredients: true }));
      const response = await axios.get(
        `${API_BASE_URL}/api/products/${barcode}?summary=true`
      );
      if (response.data.status === 'success' && response.data.data) {
        setIngredientsAnalysis(response.data.data.ingredients_analysis || null);
      }
    } catch (err: any) {
      console.error('Error fetching ingredients:', err);
    } finally {
      setTabLoading(prev => ({ ...prev, ingredients: false }));
    }
  };

  const fetchRecommendations = async () => {
    try {
      setTabLoading(prev => ({ ...prev, recommendations: true }));
      const response = await axios.get(
        `${API_BASE_URL}/api/products/${barcode}?recommendations=true`
      );
      if (response.data.status === 'success' && response.data.data) {
        setRecommendations(response.data.data.recommendations || []);
      }
    } catch (err: any) {
      console.error('Error fetching recommendations:', err);
    } finally {
      setTabLoading(prev => ({ ...prev, recommendations: false }));
    }
  };

  const fetchSummary = async () => {
    try {
      setTabLoading(prev => ({ ...prev, summary: true }));
      const response = await axios.get(
        `${API_BASE_URL}/api/products/${barcode}?summary=true`
      );
      if (response.data.status === 'success' && response.data.data) {
        setAiSummary(response.data.data.ai_summary || null);
      }
    } catch (err: any) {
      console.error('Error fetching summary:', err);
    } finally {
      setTabLoading(prev => ({ ...prev, summary: false }));
    }
  };

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return '#22c55e';
      case 'B': return '#86efac';
      case 'C': return '#eab308';
      case 'D': return '#f97316';
      case 'E': return '#ef4444';
      default: return '#9ca3af';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#eab308';
    if (score >= 40) return '#f97316';
    return '#ef4444';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#22c55e" />
        <Text style={styles.loadingText}>Analyzing product sustainability...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.loadingContainer}>
        <MaterialCommunityIcons name="alert-circle" size={64} color="#ef4444" />
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  if (!product) {
    return (
      <View style={styles.loadingContainer}>
        <MaterialCommunityIcons name="package-variant" size={64} color="#9ca3af" />
        <Text style={styles.errorText}>Product not found</Text>
      </View>
    );
  }

  const renderTabContent = () => {
    if (activeTab === 'score') {
      return renderScoreTab();
    } else if (activeTab === 'ingredients') {
      return renderIngredientsTab();
    } else if (activeTab === 'recommendations') {
      return renderRecommendationsTab();
    } else if (activeTab === 'summary') {
      return renderSummaryTab();
    }
  };

  const renderScoreTab = () => (
    <>
      {/* Sustainability Score */}
      {sustainabilityScores && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Sustainability Score</Text>

          <View style={styles.gradeContainer}>
            <View style={[styles.gradeBadge, { backgroundColor: getGradeColor(sustainabilityScores.grade) }]}>
              <Text style={styles.gradeText}>{sustainabilityScores.grade}</Text>
            </View>
            <View style={styles.scoreDetails}>
              <Text style={[styles.scoreNumber, { color: getScoreColor(sustainabilityScores.total_score) }]}>
                {sustainabilityScores.total_score}/100
              </Text>
              <Text style={styles.scoreLabel}>Overall Score</Text>
            </View>
          </View>

          {/* Metrics Breakdown */}
          <View style={styles.metricsContainer}>
            <Text style={styles.metricsTitle}>Score Breakdown</Text>

            {sustainabilityScores.metrics.climate_efficiency && (
              <View style={styles.metricRow}>
                <View style={styles.metricLeft}>
                  <MaterialCommunityIcons name="leaf" size={20} color="#22c55e" />
                  <Text style={styles.metricLabel}>Climate Efficiency</Text>
                </View>
                <View style={styles.metricRight}>
                  <Text style={[styles.metricScore, { color: getScoreColor(sustainabilityScores.metrics.climate_efficiency.score + 50) }]}>
                    {sustainabilityScores.metrics.climate_efficiency.score}
                  </Text>
                  <Text style={styles.metricRating}>{sustainabilityScores.metrics.climate_efficiency.efficiency_rating}</Text>
                </View>
              </View>
            )}

            {sustainabilityScores.metrics.packaging && (
              <View style={styles.metricRow}>
                <View style={styles.metricLeft}>
                  <MaterialCommunityIcons name="package-variant-closed" size={20} color="#22c55e" />
                  <Text style={styles.metricLabel}>Packaging</Text>
                </View>
                <View style={styles.metricRight}>
                  <Text style={[styles.metricScore, { color: getScoreColor(sustainabilityScores.metrics.packaging.score + 50) }]}>
                    {sustainabilityScores.metrics.packaging.score}
                  </Text>
                  <Text style={styles.metricConfidence}>{sustainabilityScores.metrics.packaging.confidence} confidence</Text>
                </View>
              </View>
            )}

            {sustainabilityScores.metrics.raw_materials && (
              <View style={styles.metricRow}>
                <View style={styles.metricLeft}>
                  <MaterialCommunityIcons name="barley" size={20} color="#22c55e" />
                  <Text style={styles.metricLabel}>Raw Materials</Text>
                </View>
                <View style={styles.metricRight}>
                  <Text style={[styles.metricScore, { color: getScoreColor(sustainabilityScores.metrics.raw_materials.score + 50) }]}>
                    {sustainabilityScores.metrics.raw_materials.score}
                  </Text>
                  <Text style={styles.metricConfidence}>{sustainabilityScores.metrics.raw_materials.confidence} confidence</Text>
                </View>
              </View>
            )}
          </View>
        </View>
      )}

      {/* Similar Products */}
      {similarProducts.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Similar Products</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.similarScroll}>
            {similarProducts.map((similar, index) => (
              <TouchableOpacity key={index} style={styles.similarCard}>
                {similar.image_small_url ? (
                  <Image source={{ uri: similar.image_small_url }} style={styles.similarImage} />
                ) : (
                  <View style={styles.similarImagePlaceholder}>
                    <MaterialCommunityIcons name="package-variant" size={40} color="#ccc" />
                  </View>
                )}
                <Text style={styles.similarName} numberOfLines={2}>{similar.product_name}</Text>
                {similar.brand && <Text style={styles.similarBrand}>{similar.brand}</Text>}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}
    </>
  );

  const getIngredientColor = (classification: string) => {
    switch (classification) {
      case 'good': return '#22c55e';
      case 'caution': return '#eab308';
      case 'harmful': return '#ef4444';
      default: return '#9ca3af';
    }
  };

  const getIngredientIcon = (classification: string) => {
    switch (classification) {
      case 'good': return 'check-circle';
      case 'caution': return 'alert-circle';
      case 'harmful': return 'close-circle';
      default: return 'help-circle';
    }
  };

  const renderIngredientsTab = () => {
    if (tabLoading.ingredients) {
      return (
        <View style={styles.tabLoadingContainer}>
          <ActivityIndicator size="large" color="#22c55e" />
          <Text style={styles.loadingText}>Analyzing ingredients...</Text>
        </View>
      );
    }

    if (!ingredientsAnalysis || !ingredientsAnalysis.data_available) {
      return (
        <View style={styles.card}>
          <Text style={styles.emptyText}>No ingredient information available</Text>
        </View>
      );
    }

    const { ingredients, summary } = ingredientsAnalysis;

    return (
      <>
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Ingredient Analysis</Text>

          {/* Summary Stats */}
          <View style={styles.ingredientsSummary}>
            <View style={styles.ingredientStat}>
              <MaterialCommunityIcons name="check-circle" size={24} color="#22c55e" />
              <Text style={styles.ingredientStatNumber}>{summary.good}</Text>
              <Text style={styles.ingredientStatLabel}>Good</Text>
            </View>
            <View style={styles.ingredientStat}>
              <MaterialCommunityIcons name="alert-circle" size={24} color="#eab308" />
              <Text style={styles.ingredientStatNumber}>{summary.caution}</Text>
              <Text style={styles.ingredientStatLabel}>Caution</Text>
            </View>
            <View style={styles.ingredientStat}>
              <MaterialCommunityIcons name="close-circle" size={24} color="#ef4444" />
              <Text style={styles.ingredientStatNumber}>{summary.harmful}</Text>
              <Text style={styles.ingredientStatLabel}>Harmful</Text>
            </View>
          </View>

          {/* Ingredients List */}
          <Text style={styles.ingredientsListTitle}>Ingredients ({summary.total})</Text>
          {ingredients.map((ingredient, index) => (
            <View key={index} style={styles.ingredientItem}>
              <MaterialCommunityIcons
                name={getIngredientIcon(ingredient.classification)}
                size={20}
                color={getIngredientColor(ingredient.classification)}
              />
              <View style={styles.ingredientInfo}>
                <View style={styles.ingredientNameRow}>
                  <Text style={styles.ingredientName}>{ingredient.name}</Text>
                  <Text style={styles.ingredientPercent}>{ingredient.percent.toFixed(1)}%</Text>
                </View>
                <View style={styles.ingredientMeta}>
                  {ingredient.vegan && (
                    <View style={styles.ingredientBadge}>
                      <Text style={styles.ingredientBadgeText}>
                        {ingredient.vegan === 'yes' ? '🌱 Vegan' : ingredient.vegan === 'no' ? '❌ Not Vegan' : '❓ Maybe Vegan'}
                      </Text>
                    </View>
                  )}
                  {ingredient.vegetarian && (
                    <View style={styles.ingredientBadge}>
                      <Text style={styles.ingredientBadgeText}>
                        {ingredient.vegetarian === 'yes' ? '🥬 Vegetarian' : ingredient.vegetarian === 'no' ? '❌ Not Vegetarian' : '❓ Maybe Vegetarian'}
                      </Text>
                    </View>
                  )}
                </View>
              </View>
            </View>
          ))}
        </View>
      </>
    );
  };

  const renderRecommendationsTab = () => {
    if (tabLoading.recommendations) {
      return (
        <View style={styles.tabLoadingContainer}>
          <ActivityIndicator size="large" color="#22c55e" />
          <Text style={styles.loadingText}>Finding better alternatives...</Text>
        </View>
      );
    }

    if (recommendations.length === 0) {
      return (
        <View style={styles.card}>
          <Text style={styles.emptyText}>No better alternatives found</Text>
        </View>
      );
    }

    return (
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Better Alternatives</Text>
        <Text style={styles.recSubtitle}>Products with better sustainability scores</Text>
        {recommendations.map((rec, index) => (
          <View key={index} style={styles.recommendationCard}>
            {rec.product.image_small_url ? (
              <Image source={{ uri: rec.product.image_small_url }} style={styles.recImage} />
            ) : (
              <View style={styles.recImagePlaceholder}>
                <MaterialCommunityIcons name="package-variant" size={30} color="#ccc" />
              </View>
            )}
            <View style={styles.recContent}>
              <View style={styles.recHeader}>
                <Text style={styles.recName} numberOfLines={2}>{rec.product.product_name}</Text>
                <View style={[styles.recGradeBadge, { backgroundColor: getGradeColor(rec.grade) }]}>
                  <Text style={styles.recGradeText}>{rec.grade}</Text>
                </View>
              </View>
              {rec.product.brand && <Text style={styles.recBrand}>{rec.product.brand}</Text>}
              <View style={styles.recMetrics}>
                <View style={styles.recMetricItem}>
                  <MaterialCommunityIcons name="arrow-up-circle" size={16} color="#22c55e" />
                  <Text style={styles.recImprovement}>+{rec.score_improvement} points better</Text>
                </View>
                <Text style={styles.recScore}>{rec.sustainability_score}/100</Text>
              </View>
              <Text style={styles.recReason}>{rec.reason}</Text>
            </View>
          </View>
        ))}
      </View>
    );
  };

  const renderSummaryTab = () => {
    if (tabLoading.summary) {
      return (
        <View style={styles.tabLoadingContainer}>
          <ActivityIndicator size="large" color="#22c55e" />
          <Text style={styles.loadingText}>Generating AI summary...</Text>
        </View>
      );
    }

    if (!aiSummary) {
      return (
        <View style={styles.card}>
          <Text style={styles.emptyText}>No summary available</Text>
        </View>
      );
    }

    return (
      <View style={styles.card}>
        <View style={styles.summaryHeader}>
          <MaterialCommunityIcons name="robot" size={32} color="#22c55e" />
          <Text style={styles.sectionTitle}>AI Summary</Text>
        </View>
        <Text style={styles.summaryText}>{aiSummary}</Text>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView}>
        {/* Product Header */}
        {product.image_url && (
          <Image source={{ uri: product.image_url }} style={styles.productImage} />
        )}

        <View style={styles.card}>
          <Text style={styles.productName}>{product.product_name}</Text>
          {product.brand && <Text style={styles.brand}>{product.brand}</Text>}
          <View style={styles.metaRow}>
            {product.quantity && (
              <View style={styles.metaItem}>
                <MaterialCommunityIcons name="package-variant" size={16} color="#666" />
                <Text style={styles.metaText}>{product.quantity}</Text>
              </View>
            )}
            {product.primary_category && (
              <View style={styles.metaItem}>
                <MaterialCommunityIcons name="tag" size={16} color="#666" />
                <Text style={styles.metaText}>{product.primary_category}</Text>
              </View>
            )}
          </View>
        </View>

        {/* Tabs */}
        <View style={styles.tabsContainer}>
          <TouchableOpacity
            style={[styles.tab, activeTab === 'score' && styles.activeTab]}
            onPress={() => setActiveTab('score')}
          >
            <MaterialCommunityIcons
              name="chart-box"
              size={20}
              color={activeTab === 'score' ? '#22c55e' : '#999'}
            />
            <Text style={[styles.tabText, activeTab === 'score' && styles.activeTabText]}>
              Score
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tab, activeTab === 'ingredients' && styles.activeTab]}
            onPress={() => setActiveTab('ingredients')}
          >
            <MaterialCommunityIcons
              name="food-apple"
              size={20}
              color={activeTab === 'ingredients' ? '#22c55e' : '#999'}
            />
            <Text style={[styles.tabText, activeTab === 'ingredients' && styles.activeTabText]}>
              Ingredients
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tab, activeTab === 'recommendations' && styles.activeTab]}
            onPress={() => setActiveTab('recommendations')}
          >
            <MaterialCommunityIcons
              name="lightbulb"
              size={20}
              color={activeTab === 'recommendations' ? '#22c55e' : '#999'}
            />
            <Text style={[styles.tabText, activeTab === 'recommendations' && styles.activeTabText]}>
              Alternatives
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.tab, activeTab === 'summary' && styles.activeTab]}
            onPress={() => setActiveTab('summary')}
          >
            <MaterialCommunityIcons
              name="text"
              size={20}
              color={activeTab === 'summary' ? '#22c55e' : '#999'}
            />
            <Text style={[styles.tabText, activeTab === 'summary' && styles.activeTabText]}>
              Summary
            </Text>
          </TouchableOpacity>
        </View>

        {/* Tab Content */}
        {renderTabContent()}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  errorText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  productImage: {
    width: '100%',
    height: 250,
    resizeMode: 'contain',
    backgroundColor: '#fff',
    marginBottom: 0,
  },
  card: {
    backgroundColor: '#fff',
    marginHorizontal: 12,
    marginVertical: 12,
    marginTop: 0,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  productName: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  brand: {
    fontSize: 16,
    color: '#666',
    marginBottom: 12,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  metaText: {
    fontSize: 14,
    color: '#666',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
    color: '#333',
  },
  gradeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  gradeBadge: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 20,
  },
  gradeText: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#fff',
  },
  scoreDetails: {
    flex: 1,
  },
  scoreNumber: {
    fontSize: 36,
    fontWeight: 'bold',
  },
  scoreLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  metricsContainer: {
    marginTop: 12,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e5e5e5',
  },
  metricsTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    color: '#333',
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f5f5f5',
  },
  metricLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  metricLabel: {
    fontSize: 15,
    color: '#333',
    marginLeft: 8,
  },
  metricRight: {
    alignItems: 'flex-end',
  },
  metricScore: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  metricRating: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  metricConfidence: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  similarScroll: {
    marginHorizontal: -16,
    paddingHorizontal: 16,
  },
  similarCard: {
    width: 120,
    marginRight: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    padding: 8,
  },
  similarImage: {
    width: '100%',
    height: 100,
    borderRadius: 6,
    marginBottom: 8,
    resizeMode: 'contain',
  },
  similarImagePlaceholder: {
    width: '100%',
    height: 100,
    borderRadius: 6,
    marginBottom: 8,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  similarName: {
    fontSize: 13,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  similarBrand: {
    fontSize: 11,
    color: '#666',
  },
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  tabsContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginHorizontal: 12,
    marginVertical: 12,
    marginTop: 0,
    borderRadius: 12,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
    gap: 4,
  },
  activeTab: {
    backgroundColor: '#f0fdf4',
  },
  tabText: {
    fontSize: 12,
    color: '#999',
    fontWeight: '600',
  },
  activeTabText: {
    color: '#22c55e',
  },
  tabLoadingContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    paddingVertical: 20,
  },
  ingredientsText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 22,
  },
  alertSection: {
    flexDirection: 'row',
    marginTop: 16,
    padding: 12,
    backgroundColor: '#fef2f2',
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: '#ef4444',
  },
  alertContent: {
    marginLeft: 12,
    flex: 1,
  },
  alertTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  alertText: {
    fontSize: 13,
    color: '#666',
    lineHeight: 20,
  },
  recSubtitle: {
    fontSize: 13,
    color: '#666',
    marginBottom: 16,
    marginTop: -8,
  },
  recommendationCard: {
    flexDirection: 'row',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  recImage: {
    width: 80,
    height: 80,
    borderRadius: 8,
    marginRight: 12,
    resizeMode: 'contain',
    backgroundColor: '#f9fafb',
  },
  recImagePlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 8,
    marginRight: 12,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  recContent: {
    flex: 1,
    justifyContent: 'flex-start',
  },
  recHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  recName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
    flex: 1,
    marginRight: 8,
  },
  recGradeBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  recGradeText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
  },
  recBrand: {
    fontSize: 13,
    color: '#666',
    marginBottom: 6,
  },
  recMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  recMetricItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  recImprovement: {
    fontSize: 13,
    fontWeight: '600',
    color: '#22c55e',
  },
  recScore: {
    fontSize: 14,
    fontWeight: '700',
    color: '#22c55e',
  },
  recReason: {
    fontSize: 12,
    color: '#666',
    lineHeight: 18,
    fontStyle: 'italic',
  },
  summaryText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 22,
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  ingredientsSummary: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
    paddingVertical: 16,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
  },
  ingredientStat: {
    alignItems: 'center',
    gap: 4,
  },
  ingredientStatNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  ingredientStatLabel: {
    fontSize: 12,
    color: '#666',
  },
  ingredientsListTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  ingredientItem: {
    flexDirection: 'row',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    gap: 12,
  },
  ingredientInfo: {
    flex: 1,
  },
  ingredientNameRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  ingredientName: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
    flex: 1,
  },
  ingredientPercent: {
    fontSize: 13,
    fontWeight: '600',
    color: '#666',
  },
  ingredientMeta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 4,
  },
  ingredientBadge: {
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  ingredientBadgeText: {
    fontSize: 11,
    color: '#666',
  },
});
