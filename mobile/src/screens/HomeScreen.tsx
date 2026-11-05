import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { THEME } from '../constants/theme';
import { StatusBadge } from '../components/StatusBadge';
import { mobileApi } from '../services/api';
import { HealthResponse, CurrentConditionResponse } from '../types/api';

interface HomeScreenProps {
  onNavigate: (screen: string) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({ onNavigate }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [condition, setCondition] = useState<CurrentConditionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [healthData, conditionData] = await Promise.allSettled([
        mobileApi.getHealth(),
        mobileApi.getCurrentConditions(),
      ]);

      if (healthData.status === 'fulfilled') {
        setHealth(healthData.value);
        setApiError(null);
      } else {
        setApiError('Backend unreachable');
      }

      if (conditionData.status === 'fulfilled') {
        setCondition(conditionData.value);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Backend unreachable';
      setApiError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getSystemStatus = () => {
    if (apiError || !health) return 'offline';
    if (health.status === 'degraded') return 'degraded';
    if (health.status === 'healthy') return 'healthy';
    return 'degraded';
  };

  const getAlertColor = (status?: string) => {
    if (!status) return THEME.colors.slate;
    if (status === 'SEVERE_INUNDATION_RISK') return THEME.colors.red;
    if (status === 'ELEVATED_PLUVIAL_RISK') return THEME.colors.amber;
    if (status === 'NORMAL') return THEME.colors.green;
    return THEME.colors.slate;
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={fetchData} tintColor={THEME.colors.cyan} />}
    >
      {/* Pilot Basin Header Card */}
      <View style={styles.regionCard}>
        <View style={styles.regionHeader}>
          <Text style={styles.regionTag}>PUNE BASIN FLOOD INTELLIGENCE</Text>
          <StatusBadge
            status={getSystemStatus()}
            label={
              !health
                ? 'Backend Offline'
                : health.status === 'degraded'
                ? 'Degraded'
                : 'Systems Online'
            }
          />
        </View>
        <Text style={styles.regionTitle}>Mula-Mutha River Basin</Text>
        <Text style={styles.regionDesc}>
          Real-time hydrometeorological intelligence, Khadakwasla spillway telemetry, and dynamic safe evacuation routing.
        </Text>
      </View>

      {/* Task B: Current Condition Status Card */}
      <View
        style={[
          styles.alertCard,
          { borderColor: getAlertColor(condition?.condition_status) },
        ]}
      >
        <View style={styles.alertHeader}>
          <Text style={styles.alertCategory}>CURRENT FLOOD ALERT LEVEL</Text>
          {condition && (
            <View style={styles.freshnessBadge}>
              <Text style={styles.freshnessText}>
                {condition.data_freshness_status} ({condition.data_freshness_age_hours.toFixed(1)}h ago)
              </Text>
            </View>
          )}
        </View>

        <Text style={[styles.alertTitle, { color: getAlertColor(condition?.condition_status) }]}>
          {condition ? condition.condition_status.replace(/_/g, ' ') : 'NORMAL CONDITIONS'}
        </Text>

        <Text style={styles.alertGuidance}>
          {condition?.operational_action_recommendation ||
            'Weather and urban drainage parameters within normal seasonal thresholds. Maintain standard vigilance.'}
        </Text>

        {/* Observed Weather Metrics */}
        {condition && (
          <View style={styles.metricGrid}>
            <View style={styles.metricBox}>
              <Text style={styles.metricLabel}>Rain Intensity</Text>
              <Text style={styles.metricVal}>
                {condition.observed_metrics.precipitation_rate_mmh} mm/h
              </Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricLabel}>24h Rain Total</Text>
              <Text style={styles.metricVal}>
                {condition.observed_metrics.rainfall_accum_24h_mm} mm
              </Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricLabel}>Soil Saturation</Text>
              <Text style={styles.metricVal}>
                {condition.observed_metrics.soil_saturation_pct}%
              </Text>
            </View>
            <View style={styles.metricBox}>
              <Text style={styles.metricLabel}>Road Closures</Text>
              <Text
                style={[
                  styles.metricVal,
                  {
                    color:
                      condition.observed_metrics.active_road_closures_count > 0
                        ? THEME.colors.red
                        : THEME.colors.green,
                  },
                ]}
              >
                {condition.observed_metrics.active_road_closures_count} Active
              </Text>
            </View>
          </View>
        )}
      </View>

      {/* Quick Action Navigation Grid */}
      <Text style={styles.sectionHeader}>CITIZEN ACTION SERVICES</Text>

