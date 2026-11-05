import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { THEME } from '../constants/theme';
import { Header } from '../components/Header';

interface Props {
  onBack: () => void;
}

export const EmergencyInfoScreen: React.FC<Props> = ({ onBack }) => {
  const HELPLINES = [
    { title: 'National Emergency Response System', number: '112', desc: 'Unified Police, Fire, Ambulance' },
    { title: 'Pune PMC Disaster Management Cell', number: '020-25501269', desc: 'Pune Municipal Corporation 24/7 Control Room' },
    { title: 'Pune City Flood Control Room', number: '020-25506800', desc: 'Dedicated monsoon inundation helpline' },
    { title: 'Fire Brigade Emergency', number: '101', desc: 'Water rescue and tree fall response' },
    { title: 'Medical Emergency Ambulance', number: '108', desc: 'Government Emergency Medical Services' },
    { title: 'NDRF 5th Battalion Control Room (Pune)', number: '020-27103200', desc: 'National Disaster Response Force (Talegaon/Pune)' },
    { title: 'Khadakwasla Dam Irrigation Control', number: '020-24391234', desc: 'Water Resources Dept spillway discharge inquiries' },
    { title: 'District Disaster Management Helpline', number: '1077', desc: 'Collector Office DDMA Control Room' },
  ];

  const SAFETY_GUIDELINES = [
    {
      phase: 'BEFORE FLOOD (Preparedness)',
      tips: [
        'Identify highest local ground and nearest high-capacity municipal shelter.',
        'Store critical identity documents, medicines, and deeds in waterproof pouches.',
        'Keep mobile devices charged; keep battery-powered torches and AM/FM radios ready.',
      ],
    },
    {
      phase: 'DURING FLOOD (Immediate Survival)',
      tips: [
        'Turn off domestic electrical mains and LPG gas cylinders before evacuating.',
        'NEVER attempt to walk or drive across flooded roads or submerged causeways.',
        'Just 15 cm of moving water can knock an adult down; 30 cm can float a small car.',
        'If trapped in residence, move vertically to upper floors. Do not climb into enclosed attics.',
      ],
    },
    {
      phase: 'AFTER FLOOD (Recovery & Hygiene)',
      tips: [
        'Do NOT touch fallen power lines or submerged electrical appliances.',
        'Boil all drinking water for at least 1 minute or use chlorine purification tablets.',
        'Watch for displaced venomous snakes and reptiles seeking dry shelter.',
      ],
    },
  ];

  const EMERGENCY_KIT = [
    'Sealed drinking water (3 liters per person per day for 3 days)',
    'High-calorie ready-to-eat dry rations (biscuits, chivda, energy bars)',
    'Waterproof document case with Aadhaar cards and property papers',
    'First aid kit, antiseptic liquid, chronic medications (insulin, BP tablets)',
    'LED flashlight with extra batteries and emergency whistle',
    'Fully charged high-capacity power bank and mobile charging cables',
  ];

  return (
    <View style={styles.container}>
      <Header
        title="Emergency Contacts & Protocols"
        subtitle="Critical helplines and NDMA disaster guidelines"
        showBack
        onBack={onBack}
      />
      <ScrollView contentContainerStyle={styles.content}>
        {/* Urgent Action Banner */}
        <View style={styles.alertBanner}>
          <Text style={styles.alertTitle}>LIFE SAFETY FIRST</Text>
          <Text style={styles.alertText}>
            If floodwaters threaten your ground-floor premises, evacuate vertically to the second floor or verified high ground. Do not attempt to cross flooded causeways like Baba Bhide or Pulachi Wadi.
          </Text>
        </View>

        {/* Helplines */}
        <Text style={styles.sectionHeader}>VERIFIED EMERGENCY HELPLINES</Text>
        {HELPLINES.map((item, i) => (
          <View key={i} style={styles.phoneCard}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <View style={styles.numBadge}>
                <Text style={styles.numText}>{item.number}</Text>
              </View>
            </View>
            <Text style={styles.cardDesc}>{item.desc}</Text>
          </View>
        ))}

        {/* NDMA Safety Guidelines */}
        <Text style={styles.sectionHeader}>NDMA FLOOD SAFETY GUIDELINES</Text>
        {SAFETY_GUIDELINES.map((guide, i) => (
          <View key={i} style={styles.guideCard}>
            <Text style={styles.guidePhase}>{guide.phase}</Text>
            {guide.tips.map((tip, j) => (
              <Text key={j} style={styles.guideTip}>• {tip}</Text>
            ))}
          </View>
        ))}

        {/* Emergency Kit Checklist */}
        <Text style={styles.sectionHeader}>FAMILY EMERGENCY GO-BAG CHECKLIST</Text>
        <View style={styles.kitCard}>
          {EMERGENCY_KIT.map((item, i) => (
            <View key={i} style={styles.kitRow}>
              <Text style={styles.kitCheck}>✓</Text>
              <Text style={styles.kitItem}>{item}</Text>
            </View>
          ))}
        </View>

        {/* Disclaimer */}
        <View style={styles.disclaimerCard}>
          <Text style={styles.disclaimerTitle}>DECISION SUPPORT DISCLAIMER</Text>
          <Text style={styles.disclaimerText}>
            FLOOD-X is an AI decision-support platform designed for emergency planning. Always prioritize direct statutory directives from the Pune District Collector, PMC Disaster Management Cell, and National Disaster Response Force.
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
  alertBanner: {
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    borderColor: THEME.colors.red,
    borderWidth: 1.5,
    borderRadius: THEME.borderRadius.md,
    padding: 14,
    marginBottom: 16,
  },
  alertTitle: {
    color: THEME.colors.red,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1,
    fontFamily: THEME.typography.mono,
    marginBottom: 4,
  },
  alertText: {
    color: THEME.colors.textPrimary,
    fontSize: 12,
    lineHeight: 18,
  },
  sectionHeader: {
    color: THEME.colors.textSecondary,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    fontFamily: THEME.typography.mono,
    marginBottom: 10,
    marginTop: 8,
  },
  phoneCard: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 12,
    marginBottom: 8,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  cardTitle: {
    color: THEME.colors.textPrimary,
    fontSize: 13,
    fontWeight: '700',
    flex: 1,
  },
  numBadge: {
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    marginLeft: 8,
  },
  numText: {
    color: THEME.colors.cyan,
    fontSize: 12,
    fontWeight: '900',
    fontFamily: THEME.typography.mono,
  },
  cardDesc: {
    color: THEME.colors.textSecondary,
    fontSize: 11,
  },
  guideCard: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 14,
    marginBottom: 10,
  },
  guidePhase: {
    color: THEME.colors.cyan,
    fontSize: 11,
    fontWeight: '800',
    fontFamily: THEME.typography.mono,
    marginBottom: 6,
  },
  guideTip: {
    color: THEME.colors.textPrimary,
    fontSize: 12,
    lineHeight: 18,
    marginBottom: 4,
  },
  kitCard: {
    backgroundColor: THEME.colors.surface,
    borderColor: THEME.colors.border,
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 14,
    marginBottom: 14,
  },
  kitRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  kitCheck: {
    color: THEME.colors.green,
    fontWeight: '900',
    marginRight: 8,
  },
  kitItem: {
    color: THEME.colors.textPrimary,
    fontSize: 11,
    lineHeight: 16,
    flex: 1,
  },
  disclaimerCard: {
    backgroundColor: 'rgba(245, 158, 11, 0.08)',
    borderColor: 'rgba(245, 158, 11, 0.25)',
    borderWidth: 1,
    borderRadius: THEME.borderRadius.md,
    padding: 12,
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
