import { View, Text, TouchableOpacity, StyleSheet, FlatList } from 'react-native';
import { useState, useEffect } from 'react';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import BarcodeScanner from '../../components/BarcodeScanner';

interface RecentScan {
  barcode: string;
  timestamp: number;
  productName?: string;
}

export default function HomeScreen() {
  const [scannerVisible, setScannerVisible] = useState(false);
  const [recentScans, setRecentScans] = useState<RecentScan[]>([]);
  const router = useRouter();

  useEffect(() => {
    loadRecentScans();
  }, []);

  const loadRecentScans = async () => {
    try {
      const stored = await AsyncStorage.getItem('recentScans');
      if (stored) {
        setRecentScans(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Failed to load recent scans:', error);
    }
  };

  const saveRecentScan = async (barcode: string) => {
    try {
      const newScan: RecentScan = {
        barcode,
        timestamp: Date.now(),
      };

      const updated = [newScan, ...recentScans.filter(s => s.barcode !== barcode)].slice(0, 10);
      setRecentScans(updated);
      await AsyncStorage.setItem('recentScans', JSON.stringify(updated));
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

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.sectionTitle}>Recent Scans</Text>

        {recentScans.length === 0 ? (
          <View style={styles.emptyState}>
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
                <View style={styles.scanItemContent}>
                  <Text style={styles.scanBarcode}>{item.barcode}</Text>
                  {item.productName && (
                    <Text style={styles.scanProductName}>{item.productName}</Text>
                  )}
                </View>
                <Text style={styles.scanTime}>{formatTimestamp(item.timestamp)}</Text>
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
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
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
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  scanItemContent: {
    flex: 1,
  },
  scanBarcode: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  scanProductName: {
    fontSize: 14,
    color: '#666',
    marginTop: 3,
  },
  scanTime: {
    fontSize: 12,
    color: '#999',
    marginLeft: 10,
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