      <TouchableOpacity
        style={styles.actionCard}
        onPress={() => onNavigate('routes')}
      >
        <View style={styles.actionIconBox}>
          <Text style={styles.actionIconText}>🧭</Text>
        </View>
        <View style={styles.actionInfo}>
          <Text style={styles.actionTitle}>Safe Evacuation Routes</Text>
          <Text style={styles.actionDesc}>
            Calculate flood-free routes avoiding submerged causeways and low underpasses.
          </Text>
        </View>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.actionCard}
        onPress={() => onNavigate('shelters')}
      >
        <View style={styles.actionIconBox}>
          <Text style={styles.actionIconText}>🏠</Text>
        </View>
        <View style={styles.actionInfo}>
          <Text style={styles.actionTitle}>High-Ground Shelters</Text>
          <Text style={styles.actionDesc}>
            Locate nearby candidate municipal relief centers with amenities and medical facilities.
          </Text>
        </View>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.actionCard}
        onPress={() => onNavigate('conditions')}
      >
        <View style={styles.actionIconBox}>
          <Text style={styles.actionIconText}>🌊</Text>
        </View>
        <View style={styles.actionInfo}>
          <Text style={styles.actionTitle}>River & Dam Telemetry</Text>
          <Text style={styles.actionDesc}>
            Khadakwasla Dam spillway discharge bulletins and Pune river crossing status.
          </Text>
        </View>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.actionCard, styles.emergencyCard]}
        onPress={() => onNavigate('emergency')}
      >
        <View style={[styles.actionIconBox, { backgroundColor: 'rgba(239, 68, 68, 0.2)' }]}>
          <Text style={styles.actionIconText}>🚨</Text>
        </View>
        <View style={styles.actionInfo}>
          <Text style={[styles.actionTitle, { color: THEME.colors.red }]}>
            Emergency Helplines (112 / PMC)
          </Text>
          <Text style={styles.actionDesc}>
            One-tap dial to PMC Disaster Cell (020-25501269), NDRF, Fire Brigade, and Police.
          </Text>
        </View>
      </TouchableOpacity>

      {/* Mandatory Decision Support Disclaimer */}
      <View style={styles.disclaimerCard}>
        <Text style={styles.disclaimerTitle}>DECISION SUPPORT TOOL NOTICE</Text>
        <Text style={styles.disclaimerText}>
          FLOOD-X is an AI decision-support platform designed for emergency planning. In an imminent life-threatening emergency, follow immediate instructions from the Pune Municipal Corporation (PMC) and National Disaster Response Force (NDRF).
        </Text>
      </View>
    </ScrollView>
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
  regionCard: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.lg,
    padding: 16,
    marginBottom: 16,
  },
  regionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  regionTag: {
    color: THEME.colors.cyan,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    fontFamily: THEME.typography.mono,
  },
  regionTitle: {
    color: THEME.colors.textPrimary,
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 4,
  },
  regionDesc: {
    color: THEME.colors.textSecondary,
    fontSize: 12,
    lineHeight: 18,
  },
  alertCard: {
    backgroundColor: THEME.colors.surface,
    borderWidth: 1.5,
    borderRadius: THEME.borderRadius.lg,
    padding: 16,
    marginBottom: 20,
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  alertCategory: {
    color: THEME.colors.textSecondary,
    fontSize: 10,
    fontWeight: '700',
    fontFamily: THEME.typography.mono,
  },
  freshnessBadge: {
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  freshnessText: {
    color: THEME.colors.cyan,
    fontSize: 10,
    fontWeight: '700',
    fontFamily: THEME.typography.mono,
  },
  alertTitle: {
    fontSize: 20,
    fontWeight: '900',
    marginBottom: 6,
  },
  alertGuidance: {
    color: THEME.colors.textPrimary,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 14,
  },
  metricGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: THEME.colors.border,
  },
  metricBox: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: THEME.colors.surfaceHighlight,
    padding: 10,
    borderRadius: THEME.borderRadius.md,
  },
  metricLabel: {
    color: THEME.colors.textSecondary,
    fontSize: 10,
    marginBottom: 2,
  },
  metricVal: {
    color: THEME.colors.textPrimary,
    fontSize: 14,
    fontWeight: '800',
    fontFamily: THEME.typography.mono,
  },
  sectionHeader: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1,
    fontFamily: THEME.typography.mono,
    marginBottom: 10,
  },
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.lg,
    padding: 14,
    marginBottom: 10,
  },
  emergencyCard: {
    borderColor: 'rgba(239, 68, 68, 0.4)',
    backgroundColor: 'rgba(239, 68, 68, 0.05)',
  },
  actionIconBox: {
    width: 44,
    height: 44,
    borderRadius: THEME.borderRadius.md,
    backgroundColor: THEME.colors.surfaceHighlight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  actionIconText: {
    fontSize: 20,
  },
  actionInfo: {
    flex: 1,
  },
  actionTitle: {
    color: THEME.colors.textPrimary,
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 2,
  },
  actionDesc: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
    lineHeight: 15,
  },
  disclaimerCard: {
    backgroundColor: 'rgba(245, 158, 11, 0.08)',
    borderColor: 'rgba(245, 158, 11, 0.25)',
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 12,
    marginTop: 12,
  },
  disclaimerTitle: {
    color: THEME.colors.amber,
    fontSize: 10,
    fontWeight: '800',
    fontFamily: THEME.typography.mono,
    marginBottom: 4,
  },
  disclaimerText: {
    color: THEME.colors.amber,
    fontSize: 10,
    lineHeight: 14,
  },
});
