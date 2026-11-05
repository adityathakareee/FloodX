import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { THEME } from '../constants/theme';
import { Header } from '../components/Header';
import { mobileApi } from '../services/api';

interface Props {
  onBack: () => void;
}

export const ProfileSettingsScreen: React.FC<Props> = ({ onBack }) => {
  const [urlInput, setUrlInput] = useState(mobileApi.getBaseUrl());
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const applyUrl = (url: string) => {
    setUrlInput(url);
    mobileApi.setBaseUrl(url);
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    mobileApi.setBaseUrl(urlInput);

    try {
      const data = await mobileApi.getHealth(4000);
      setTestResult(
        `✓ Connected: ${data.app_name} (${data.status.toUpperCase()}) | DB: ${data.database.status}`
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Connection failed';
      setTestResult(`✗ Error: ${msg}`);
    } finally {
      setTesting(false);
    }
  };

  return (
    <View style={styles.container}>
      <Header
        title="Settings & Network"
        subtitle="Backend API endpoint configuration"
        showBack
        onBack={onBack}
      />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Backend API Gateway URL</Text>
          <Text style={styles.cardSubtitle}>
            When testing on a physical Android phone, do not use 'localhost'. Use your PC's Wi-Fi IP address.
          </Text>

          <TextInput
            style={styles.input}
            value={urlInput}
            onChangeText={setUrlInput}
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="http://192.168.x.x:8000/api/v1"
            placeholderTextColor={THEME.colors.textMuted}
          />

          <View style={styles.presetRow}>
            <TouchableOpacity
              style={styles.presetBtn}
              onPress={() => applyUrl('http://10.0.2.2:8000/api/v1')}
            >
              <Text style={styles.presetText}>Emulator (10.0.2.2)</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.presetBtn}
              onPress={() => applyUrl('http://localhost:8000/api/v1')}
            >
              <Text style={styles.presetText}>Localhost</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={styles.testBtn}
            onPress={handleTestConnection}
            disabled={testing}
            activeOpacity={0.8}
          >
            <Text style={styles.testBtnText}>
              {testing ? 'Testing Connection...' : 'Test Backend Connection'}
            </Text>
          </TouchableOpacity>

          {testResult && (
            <View
              style={[
                styles.resultBox,
                testResult.startsWith('✓') ? styles.resultSuccess : styles.resultError,
              ]}
            >
              <Text
                style={[
                  styles.resultText,
                  testResult.startsWith('✓') ? styles.resultSuccessText : styles.resultErrorText,
                ]}
              >
                {testResult}
              </Text>
            </View>
          )}
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Platform Build Details</Text>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Client:</Text>
            <Text style={styles.infoValue}>FLOOD-X Citizen Android</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Version:</Text>
            <Text style={styles.infoValue}>0.1.0-phase0</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Milestone:</Text>
            <Text style={styles.infoValue}>Phase 0: System Architecture</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Target Basin:</Text>
            <Text style={styles.infoValue}>Pune / Mula-Mutha Basin</Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: THEME.colors.background,
  },
  content: {
    padding: 20,
  },
  card: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.lg,
    padding: 18,
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: THEME.colors.textPrimary,
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 12,
    color: THEME.colors.textSecondary,
    marginBottom: 14,
    lineHeight: 18,
  },
  input: {
    backgroundColor: THEME.colors.background,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 13,
    color: THEME.colors.textPrimary,
    fontFamily: 'monospace',
    marginBottom: 12,
  },
  presetRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  presetBtn: {
    backgroundColor: THEME.colors.surfaceElevated,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: THEME.borderRadius.sm,
  },
  presetText: {
    color: THEME.colors.cyan,
    fontSize: 11,
    fontWeight: '600',
  },
  testBtn: {
    backgroundColor: THEME.colors.cyan,
    borderRadius: THEME.borderRadius.md,
    paddingVertical: 12,
    alignItems: 'center',
  },
  testBtnText: {
    color: '#070D1E',
    fontWeight: 'bold',
    fontSize: 13,
  },
  resultBox: {
    marginTop: 12,
    padding: 10,
    borderRadius: THEME.borderRadius.sm,
    borderWidth: 1,
  },
  resultSuccess: {
    backgroundColor: THEME.colors.emeraldMuted,
    borderColor: THEME.colors.emerald,
  },
  resultError: {
    backgroundColor: THEME.colors.roseMuted,
    borderColor: THEME.colors.rose,
  },
  resultText: {
    fontSize: 11,
    fontFamily: 'monospace',
  },
  resultSuccessText: {
    color: THEME.colors.emerald,
  },
  resultErrorText: {
    color: THEME.colors.rose,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: THEME.colors.border,
  },
  infoLabel: {
    fontSize: 12,
    color: THEME.colors.textSecondary,
  },
  infoValue: {
    fontSize: 12,
    fontWeight: '600',
    color: THEME.colors.textPrimary,
  },
});

