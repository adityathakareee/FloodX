import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { THEME } from '../constants/theme';

interface HeaderProps {
  title: string;
  subtitle?: string;
  showBack?: boolean;
  onBack?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  showBack = false,
  onBack,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.topRow}>
        {showBack && (
          <TouchableOpacity onPress={onBack} style={styles.backBtn} activeOpacity={0.7}>
            <Text style={styles.backText}>‹ Back</Text>
          </TouchableOpacity>
        )}
        <View style={styles.brandRow}>
          <Text style={styles.brandTitle}>FLOOD-X</Text>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>CITIZEN</Text>
          </View>
        </View>
      </View>

      <Text style={styles.title}>{title}</Text>
      {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 16,
    backgroundColor: THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: THEME.colors.border,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  backBtn: {
    paddingRight: 10,
  },
  backText: {
    color: THEME.colors.cyan,
    fontSize: 16,
    fontWeight: '600',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  brandTitle: {
    color: THEME.colors.cyan,
    fontWeight: '900',
    fontSize: 14,
    letterSpacing: 1.5,
  },
  badge: {
    backgroundColor: THEME.colors.cyanMuted,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 6,
    borderWidth: 1,
    borderColor: THEME.colors.cyan,
  },
  badgeText: {
    color: THEME.colors.cyan,
    fontSize: 9,
    fontWeight: 'bold',
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: THEME.colors.textPrimary,
  },
  subtitle: {
    fontSize: 12,
    color: THEME.colors.textSecondary,
    marginTop: 2,
  },
});

