import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Switch } from 'react-native';
import { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MaterialCommunityIcons } from '@expo/vector-icons';

const AI_SUMMARIES_KEY = 'aiSummariesEnabled';

export default function SettingsScreen() {
  const [aiSummariesEnabled, setAiSummariesEnabled] = useState(true);
  const [hapticEnabled, setHapticEnabled] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const aiEnabled = await AsyncStorage.getItem(AI_SUMMARIES_KEY);
      if (aiEnabled !== null) {
        setAiSummariesEnabled(aiEnabled === 'true');
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const handleAiSummariesToggle = async (value: boolean) => {
    try {
      setAiSummariesEnabled(value);
      await AsyncStorage.setItem(AI_SUMMARIES_KEY, value.toString());
    } catch (error) {
      console.error('Failed to save AI summaries setting:', error);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Preferences</Text>

          <View style={styles.settingItem}>
            <View style={styles.settingLeft}>
              <MaterialCommunityIcons name="robot" size={24} color="#666" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>AI Summaries</Text>
                <Text style={styles.settingDescription}>Enable AI-generated summaries</Text>
              </View>
            </View>
            <Switch
              value={aiSummariesEnabled}
              onValueChange={handleAiSummariesToggle}
              trackColor={{ false: '#d1d5db', true: '#86efac' }}
              thumbColor={aiSummariesEnabled ? '#22c55e' : '#f4f3f4'}
            />
          </View>

          <View style={styles.settingItem}>
            <View style={styles.settingLeft}>
              <MaterialCommunityIcons name="vibrate" size={24} color="#666" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Haptic Feedback</Text>
                <Text style={styles.settingDescription}>Vibrate on scan</Text>
              </View>
            </View>
            <Switch
              value={hapticEnabled}
              onValueChange={setHapticEnabled}
              trackColor={{ false: '#d1d5db', true: '#86efac' }}
              thumbColor={hapticEnabled ? '#22c55e' : '#f4f3f4'}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Scanner Settings</Text>

          <TouchableOpacity style={styles.settingItem}>
            <View style={styles.settingLeft}>
              <MaterialCommunityIcons name="history" size={24} color="#666" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Clear History</Text>
                <Text style={styles.settingDescription}>Remove all recent scans</Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#999" />
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>

          <TouchableOpacity style={styles.settingItem}>
            <View style={styles.settingLeft}>
              <MaterialCommunityIcons name="information" size={24} color="#666" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>App Version</Text>
                <Text style={styles.settingDescription}>1.0.0</Text>
              </View>
            </View>
          </TouchableOpacity>

          <TouchableOpacity style={styles.settingItem}>
            <View style={styles.settingLeft}>
              <MaterialCommunityIcons name="file-document" size={24} color="#666" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Privacy Policy</Text>
                <Text style={styles.settingDescription}>View our privacy policy</Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#999" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.settingItem}>
            <View style={styles.settingLeft}>
              <MaterialCommunityIcons name="shield-check" size={24} color="#666" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Terms of Service</Text>
                <Text style={styles.settingDescription}>View terms and conditions</Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#999" />
          </TouchableOpacity>
        </View>
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
  section: {
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
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingText: {
    marginLeft: 15,
    flex: 1,
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
    marginBottom: 2,
  },
  settingDescription: {
    fontSize: 14,
    color: '#666',
  },
});
