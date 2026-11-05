import React, { useState } from 'react';
import { SafeAreaView, StatusBar, StyleSheet, View } from 'react-native';
import { StatusBar as ExpoStatusBar } from 'expo-status-bar';
import { THEME } from './src/constants/theme';

import { WelcomeScreen } from './src/screens/WelcomeScreen';
import { HomeScreen } from './src/screens/HomeScreen';
import { FloodConditionsScreen } from './src/screens/FloodConditionsScreen';
import { SafeRoutesScreen } from './src/screens/SafeRoutesScreen';
import { SheltersScreen } from './src/screens/SheltersScreen';
import { EmergencyInfoScreen } from './src/screens/EmergencyInfoScreen';
import { ProfileSettingsScreen } from './src/screens/ProfileSettingsScreen';

type Screen =
  | 'welcome'
  | 'home'
  | 'conditions'
  | 'routes'
  | 'shelters'
  | 'emergency'
  | 'settings';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('welcome');

  const renderScreen = () => {
    switch (currentScreen) {
      case 'welcome':
        return <WelcomeScreen onContinue={() => setCurrentScreen('home')} />;
      case 'home':
        return <HomeScreen onNavigate={(s) => setCurrentScreen(s as Screen)} />;
      case 'conditions':
        return <FloodConditionsScreen onBack={() => setCurrentScreen('home')} />;
      case 'routes':
        return <SafeRoutesScreen onBack={() => setCurrentScreen('home')} />;
      case 'shelters':
        return <SheltersScreen onBack={() => setCurrentScreen('home')} />;
      case 'emergency':
        return <EmergencyInfoScreen onBack={() => setCurrentScreen('home')} />;
      case 'settings':
        return <ProfileSettingsScreen onBack={() => setCurrentScreen('home')} />;
      default:
        return <HomeScreen onNavigate={(s) => setCurrentScreen(s as Screen)} />;
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ExpoStatusBar style="light" />
      <View style={styles.container}>{renderScreen()}</View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: THEME.colors.background,
    paddingTop: StatusBar.currentHeight || 0,
  },
  container: {
    flex: 1,
    backgroundColor: THEME.colors.background,
  },
});

