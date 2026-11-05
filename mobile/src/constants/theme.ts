/**
 * Shared mobile visual design tokens matching the FLOOD-X command aesthetic.
 */
import { Platform } from 'react-native';

export const THEME = {
  colors: {
    background: '#070D1E',
    surface: '#0D162B',
    surfaceElevated: '#121F3D',
    surfaceHighlight: '#16254A',
    border: '#1E325F',
    borderLight: '#2C447A',
    
    // Accents
    cyan: '#00F0FF',
    cyanMuted: 'rgba(0, 240, 255, 0.15)',
    blue: '#38BDF8',
    blueMuted: 'rgba(56, 189, 248, 0.15)',
    
    // Status colors
    emerald: '#10B981',
    green: '#10B981',
    emeraldMuted: 'rgba(16, 185, 129, 0.15)',
    amber: '#F59E0B',
    amberMuted: 'rgba(245, 158, 11, 0.15)',
    rose: '#EF4444',
    red: '#EF4444',
    roseMuted: 'rgba(239, 68, 68, 0.15)',
    slate: '#94A3B8',
    
    // Text
    textPrimary: '#F8FAFC',
    textSecondary: '#94A3B8',
    textMuted: '#64748B',
  },
  typography: {
    mono: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  borderRadius: {
    sm: 6,
    md: 10,
    lg: 16,
    full: 9999,
  },
};
