import { View, Text, StyleSheet, ScrollView } from 'react-native';
import React, { useState, useEffect } from 'react';
import { useFocusEffect } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MaterialCommunityIcons } from '@expo/vector-icons';

export default function ProfileScreen() {
  const [ecoScore, setEcoScore] = useState(0);
  const [productsScanned, setProductsScanned] = useState(0);
  const [treesPlanted, setTreesPlanted] = useState(0);

  useEffect(() => {
    loadStats();
  }, []);

  // Reload stats when screen comes into focus
  useFocusEffect(
    React.useCallback(() => {
      loadStats();
    }, [])
  );

  const loadStats = async () => {
    try {
      const score = await AsyncStorage.getItem('ecoScore');
      const scanned = await AsyncStorage.getItem('productsScanned');

      const ecoScoreValue = parseInt(score || '0');
      const scannedValue = parseInt(scanned || '0');
      const treesValue = Math.floor(ecoScoreValue / 100);

      setEcoScore(ecoScoreValue);
      setProductsScanned(scannedValue);
      setTreesPlanted(treesValue);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <View style={styles.avatarContainer}>
            <MaterialCommunityIcons name="leaf" size={80} color="#22c55e" />
          </View>
          <Text style={styles.name}>My Impact</Text>
        </View>

        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{productsScanned}</Text>
            <Text style={styles.statLabel}>Products Scanned</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{ecoScore}</Text>
            <Text style={styles.statLabel}>ECO Score</Text>
          </View>
        </View>

        <View style={styles.impactSection}>
          <MaterialCommunityIcons name="tree" size={64} color="#22c55e" />
          <Text style={styles.impactTitle}>Your Environmental Impact</Text>
          <Text style={styles.impactText}>
            You have planted the equivalent of
          </Text>
          <Text style={styles.treesValue}>
            {treesPlanted} {treesPlanted === 1 ? 'tree' : 'trees'}
          </Text>
          <Text style={styles.impactSubtext}>
            by choosing sustainable products
          </Text>
          <View style={styles.progressInfo}>
            <MaterialCommunityIcons name="information" size={16} color="#666" />
            <Text style={styles.progressText}>
              100 ECO points = 1 tree planted
            </Text>
          </View>
        </View>

        {ecoScore < 100 && (
          <View style={styles.nextTreeSection}>
            <View style={styles.progressBarContainer}>
              <View style={[styles.progressBar, { width: `${(ecoScore % 100)}%` }]} />
            </View>
            <Text style={styles.nextTreeText}>
              {100 - (ecoScore % 100)} more points until your next tree!
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    padding: 20,
    paddingTop: 60,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  avatarContainer: {
    marginBottom: 15,
  },
  name: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
  },
  statsContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    backgroundColor: '#e5e5e5',
    marginHorizontal: 20,
  },
  statValue: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#22c55e',
    marginBottom: 5,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  impactSection: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 30,
    marginBottom: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  impactTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 16,
    marginBottom: 12,
  },
  impactText: {
    fontSize: 15,
    color: '#666',
    textAlign: 'center',
  },
  treesValue: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#22c55e',
    marginVertical: 12,
  },
  impactSubtext: {
    fontSize: 15,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  progressInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
  },
  progressText: {
    fontSize: 13,
    color: '#666',
  },
  nextTreeSection: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  progressBarContainer: {
    height: 12,
    backgroundColor: '#e5e5e5',
    borderRadius: 6,
    overflow: 'hidden',
    marginBottom: 12,
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#22c55e',
    borderRadius: 6,
  },
  nextTreeText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    fontWeight: '500',
  },
});
