import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { THEME } from '../constants/theme';
import { Header } from '../components/Header';
import { StatusBadge } from '../components/StatusBadge';
import { mobileApi } from '../services/api';
import { CurrentConditionResponse, MobileRoadClosure } from '../types/api';

interface Props {
  onBack: () => void;
}

export const FloodConditionsScreen: React.FC<Props> = ({ onBack }) => {
  const [condition, setCondition] = useState<CurrentConditionResponse | null>(null);
  const [closures, setClosures] = useState<MobileRoadClosure[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [condRes, closRes] = await Promise.allSettled([
        mobileApi.getCurrentConditions(),
        mobileApi.getRoadClosures(),
      ]);

      if (condRes.status === 'fulfilled') {
        setCondition(condRes.value);
      }
      if (closRes.status === 'fulfilled') {
        setClosures(closRes.value);
      }
    } catch (e) {
      console.warn('Failed to fetch conditions:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <View style={styles.container}>
      <Header
        title="River & Flood Conditions"
        subtitle="Mula-Mutha river stage & road closures"
        showBack
        onBack={onBack}
      />
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={fetchData} tintColor={THEME.colors.cyan} />}
      >
        {/* Telemetry Status Notice */}
        <View style={styles.noticeCard}>
          <View style={styles.badgeRow}>
            <StatusBadge
              status="healthy"
              label={condition ? `Freshness: ${condition.data_freshness_status}` : 'Offline Proxy'}
            />
          </View>
          <Text style={styles.noticeTitle}>WRD Dam & River Telemetry Bulletin</Text>
          <Text style={styles.noticeText}>
            Note: Live open streaming REST river gauge feeds are not published by WRD Maharashtra. FLOOD-X monitors Khadakwasla Dam spillway discharge bulletins and CPHEEO drainage thresholds.
          </Text>
        </View>

        {/* Current Metrics Overview */}
        {condition && (
          <View style={styles.sectionCard}>
            <Text style={styles.sectionHeader}>HYDROMETEOROLOGICAL OBSERVATIONS</Text>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Rainfall Intensity:</Text>
              <Text style={styles.metricVal}>{condition.observed_metrics.precipitation_rate_mmh} mm/h</Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>24h Cumulative Precipitation:</Text>
              <Text style={styles.metricVal}>{condition.observed_metrics.rainfall_accum_24h_mm} mm</Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Surface Soil Wetness:</Text>
              <Text style={styles.metricVal}>{condition.observed_metrics.soil_saturation_pct}% Saturation</Text>
            </View>
            <View style={styles.metricRow}>
              <Text style={styles.metricLabel}>Dam Discharge Estimate:</Text>
              <Text style={styles.metricVal}>
                {condition.observed_metrics.khadakwasla_discharge_cfs
                  ? `${condition.observed_metrics.khadakwasla_discharge_cfs.toLocaleString()} cfs`
                  : 'Normal (<5,000 cfs)'}
              </Text>
            </View>
          </View>
        )}

        {/* Active Inundation & Road Closures */}
        <Text style={styles.sectionHeader}>ACTIVE ROAD CLOSURES & CAUSEWAYS</Text>
        {closures.length > 0 ? (
          closures.map((c, i) => (
            <View key={i} style={styles.closureCard}>
              <View style={styles.closureHeader}>
                <Text style={styles.closureTitle}>{c.road_name || `Road Segment ${c.road_id}`}</Text>
                <Text style={styles.closureBadge}>CLOSED</Text>
              </View>
              <Text style={styles.closureDesc}>{c.closure_reason}</Text>
            </View>
          ))
        ) : (
          <View style={styles.closureCard}>
            <Text style={styles.closureTitle}>Baba Bhide Causeway (Deccan)</Text>
            <Text style={styles.closureDesc}>
              Low-level causeway connecting Deccan to Narayan Peth. Submersion threshold: 15,000 cfs. Monitored for flash closure.
            </Text>
          </View>
        )}

        {/* Monitored Gauge Stations */}
        <Text style={styles.sectionHeader}>MONITORED BASIN STATIONS</Text>
        {[
          { name: 'Khadakwasla Dam Spillway', basin: 'Mutha River', status: 'Bulletin Monitoring' },
          { name: 'Baba Bhide Low Causeway', basin: 'Mutha River', status: 'Submersion Indicator' },
          { name: 'Sangam Confluence', basin: 'Mula-Mutha Confluence', status: 'Confluence Backwater' },
          { name: 'Bund Garden Weir', basin: 'Mula-Mutha River', status: 'Downstream Outflow' },
        ].map((gauge, i) => (
          <View key={i} style={styles.gaugeItem}>
            <Text style={styles.gaugeName}>{gauge.name}</Text>
            <Text style={styles.gaugeBasin}>{gauge.basin}</Text>
            <Text style={styles.gaugeStatus}>{gauge.status}</Text>
          </View>
        ))}

        {/* Disclaimer */}
        <View style={styles.disclaimerCard}>
          <Text style={styles.disclaimerText}>
            Official emergency notices take precedence. For verified evacuation orders, tune to PMC Disaster Management Cell.
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
  noticeCard: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 16,
    marginBottom: 16,
  },
  badgeRow: {
    marginBottom: 8,
  },
  noticeTitle: {
    color: THEME.colors.textPrimary,
    fontSize: 14,
    fontWeight: '800',
    marginBottom: 6,
  },
  noticeText: {
    color: THEME.colors.textSecondary,
    fontSize: 12,
    lineHeight: 18,
  },
  sectionCard: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 16,
    marginBottom: 16,
  },
  sectionHeader: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1,
    fontFamily: THEME.typography.mono,
    marginBottom: 10,
    marginTop: 8,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: THEME.colors.border,
  },
  metricLabel: {
    color: THEME.colors.textSecondary,
    fontSize: 12,
  },
  metricVal: {
    color: THEME.colors.cyan,
    fontSize: 12,
    fontWeight: '800',
    fontFamily: THEME.typography.mono,
  },
  closureCard: {
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 14,
    marginBottom: 10,
  },
  closureHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  closureTitle: {
    color: THEME.colors.textPrimary,
    fontSize: 13,
    fontWeight: '700',
  },
  closureBadge: {
    backgroundColor: THEME.colors.red,
    color: '#fff',
    fontSize: 9,
    fontWeight: '900',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    fontFamily: THEME.typography.mono,
  },
  closureDesc: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
    lineHeight: 16,
  },
  gaugeItem: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 12,
    marginBottom: 8,
  },
  gaugeName: {
    color: THEME.colors.textPrimary,
    fontSize: 13,
    fontWeight: '700',
  },
  gaugeBasin: {
    color: THEME.colors.cyan,
    fontSize: 11,
    fontFamily: THEME.typography.mono,
    marginTop: 2,
  },
  gaugeStatus: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
    marginTop: 2,
  },
  disclaimerCard: {
    backgroundColor: 'rgba(245, 158, 11, 0.08)',
    borderColor: 'rgba(245, 158, 11, 0.25)',
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 12,
    marginTop: 12,
  },
  disclaimerText: {
    color: THEME.colors.amber,
    fontSize: 10,
    lineHeight: 14,
  },
});
