import { View, Text, ScrollView, ActivityIndicator, StyleSheet, Image, TouchableOpacity } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { API_BASE_URL } from '../../config/constants';

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
    climate_efficiency: {
      score: number;
      efficiency_rating: string;
      co2_per_100g_protein: number;
      confidence: string;
    };
    packaging: {
      score: number;
      co2_kg_per_kg: number;
      confidence: string;
    };
    raw_materials: {
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

export default function ProductDetailsScreen() {
  const { barcode } = useLocalSearchParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [sustainabilityScores, setSustainabilityScores] = useState<SustainabilityScores | null>(null);
  const [similarProducts, setSimilarProducts] = useState<SimilarProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProductDetails();
  }, [barcode]);

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

  return (
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
    </ScrollView>
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
  },
  card: {
    backgroundColor: '#fff',
    margin: 12,
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
});
