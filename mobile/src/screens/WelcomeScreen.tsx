import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { THEME } from '../constants/theme';

interface WelcomeScreenProps {
  onContinue: () => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onContinue }) => {
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.badgeContainer}>
        <Text style={styles.badgeText}>PCCOE GRAND CHALLENGE 2026</Text>
      </View>

      <Text style={styles.appName}>FLOOD-X</Text>
      <Text style={styles.tagline}>PREDICT | PRIORITIZE | PROTECT</Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Citizen Flood Intelligence</Text>
        <Text style={styles.cardText}>
          FLOOD-X is an AI-powered early warning and evacuation decision platform for residents of the{' '}
          <Text style={styles.highlight}>Pune / Mula-Mutha River Basin</Text>.
        </Text>
        <Text style={styles.cardText}>
          When fully deployed, this application will provide localized flash-flood alerts, safe high-ground evacuation routes avoiding submerged bridges, and nearby relief shelter occupancy tracking.
        </Text>
      </View>

      <View style={styles.phaseNotice}>
        <Text style={styles.phaseTitle}>Phase 0: Architecture Foundation</Text>
        <Text style={styles.phaseDesc}>
          This build verifies backend API connectivity, resilient health reporting, and screen routing. In adherence to Phase 0 rules, no fabricated flood alerts are displayed.
        </Text>
      </View>

      <TouchableOpacity style={styles.btn} onPress={onContinue} activeOpacity={0.8}>
        <Text style={styles.btnText}>Open Citizen Dashboard →</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: THEME.colors.background,
    paddingHorizontal: 24,
    paddingVertical: 40,
    justifyContent: 'center',
  },
  badgeContainer: {
    alignSelf: 'flex-start',
    backgroundColor: THEME.colors.cyanMuted,
    borderColor: THEME.colors.cyan,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: THEME.borderRadius.full,
    marginBottom: 16,
  },
  badgeText: {
    color: THEME.colors.cyan,
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
  },
  appName: {
    fontSize: 36,
    fontWeight: '900',
    color: THEME.colors.textPrimary,
    letterSpacing: 2,
  },
  tagline: {
    fontSize: 12,
    fontWeight: '700',
    color: THEME.colors.cyan,
    letterSpacing: 2,
    marginBottom: 24,
  },
  card: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.lg,
    padding: 20,
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: THEME.colors.textPrimary,
    marginBottom: 10,
  },
  cardText: {
    fontSize: 13,
    color: THEME.colors.textSecondary,
    lineHeight: 20,
    marginBottom: 8,
  },
  highlight: {
    color: THEME.colors.cyan,
    fontWeight: '600',
  },
  phaseNotice: {
    backgroundColor: THEME.colors.amberMuted,
    borderColor: THEME.colors.amber,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 14,
    marginBottom: 28,
  },
  phaseTitle: {
    color: THEME.colors.amber,
    fontWeight: '700',
    fontSize: 12,
    marginBottom: 4,
  },
  phaseDesc: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
    lineHeight: 16,
  },
  btn: {
    backgroundColor: THEME.colors.cyan,
    paddingVertical: 16,
    borderRadius: THEME.borderRadius.md,
    alignItems: 'center',
    shadowColor: THEME.colors.cyan,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  btnText: {
    color: '#070D1E',
    fontWeight: '800',
    fontSize: 14,
    letterSpacing: 0.5,
  },
});

