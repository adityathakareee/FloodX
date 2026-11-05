import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { THEME } from '../constants/theme';

interface StatusBadgeProps {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'online' | 'offline' | 'operational' | 'planned' | 'not_configured';
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const getBadgeStyle = () => {
    switch (status) {
      case 'healthy':
      case 'online':
      case 'operational':
        return {
          bg: THEME.colors.emeraldMuted,
          border: THEME.colors.emerald,
          text: THEME.colors.emerald,
          defaultLabel: 'Operational',
        };
      case 'degraded':
        return {
          bg: THEME.colors.amberMuted,
          border: THEME.colors.amber,
          text: THEME.colors.amber,
          defaultLabel: 'Degraded',
        };
      case 'planned':
        return {
          bg: THEME.colors.blueMuted,
          border: THEME.colors.blue,
          text: THEME.colors.blue,
          defaultLabel: 'Planned',
        };
      case 'not_configured':
        return {
          bg: 'rgba(100, 116, 139, 0.2)',
          border: THEME.colors.textMuted,
          text: THEME.colors.textSecondary,
          defaultLabel: 'Not Configured',
        };
      case 'unhealthy':
      case 'offline':
      default:
        return {
          bg: THEME.colors.roseMuted,
          border: THEME.colors.rose,
          text: THEME.colors.rose,
          defaultLabel: 'Offline',
        };
    }
  };

  const style = getBadgeStyle();

  return (
    <View style={[styles.container, { backgroundColor: style.bg, borderColor: style.border }]}>
      <View style={[styles.dot, { backgroundColor: style.text }]} />
      <Text style={[styles.text, { color: style.text }]}>
        {label || style.defaultLabel}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: THEME.borderRadius.full,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  text: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
});

