import { View, Text, TouchableOpacity, StyleSheet, FlatList, Image, ActivityIndicator } from 'react-native';
import React, { useState, useEffect } from 'react';
import { useRouter, useFocusEffect } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import BarcodeScanner from '../../components/BarcodeScanner';
import { API_BASE_URL } from '../../config/constants';

interface RecentScan {
  barcode: string;
  timestamp: number;
  productName?: string;
  brand?: string;
  image_url?: string;
  grade?: string;
  score?: number;
}

export default function HomeScreen() {
  const [scannerVisible, setScannerVisible] = useState(false);
  const [recentScans, setRecentScans] = useState<RecentScan[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    loadRecentScans();
  }, []);

  // Reload scans when screen comes into focus
  useFocusEffect(
    React.useCallback(() => {
      loadRecentScans();
    }, [])
  );

  const loadRecentScans = async () => {
    try {
      setLoading(true);
      const stored = await AsyncStorage.getItem('recentScans');
      if (stored) {
        const scans = JSON.parse(stored);
        // Fetch product details for each scan
        const scansWithDetails = await Promise.all(
          scans.map(async (scan: RecentScan) => {
            try {
              const response = await axios.get(
                `${API_BASE_URL}/api/products/${scan.barcode}?sustainability_score=true`
              );
              if (response.data.status === 'success' && response.data.data) {
                const { product, sustainability_scores } = response.data.data;
                return {
                  ...scan,
                  productName: product.product_name,
                  brand: product.brand,
                  image_url: product.image_small_url,
                  grade: sustainability_scores?.grade,
                  score: sustainability_scores?.total_score,
                };
              }
              return scan;
            } catch (err) {
              console.error(`Failed to fetch details for ${scan.barcode}:`, err);
              return scan;
            }
          })
        );
        setRecentScans(scansWithDetails);
      }
    } catch (error) {
      console.error('Failed to load recent scans:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveRecentScan = async (barcode: string) => {
    try {
      const newScan: RecentScan = {
        barcode,
        timestamp: Date.now(),
      };

      const updated = [newScan, ...recentScans.filter(s => s.barcode !== barcode)].slice(0, 10);
      await AsyncStorage.setItem('recentScans', JSON.stringify(updated));
      // Reload to fetch product details
      loadRecentScans();
    } catch (error) {
      console.error('Failed to save recent scan:', error);
    }
  };

  const handleScan = (barcode: string) => {
    saveRecentScan(barcode);
    setScannerVisible(false);
    router.push(`/product/${barcode}`);
  };

  const handleScanPress = (barcode: string) => {
    router.push(`/product/${barcode}`);
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getGradeColor = (grade?: string) => {
    if (!grade) return '#9ca3af';
    switch (grade.toUpperCase()) {
      case 'A': return '#22c55e';
      case 'B': return '#86efac';
      case 'C': return '#eab308';
      case 'D': return '#f97316';
      case 'E': return '#ef4444';
      default: return '#9ca3af';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.sectionTitle}>Recent Scans</Text>

        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#22c55e" />
            <Text style={styles.loadingText}>Loading your scans...</Text>
          </View>
        ) : recentScans.length === 0 ? (
          <View style={styles.emptyState}>
            <MaterialCommunityIcons name="barcode-scan" size={64} color="#ccc" />
            <Text style={styles.emptyText}>No recent scans</Text>
            <Text style={styles.emptySubtext}>Tap the scan button to get started</Text>
          </View>
        ) : (
          <FlatList
            data={recentScans}
            keyExtractor={(item) => item.barcode + item.timestamp}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.scanItem}
                onPress={() => handleScanPress(item.barcode)}
              >
                {item.image_url ? (
                  <Image source={{ uri: item.image_url }} style={styles.scanImage} />
                ) : (
                  <View style={styles.scanImagePlaceholder}>
                    <MaterialCommunityIcons name="package-variant" size={40} color="#ccc" />
                  </View>
                )}
                <View style={styles.scanItemContent}>
                  <View style={styles.scanHeader}>
                    <Text style={styles.scanProductName} numberOfLines={2}>
                      {item.productName || item.barcode}
                    </Text>
                    {item.grade && (
                      <View style={[styles.gradeBadge, { backgroundColor: getGradeColor(item.grade) }]}>
                        <Text style={styles.gradeText}>{item.grade}</Text>
                      </View>
                    )}
                  </View>
                  {item.brand && (
                    <Text style={styles.scanBrand}>{item.brand}</Text>
                  )}
                  <View style={styles.scanFooter}>
                    {item.score !== undefined && (
                      <Text style={styles.scanScore}>Score: {item.score}/100</Text>
                    )}
                    <Text style={styles.scanTime}>{formatTimestamp(item.timestamp)}</Text>
                  </View>
                </View>
              </TouchableOpacity>
            )}
            contentContainerStyle={styles.listContent}
          />
        )}
      </View>

      {/* Floating Scan Button */}
      <TouchableOpacity
        style={styles.fabButton}
        onPress={() => setScannerVisible(true)}
      >
        <MaterialCommunityIcons name="barcode-scan" size={32} color="#22c55e" />
      </TouchableOpacity>

      {/* Scanner Modal */}
      <BarcodeScanner
        visible={scannerVisible}
        onClose={() => setScannerVisible(false)}
        onScan={handleScan}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    flex: 1,
    padding: 20,
    paddingTop: 60,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    fontSize: 14,
    color: '#666',
    marginTop: 12,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    marginTop: 16,
    marginBottom: 5,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
  },
  listContent: {
    paddingBottom: 100,
  },
  scanItem: {
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
    flexDirection: 'row',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  scanImage: {
    width: 80,
    height: 80,
    borderRadius: 8,
    marginRight: 12,
    resizeMode: 'contain',
    backgroundColor: '#f9fafb',
  },
  scanImagePlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 8,
    marginRight: 12,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  scanItemContent: {
    flex: 1,
    justifyContent: 'space-between',
  },
  scanHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  scanProductName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#333',
    flex: 1,
    marginRight: 8,
  },
  gradeBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  gradeText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#fff',
  },
  scanBrand: {
    fontSize: 13,
    color: '#666',
    marginBottom: 6,
  },
  scanFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  scanScore: {
    fontSize: 13,
    fontWeight: '600',
    color: '#22c55e',
  },
  scanTime: {
    fontSize: 12,
    color: '#999',
  },
  fabButton: {
    position: 'absolute',
    right: 20,
    bottom: 80,
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 12,
  },
});
