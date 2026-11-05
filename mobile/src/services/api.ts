/**
 * Centralized API Service for FLOOD-X Mobile Application.
 * Supports configurable development API URLs for Android Emulators & Physical Phones.
 */

import { Platform } from 'react-native';
import {
  HealthResponse,
  SystemInfoResponse,
  CurrentConditionResponse,
  MobileShelterItem,
  MobileRoadClosure,
  MobileRoutePlan,
} from '../types/api';

// Platform-aware default API URL:
// - Android Emulator uses 10.0.2.2 loopback to host PC
// - iOS Simulator uses localhost
// - Configurable via EXPO_PUBLIC_API_BASE_URL
const DEFAULT_URL = Platform.select({
  android: 'http://10.0.2.2:8000/api/v1',
  ios: 'http://localhost:8000/api/v1',
  default: 'http://localhost:8000/api/v1',
});

let activeBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL || DEFAULT_URL;

class MobileApiService {
  private baseUrl: string;

  constructor(initialUrl: string) {
    this.baseUrl = initialUrl.replace(/\/+$/, '');
  }

  setBaseUrl(newUrl: string) {
    this.baseUrl = newUrl.replace(/\/+$/, '');
    activeBaseUrl = this.baseUrl;
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  async getHealth(timeoutMs = 4000): Promise<HealthResponse> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`Health status code HTTP ${response.status}`);
      }

      return (await response.json()) as HealthResponse;
    } finally {
      clearTimeout(timer);
    }
  }

  async getSystemInfo(timeoutMs = 4000): Promise<SystemInfoResponse> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/system/info`, {
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`System info status code HTTP ${response.status}`);
      }

      return (await response.json()) as SystemInfoResponse;
    } finally {
      clearTimeout(timer);
    }
  }

  async getCurrentConditions(timeoutMs = 4000): Promise<CurrentConditionResponse> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/ml/current-conditions`, {
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`Conditions error HTTP ${response.status}`);
      }

      return (await response.json()) as CurrentConditionResponse;
    } finally {
      clearTimeout(timer);
    }
  }

  async getShelters(limit = 20, timeoutMs = 4000): Promise<MobileShelterItem[]> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/evacuation/shelters?limit=${limit}`, {
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`Shelters error HTTP ${response.status}`);
      }

      const data = await response.json();
      return (data.items || []) as MobileShelterItem[];
    } finally {
      clearTimeout(timer);
    }
  }

  async getRoadClosures(timeoutMs = 4000): Promise<MobileRoadClosure[]> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/evacuation/closures?active_only=true`, {
        signal: controller.signal,
        headers: { Accept: 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`Road closures error HTTP ${response.status}`);
      }

      const data = await response.json();
      return (data || []) as MobileRoadClosure[];
    } finally {
      clearTimeout(timer);
    }
  }

  async planEvacuationRoute(
    originLat: number,
    originLon: number,
    destinationLat: number,
    destinationLon: number,
    costProfile = 'BALANCED',
    timeoutMs = 5000
  ): Promise<MobileRoutePlan> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/evacuation/routes/plan`, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          origin_lat: originLat,
          origin_lon: originLon,
          destination_lat: destinationLat,
          destination_lon: destinationLon,
          cost_profile: costProfile,
        }),
      });

      if (!response.ok) {
        throw new Error(`Route planning error HTTP ${response.status}`);
      }

      const data = await response.json();
      const primary = data.primary_route;
      return {
        route_id: primary?.route_id || data.chosen_profile || 'primary',
        total_distance_km: primary ? primary.total_distance_m / 1000 : 0,
        estimated_evacuation_time_minutes: primary ? primary.total_travel_time_sec / 60 : 0,
        overall_route_safety_tier: primary?.exposure_summary?.predominant_exposure || 'ELEVATED_RISK',
        has_waterway_crossings: (primary?.caution_segments_count || 0) > 0,
        submerged_bridges_encountered: [],
        warning_notes: data.warnings || [],
        waypoints_count: (primary?.geometry_geojson?.coordinates || []).length,
      };
    } finally {
      clearTimeout(timer);
    }
  }
}

export const mobileApi = new MobileApiService(activeBaseUrl);
