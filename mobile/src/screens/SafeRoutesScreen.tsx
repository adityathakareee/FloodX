import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { THEME } from '../constants/theme';
import { Header } from '../components/Header';
import { mobileApi } from '../services/api';
import { MobileRoutePlan } from '../types/api';

interface Props {
  onBack: () => void;
}

const PRESET_ORIGINS = [
  { name: 'Pulachi Wadi / Deccan Riverbed', lat: 18.518, lon: 73.847, note: 'High Flood Risk Zone' },
  { name: 'Patil Estate Slums (Sangamwadi)', lat: 18.531, lon: 73.864, note: 'Confluence Backwater Zone' },
  { name: 'Kasba Peth (Dengle Bridge Ramp)', lat: 18.522, lon: 73.856, note: 'Low-Lying Urban Core' },
  { name: 'Sinhagad Road (Ekta Nagari)', lat: 18.475, lon: 73.818, note: 'Mutha Riverbank' },
];

const PRESET_DESTINATIONS = [
  { name: 'Swargate High-Ground Relief Camp', lat: 18.502, lon: 73.858, note: 'Elevation 568m MSL' },
  { name: 'Fergusson Hill Shelter Complex', lat: 18.523, lon: 73.839, note: 'Elevation 575m MSL' },
  { name: 'Shivajinagar Elevated Station Ground', lat: 18.532, lon: 73.852, note: 'Elevation 562m MSL' },
];

