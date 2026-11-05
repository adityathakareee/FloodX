/**
 * Mobile TypeScript interfaces synced with FLOOD-X FastAPI backend schemas.
 */

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';
export type DbStatus = 'connected' | 'disconnected' | 'error';
export type ModuleStatus = 'operational' | 'foundation_ready' | 'planned' | 'not_configured';

export interface DatabaseHealth {
  status: DbStatus;
  database_engine: string;
  latency_ms: number | null;
  error: string | null;
}

export interface HealthResponse {
  status: HealthStatus;
  app_name: string;
  app_version: string;
  environment: string;
  timestamp: string;
  uptime_seconds: number;
  database: DatabaseHealth;
}

export interface ModuleReadiness {
  id: string;
  name: string;
  description: string;
  target_phase: number;
  phase_title: string;
  status: ModuleStatus;
  is_operational: boolean;
  implementation_notes?: string | null;
}

export interface PilotRegion {
  name: string;
  state: string;
  latitude: number;
  longitude: number;
  rivers: string[];
  target_dams: string[];
  vulnerability_focus: string;
}

export interface SystemInfoResponse {
  project_name: string;
  project_tagline: string;
  project_version: string;
  api_version: string;
  environment: string;
  current_phase: string;
  pilot_region: PilotRegion;
  system_status: 'operational' | 'degraded' | 'maintenance';
  modules: ModuleReadiness[];
  timestamp: string;
}

export interface ObservedMetrics {
  precipitation_rate_mmh: number;
  rainfall_accum_24h_mm: number;
  forecasted_next_24h_precip_mm?: number | null;
  trailing_24h_source?: string | null;
  surface_soil_moisture_m3m3: number;
  soil_saturation_pct: number;
  river_telemetry_status: string;
  active_road_closures_count: number;
  khadakwasla_discharge_cfs?: number | null;
}

export interface CurrentConditionResponse {
  condition_status: string;
  data_freshness_status: string;
  data_freshness_age_hours: number;
  data_insufficient_reason?: string | null;
  pilot_region: string;
  timestamp_utc: string;
  observed_metrics: ObservedMetrics;
  active_warnings: string[];
  operational_action_recommendation: string;
  data_provenance: Record<string, any>;
  scientific_boundary: string;
}

export interface MobileShelterItem {
  id: number;
  name: string;
  facility_type: string;
  address?: string | null;
  latitude: number;
  longitude: number;
  elevation_m?: number | null;
  is_verified_by_authority: boolean;
  total_capacity: number;
  current_occupancy: number;
  available_capacity: number;
  has_medical_facility: boolean;
  is_wheelchair_accessible: boolean;
  distance_m?: number | null;
}

export interface MobileRoadClosure {
  id: number;
  road_id: string;
  road_name?: string | null;
  closure_reason: string;
  start_latitude?: number | null;
  start_longitude?: number | null;
  is_active: boolean;
}

export interface MobileRoutePlan {
  route_id: string;
  total_distance_km: number;
  estimated_evacuation_time_minutes: number;
  overall_route_safety_tier: string;
  has_waterway_crossings: boolean;
  submerged_bridges_encountered: string[];
  warning_notes: string[];
  waypoints_count: number;
}
