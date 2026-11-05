import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { THEME } from '../constants/theme';
import { Header } from '../components/Header';
import { mobileApi } from '../services/api';
import { MobileShelterItem } from '../types/api';

interface Props {
  onBack: () => void;
}

export const SheltersScreen: React.FC<Props> = ({ onBack }) => {
  const [shelters, setShelters] = useState<MobileShelterItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterMedical, setFilterMedical] = useState(false);
  const [filterAccessible, setFilterAccessible] = useState(false);

  const fetchShelters = async () => {
    setLoading(true);
    try {
      const items = await mobileApi.getShelters(25);
      setShelters(items);
    } catch (e) {
      console.warn('Failed to load shelters:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShelters();
  }, []);

  const filteredShelters = shelters.filter((s) => {
    if (filterMedical && !s.has_medical_facility) return false;
    if (filterAccessible && !s.is_wheelchair_accessible) return false;
    return true;
  });

  return (
    <View style={styles.container}>
      <Header
        title="High-Ground Shelters"
        subtitle="Candidate municipal relief centers in Pune"
        showBack
        onBack={onBack}
      />
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={fetchShelters} tintColor={THEME.colors.cyan} />}
      >
        {/* Mandatory Provenance & Operational Caution Notice */}
        <View style={styles.noticeCard}>
          <Text style={styles.noticeTag}>CRITICAL OPERATIONAL NOTICE</Text>
          <Text style={styles.noticeTitle}>Candidate Shelter Index Only</Text>
          <Text style={styles.noticeText}>
            Shelters listed below are candidate educational and civic buildings extracted from OpenStreetMap.
            <Text style={{ fontWeight: '800', color: THEME.colors.red }}> ZERO verified municipal beds are officially pre-allocated by PMC.</Text>
            In an emergency, official shelter activation orders are broadcast via PMC Disaster Cell (020-25501269).
          </Text>
        </View>

        {/* Filter Controls */}
        <View style={styles.filterRow}>
          <TouchableOpacity
            style={[styles.filterChip, filterMedical && styles.filterChipActive]}
            onPress={() => setFilterMedical(!filterMedical)}
          >
            <Text style={[styles.filterChipText, filterMedical && styles.filterChipTextActive]}>
              🏥 Medical Facility ({filterMedical ? 'ON' : 'OFF'})
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.filterChip, filterAccessible && styles.filterChipActive]}
            onPress={() => setFilterAccessible(!filterAccessible)}
          >
            <Text style={[styles.filterChipText, filterAccessible && styles.filterChipTextActive]}>
              ♿ Wheelchair Access ({filterAccessible ? 'ON' : 'OFF'})
            </Text>
          </TouchableOpacity>
        </View>

        {/* Shelter List */}
        <Text style={styles.sectionHeader}>
          CANDIDATE RELIEF FACILITIES ({filteredShelters.length})
        </Text>

        {filteredShelters.length > 0 ? (
          filteredShelters.map((s, i) => (
            <View key={i} style={styles.shelterCard}>
              <View style={styles.cardHeader}>
                <Text style={styles.shelterName}>{s.name || `Facility #${s.id}`}</Text>
                <View style={styles.candidateBadge}>
                  <Text style={styles.candidateText}>CANDIDATE</Text>
                </View>
              </View>
              <Text style={styles.shelterType}>{s.facility_type.replace(/_/g, ' ')}</Text>
              {s.address && <Text style={styles.shelterAddr}>{s.address}</Text>}

              <View style={styles.amenityRow}>
                {s.elevation_m && (
                  <View style={styles.amenityBadge}>
                    <Text style={styles.amenityText}>⛰ {s.elevation_m.toFixed(0)}m MSL</Text>
                  </View>
                )}
                {s.has_medical_facility && (
                  <View style={styles.amenityBadge}>
                    <Text style={styles.amenityText}>🏥 Medical Support</Text>
                  </View>
                )}
                {s.is_wheelchair_accessible && (
                  <View style={styles.amenityBadge}>
                    <Text style={styles.amenityText}>♿ Accessible</Text>
                  </View>
                )}
              </View>
            </View>
          ))
        ) : (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyText}>
              {loading ? 'Querying PostGIS shelter index...' : 'No candidate shelters match selected filters.'}
            </Text>
          </View>
        )}
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
    backgroundColor: 'rgba(239, 68, 68, 0.08)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 14,
    marginBottom: 14,
  },
  noticeTag: {
    color: THEME.colors.red,
    fontSize: 9,
    fontWeight: '800',
    fontFamily: THEME.typography.mono,
    letterSpacing: 1,
    marginBottom: 2,
  },
  noticeTitle: {
    color: THEME.colors.textPrimary,
    fontSize: 13,
    fontWeight: '800',
    marginBottom: 4,
  },
  noticeText: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
    lineHeight: 16,
  },
  filterRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  filterChip: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.full,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  filterChipActive: {
    borderColor: THEME.colors.cyan,
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
  },
  filterChipText: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
    fontWeight: '600',
  },
  filterChipTextActive: {
    color: THEME.colors.cyan,
    fontWeight: '800',
  },
  sectionHeader: {
    color: THEME.colors.textSecondary,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    fontFamily: THEME.typography.mono,
    marginBottom: 10,
  },
  shelterCard: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 14,
    marginBottom: 10,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  shelterName: {
    color: THEME.colors.textPrimary,
    fontSize: 14,
    fontWeight: '700',
    flex: 1,
  },
  candidateBadge: {
    backgroundColor: 'rgba(245, 158, 11, 0.2)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 8,
  },
  candidateText: {
    color: THEME.colors.amber,
    fontSize: 9,
    fontWeight: '800',
    fontFamily: THEME.typography.mono,
  },
  shelterType: {
    color: THEME.colors.cyan,
    fontSize: 11,
    fontFamily: THEME.typography.mono,
    marginBottom: 2,
  },
  shelterAddr: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
    marginBottom: 8,
  },
  amenityRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 6,
  },
  amenityBadge: {
    backgroundColor: THEME.colors.surfaceHighlight,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  amenityText: {
    color: THEME.colors.textSecondary,
    fontSize: 10,
  },
  emptyCard: {
    padding: 24,
    alignItems: 'center',
  },
  emptyText: {
    color: THEME.colors.textSecondary,
    fontSize: 12,
  },
});