export const SafeRoutesScreen: React.FC<Props> = ({ onBack }) => {
  const [selectedOrigin, setSelectedOrigin] = useState(PRESET_ORIGINS[0]);
  const [selectedDest, setSelectedDest] = useState(PRESET_DESTINATIONS[0]);
  const [routePlan, setRoutePlan] = useState<MobileRoutePlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePlanRoute = async () => {
    setLoading(true);
    setError(null);
    try {
      const plan = await mobileApi.planEvacuationRoute(
        selectedOrigin.lat,
        selectedOrigin.lon,
        selectedDest.lat,
        selectedDest.lon,
        'BALANCED'
      );
      setRoutePlan(plan);
    } catch (e: any) {
      setError(e?.message || 'Route planning engine unreachable');
    } finally {
      setLoading(false);
    }
  };

  const getSafetyBadgeColor = (tier?: string) => {
    if (tier === 'VERIFIED_SAFE') return THEME.colors.green;
    if (tier === 'ELEVATED_RISK') return THEME.colors.amber;
    return THEME.colors.red;
  };

  return (
    <View style={styles.container}>
      <Header
        title="Safe Evacuation Routes"
        subtitle="Topography-aware pathfinding avoiding flooded roads"
        showBack
        onBack={onBack}
      />
      <ScrollView contentContainerStyle={styles.content}>
        {/* Origin Selector */}
        <Text style={styles.sectionHeader}>SELECT EVACUATION ORIGIN (VULNERABLE ZONE)</Text>
        <View style={styles.chipContainer}>
          {PRESET_ORIGINS.map((orig, i) => (
            <TouchableOpacity
              key={i}
              style={[
                styles.chip,
                selectedOrigin.name === orig.name && styles.chipSelected,
              ]}
              onPress={() => setSelectedOrigin(orig)}
            >
              <Text
                style={[
                  styles.chipText,
                  selectedOrigin.name === orig.name && styles.chipTextSelected,
                ]}
              >
                {orig.name}
              </Text>
              <Text style={styles.chipNote}>{orig.note}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Destination Selector */}
        <Text style={styles.sectionHeader}>SELECT SAFE HIGH-GROUND DESTINATION</Text>
        <View style={styles.chipContainer}>
          {PRESET_DESTINATIONS.map((dest, i) => (
            <TouchableOpacity
              key={i}
              style={[
                styles.chip,
                selectedDest.name === dest.name && styles.chipSelected,
              ]}
              onPress={() => setSelectedDest(dest)}
            >
              <Text
                style={[
                  styles.chipText,
                  selectedDest.name === dest.name && styles.chipTextSelected,
                ]}
              >
                {dest.name}
              </Text>
              <Text style={styles.chipNote}>{dest.note}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Calculate Button */}
        <TouchableOpacity
          style={styles.calcButton}
          onPress={handlePlanRoute}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#000" />
          ) : (
            <Text style={styles.calcButtonText}>CALCULATE SAFE EVACUATION ROUTE</Text>
          )}
        </TouchableOpacity>

        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>Notice: {error}</Text>
          </View>
        )}

        {/* Route Result Display */}
        {routePlan && (
          <View style={styles.resultCard}>
            <View style={styles.resultHeader}>
              <Text style={styles.resultTitle}>EVACUATION CORRIDOR COMPUTED</Text>
              <Text
                style={[
                  styles.safetyBadge,
                  { backgroundColor: getSafetyBadgeColor(routePlan.overall_route_safety_tier) },
                ]}
              >
                {routePlan.overall_route_safety_tier}
              </Text>
            </View>

            <View style={styles.statGrid}>
              <View style={styles.statBox}>
                <Text style={styles.statLabel}>Distance</Text>
                <Text style={styles.statVal}>{routePlan.total_distance_km.toFixed(1)} km</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statLabel}>Est. Travel Time</Text>
                <Text style={styles.statVal}>{routePlan.estimated_evacuation_time_minutes.toFixed(0)} min</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statLabel}>River Crossings</Text>
                <Text style={styles.statVal}>{routePlan.has_waterway_crossings ? 'YES' : 'NONE'}</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statLabel}>Waypoints</Text>
                <Text style={styles.statVal}>{routePlan.waypoints_count}</Text>
              </View>
            </View>

            {routePlan.warning_notes.length > 0 && (
              <View style={styles.warningBox}>
                <Text style={styles.warningTitle}>SAFETY ADVISORIES & HAZARDS</Text>
                {routePlan.warning_notes.map((w, i) => (
                  <Text key={i} style={styles.warningItem}>• {w}</Text>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Mandatory Decision Support Disclaimer */}
        <View style={styles.disclaimerCard}>
          <Text style={styles.disclaimerText}>
            Never drive or walk into moving water. If an evacuation corridor becomes flooded en route, immediately seek nearest upper-floor vertical shelter.
          </Text>
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
    padding: 16,
    paddingBottom: 40,
  },
  sectionHeader: {
    color: THEME.colors.textSecondary,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    fontFamily: THEME.typography.mono,
    marginBottom: 8,
    marginTop: 12,
  },
  chipContainer: {
    gap: 8,
    marginBottom: 12,
  },
  chip: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 12,
  },
  chipSelected: {
    borderColor: THEME.colors.cyan,
    backgroundColor: 'rgba(56, 189, 248, 0.1)',
  },
  chipText: {
    color: THEME.colors.textPrimary,
    fontSize: 13,
    fontWeight: '700',
  },
  chipTextSelected: {
    color: THEME.colors.cyan,
  },
  chipNote: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
    marginTop: 2,
  },
  calcButton: {
    backgroundColor: THEME.colors.cyan,
    paddingVertical: 14,
    borderRadius: THEME.borderRadius.md,
    alignItems: 'center',
    marginVertical: 12,
  },
  calcButtonText: {
    color: '#000',
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 1,
    fontFamily: THEME.typography.mono,
  },
  errorBox: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderColor: THEME.colors.red,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 12,
    marginBottom: 12,
  },
  errorText: {
    color: THEME.colors.red,
    fontSize: 11,
  },
  resultCard: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.cyan,
    borderWidth: 1.5,
    borderRadius: THEME.borderRadius.lg,
    padding: 16,
    marginBottom: 16,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  resultTitle: {
    color: THEME.colors.textPrimary,
    fontSize: 12,
    fontWeight: '800',
    fontFamily: THEME.typography.mono,
  },
  safetyBadge: {
    color: '#000',
    fontSize: 9,
    fontWeight: '900',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    fontFamily: THEME.typography.mono,
  },
  statGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  statBox: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: THEME.colors.surfaceHighlight,
    padding: 10,
    borderRadius: THEME.borderRadius.md,
  },
  statLabel: {
    color: THEME.colors.textSecondary,
    fontSize: 10,
  },
  statVal: {
    color: THEME.colors.textPrimary,
    fontSize: 14,
    fontWeight: '800',
    fontFamily: THEME.typography.mono,
    marginTop: 2,
  },
  warningBox: {
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
    borderColor: THEME.colors.amber,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 12,
  },
  warningTitle: {
    color: THEME.colors.amber,
    fontSize: 10,
    fontWeight: '800',
    fontFamily: THEME.typography.mono,
    marginBottom: 4,
  },
  warningItem: {
    color: THEME.colors.textPrimary,
    fontSize: 11,
    lineHeight: 16,
  },
  disclaimerCard: {
    backgroundColor: 'rgba(245, 158, 11, 0.08)',
    borderColor: 'rgba(245, 158, 11, 0.25)',
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 12,
    marginTop: 8,
  },
  disclaimerText: {
    color: THEME.colors.amber,
    fontSize: 10,
    lineHeight: 14,
  },
});
