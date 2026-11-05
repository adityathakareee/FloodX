/**
 * Shared API response types synced with FLOOD-X FastAPI backend schemas.
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

export interface ApiError {
  code: number;
  message: string;
  details?: unknown;
  path?: string;
}

export interface ApiErrorResponse {
  error: ApiError;
}

// ==========================================
// Phase 1 Stage 2 Data Ingestion & Monitoring Types
// ==========================================

export interface DataSourceItem {
  id: number;
  source_name: string;
  source_type: string;
  provider: string;
  description?: string;
  data_format: string;
  units?: string;
  temporal_resolution?: string;
  spatial_resolution?: string;
  is_active: boolean;
  metadata_json?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface IngestionLogItem {
  id: number;
  source_id: number;
  file_name?: string;
  status: string;
  records_read: number;
  records_inserted: number;
  records_skipped: number;
  records_failed: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface IngestionOverview {
  counts: {
    data_sources: number;
    rainfall_observations: number;
    weather_observations: number;
    river_level_observations: number;
    spatial_features: number;
    data_quality_issues: number;
    ingestion_logs: number;
  };
  breakdowns: {
    spatial_features: Record<string, number>;
    rainfall_observations: Record<string, number>;
    weather_observations: Record<string, number>;
    river_level_observations: Record<string, number>;
  };
  recent_logs: IngestionLogItem[];
  quality_issues: DataQualityIssueItem[];
}

export interface DataQualityIssueItem {
  id: number;
  source_id: number;
  issue_type: string;
  severity: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  affected_record_count: number;
  detected_at: string;
  resolution_status: string;
  metadata_json?: Record<string, any>;
}

export interface DataQualitySummary {
  total_issues: number;
  by_severity: Record<string, number>;
  issues: DataQualityIssueItem[];
}

export interface RainfallObservationItem {
  id: number;
  source_id: number;
  station_name: string;
  latitude: number;
  longitude: number;
  observation_time: string;
  rainfall_value: number;
  rainfall_unit: string;
  measurement_type: string;
  quality_flag: string;
  metadata_json?: Record<string, any>;
}

export interface WeatherObservationItem {
  id: number;
  source_id: number;
  location_name: string;
  latitude: number;
  longitude: number;
  observation_time: string;
  data_category: string;
  temperature?: number;
  relative_humidity?: number;
  precipitation?: number;
  wind_speed?: number;
  wind_direction?: number;
  soil_moisture?: number;
  quality_flag: string;
  metadata_json?: Record<string, any>;
}

export interface RiverLevelObservationItem {
  id: number;
  source_id: number;
  station_name: string;
  river_name: string;
  station_code?: string;
  latitude?: number;
  longitude?: number;
  observation_time: string;
  water_level: number;
  level_unit: string;
  vertical_datum: string;
  geographic_relevance: string;
  quality_flag: string;
  metadata_json?: Record<string, any>;
}

export interface SpatialFeatureItem {
  id: number;
  source_id: number;
  feature_type: string;
  osm_id?: string;
  name?: string;
  properties_json?: Record<string, any>;
  geojson?: {
    type: string;
    coordinates: any;
  };
  created_at: string;
}

export interface PaginatedResult<T> {
  total: number;
  limit: number;
  offset: number;
  items: T[];
}

export interface GISSummary {
  total_features: number;
  layer_counts: Record<string, number>;
  study_domain: string;
}

export interface RainfallSummary {
  total_records: number;
  cwprs_24h_cumulative_peak_mm: number;
  cwprs_peak_event: string;
  chirps_basin_daily_peak_mm: number;
  stations: string[];
}

export interface FeatureDatasetItem {
  id: number;
  feature_set_name: string;
  category: 'RAINFALL' | 'WEATHER' | 'TERRAIN' | 'GEOSPATIAL' | 'INTEGRATED' | string;
  file_path_csv?: string;
  file_path_parquet?: string;
  total_records: number;
  columns_json?: string[];
  temporal_range?: string;
  spatial_domain?: string;
  quality_notes?: string;
  provenance_manifest?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface FeatureSummary {
  total_feature_sets: number;
  categories: Record<string, number>;
  total_records: number;
  feature_sets: FeatureDatasetItem[];
}

export interface IntegratedSampleRecord {
  observation_time: string;
  hour_index: number;
  date_str: string;
  cwprs_rainfall_1h_sum_mm?: number;
  cwprs_peak_5min_intensity_mmh?: number;
  cwprs_rolling_6h_mm?: number;
  cwprs_rolling_24h_mm?: number;
  weather_temperature_c?: number;
  weather_vpd_kpa?: number;
  weather_soil_saturation_index?: number;
  has_chirps_daily: boolean;
  chirps_basin_max_mm_day?: number;
  local_river_gauge_available: boolean;
  cloudburst_trigger_flag: boolean;
  runoff_susceptibility_score?: number;
}

// ==================== PHASE 2.2: ML FLOOD INTELLIGENCE TYPES ====================

export interface MLStatusResponse {
  status: 'READY' | 'TRAINING_REQUIRED' | 'ERROR';
  active_model: string;
  training_data_coverage: {
    start_date: string;
    end_date: string;
    total_days: number;
    train_days: number;
    validation_days: number;
    test_days: number;
    total_positive_flood_days: number;
    pilot_region: string;
  };
  scientific_limitations_acknowledged: boolean;
  timestamp_utc: string;
}

export interface MLModelMetadata {
  model_name: string;
  model_type: string;
  version: string;
  artifact_path: string;
  feature_count: number;
  features: string[];
  target_variable: string;
  training_period: string;
  validation_period: string;
  test_period: string;
  class_imbalance_handling: string;
}

export interface MLEvaluationMetric {
  model_name: string;
  decision_threshold: number;
  threshold_type: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number | null;
  pr_auc: number | null;
  test_events_detected?: string | null;
  confusion_matrix: {
    true_negatives: number;
    false_positives: number;
    false_negatives: number;
    true_positives: number;
  };
  class_distribution_test: {
    negative_days: number;
    positive_days: number;
  };
}

export interface MLEvaluationResponse {
  title: string;
  pilot_region: string;
  target_variable: string;
  prediction_task: string;
  models_evaluated: MLEvaluationMetric[];
  best_model_name: string;
  scientific_verdict: string;
  threshold_audit_note: string;
  test_events_count: number;
  validation_events_count: number;
  scientific_limitations: string[];
}

export interface MLFeatureContribution {
  feature: string;
  input_value: number;
  importance_weight: number;
}

export interface MLPredictionRequest {
  precip_total_24h?: number;
  precip_max_1h?: number;
  antecedent_precip_3d?: number;
  antecedent_precip_7d?: number;
  temp_2m_mean?: number;
  relative_humidity_mean?: number;
  surface_pressure_mean?: number;
  pressure_drop_24h?: number;
  soil_moisture_0_7cm_mean?: number;
  soil_moisture_0_7cm_max?: number;
  soil_moisture_7_28cm_mean?: number;
  vpd_mean_kpa?: number;
  wind_speed_max?: number;
  is_monsoon?: number;
}

export interface MLPredictionResponse {
  prediction_status: string;
  prediction_task: string;
  operational_readiness: string;
  model_version: string;
  flood_event_risk_probability: number;
  decision_threshold: number;
  threshold_source: string;
  test_independent_events_count: number;
  validation_status: string;
  risk_tier: 'NORMAL' | 'WATCH' | 'WARNING' | 'EMERGENCY' | string;
  alert_color: 'green' | 'yellow' | 'orange' | 'red' | string;
  operational_action_guidance: string;
  key_driving_factors: MLFeatureContribution[];
  input_summary: Record<string, any>;
  scientific_boundary: string;
}

export interface MLExplainabilityResponse {
  model_name: string;
  methodology: string;
  top_features: Array<{ feature: string; importance_score: number }>;
  all_features_importance: Array<{ feature: string; importance_score: number }>;
  physical_hydrology_explanation: string;
  scientific_caveats: string;
}

export interface ChronicHotspot {
  name: string;
  latitude: number;
  longitude: number;
  hazard_type: string;
  description: string;
  verified_inundation_depth_m: string;
  vulnerability_tier: string;
  sfsi_score: number;
  computed_tier: string;
  action_guidance: string;
}

export interface SpatialSusceptibilityResponse {
  title: string;
  pilot_basin: string;
  model_type: string;
  validation_status: string;
  methodology: string;
  hotspots_count: number;
  tier_distribution: Record<string, number>;
  chronic_hotspots: ChronicHotspot[];
  surface_canopy_bias_note: string;
  disclaimer: string;
}

// ==========================================
// Phase 2.3 Prospective Flood-Risk Intelligence Types
// ==========================================

export interface SourceAssessmentItem {
  official_name: string;
  url: string;
  variables_available: string[];
  geographic_coverage: string;
  update_frequency: string;
  forecast_horizon: string;
  timestamp_conventions: string;
  authentication_requirements: string;
  license_restrictions: string;
  reliability_limitations: string;
  access_mode: 'AUTOMATIC' | 'MANUAL_REGISTRATION' | 'RESTRICTED_DEPARTMENTAL' | string;
  operational_integration_status: string;
}

export interface ProspectiveSourcesResponse {
  title: string;
  audit_date: string;
  sources: SourceAssessmentItem[];
  live_dam_telemetry_status: string;
  recommendations: string[];
}

export interface ProspectiveStatusResponse {
  status: 'READY' | 'DEGRADED' | 'STALE' | 'ERROR';
  engine_name: string;
  engine_type: string;
  prediction_task: string;
  horizons_supported: string[];
  forecast_source: string;
  forecast_freshness_status: string;
  forecast_issue_time_utc: string;
  api_retrieval_time_utc?: string;
  cache_age_hours?: number;
  forecast_age_hours?: number;
  freshness_warning?: string;
  dam_telemetry_status: string;
  human_verification_required: boolean;
  timestamp_utc: string;
}

export interface ForecastHourlyPoint {
  valid_time_iso: string;
  valid_time_utc: string;
  lead_hours: number;
  precipitation_mm: number;
  precipitation_probability_pct: number;
  rain_mm: number;
  temperature_2m_c: number;
  relative_humidity_pct: number;
  surface_pressure_hpa: number;
  wind_speed_10m_kmh: number;
  wind_direction_10m_deg: number;
  soil_moisture_0_7cm: number;
}

export interface ProspectiveForecastResponse {
  pilot_region: string;
  issue_time_utc: string;
  timezone: string;
  forecast_horizon_hours: number;
  record_count: number;
  forecast_points: ForecastHourlyPoint[];
  source_metadata: Record<string, any>;
  data_freshness_status?: string;
}

export interface PluvialRiskAssessment {
  flood_mechanism: string;
  risk_tier: 'NORMAL' | 'WATCH' | 'WARNING' | 'EMERGENCY' | string;
  risk_score: number;
  drainage_threshold_mmh: number;
  drainage_threshold_status?: string;
  peak_forecast_intensity_mmh: number;
  forecast_accumulation_mm: number;
  antecedent_soil_saturation_ratio: number;
  soil_wetness_indicator?: number;
  contributing_factors: string[];
  physical_reasoning: string;
  threshold_audit_metadata?: Record<string, any>;
}

export interface RiverineRiskAssessment {
  flood_mechanism: string;
  risk_tier: 'NORMAL' | 'WATCH' | 'WARNING' | 'EMERGENCY' | 'DATA_INSUFFICIENT' | string;
  risk_score: number | null;
  dam_telemetry_status: 'DATA_INSUFFICIENT' | 'SIMULATED_SCENARIO' | 'VERIFIED_FEED' | string;
  simulated_dam_discharge_cfs: number | null;
  bhide_causeway_threshold_cfs: number;
  july2024_disaster_threshold_cfs: number;
  benchmark_verification_status?: string;
  contributing_factors: string[];
  physical_reasoning: string;
  benchmark_metadata?: Record<string, any>;
}

export interface HorizonProspectiveAssessment {
  horizon_label: string;
  horizon_hours: number;
  valid_from_utc: string;
  valid_to_utc: string;
  forecast_rain_accumulation_mm: number;
  max_1h_rainfall_intensity_mmh: number;
  mean_precipitation_probability_pct: number;
  antecedent_3d_rain_mm: number;
  antecedent_soil_moisture: number;
  pluvial_risk: PluvialRiskAssessment;
  riverine_risk: RiverineRiskAssessment;
  overall_alert_level: string;
  alert_color: string;
  operational_action_guidance: string;
  human_verification_required: boolean;
}

export interface ProspectiveAssessmentResponse {
  assessment_id: string;
  issue_time_utc: string;
  valid_until_utc: string;
  pilot_region: string;
  data_provenance: Record<string, any>;
  horizons: Record<string, HorizonProspectiveAssessment>;
  overall_summary: string;
  scientific_boundaries: string;
  human_verification_notice: string;
}

export interface ScenarioAssessmentRequest {
  scenario_name: string;
  rainfall_multiplier?: number;
  override_peak_1h_mmh?: number;
  simulated_dam_discharge_cfs?: number;
  override_soil_moisture?: number;
  override_antecedent_3d_mm?: number;
}

export interface ScenarioAssessmentResponse {
  scenario_name: string;
  is_simulated: boolean;
  simulation_tag: string;
  simulated_dam_discharge_cfs?: number | null;
  horizons: Record<string, HorizonProspectiveAssessment>;
  comparison_with_baseline: Record<string, any>;
  operational_disclaimer: string;
}

// =========================================================================
// PHASE 3.1: ROAD NETWORK INTELLIGENCE & GIS GRAPH SCHEMAS
// =========================================================================

export interface GraphNodeItem {
  node_id: number;
  latitude: number;
  longitude: number;
  layer: number;
  in_degree: number;
  out_degree: number;
  total_degree: number;
}

export interface GraphEdgeItem {
  edge_id: string;
  source_node: number;
  destination_node: number;
  source_feature_id: number;
  osm_id: string;
  name: string;
  highway: string;
  length_m: number;
  estimated_travel_time_sec: number;
  speed_limit_kmh: number;
  speed_is_default: boolean;
  speed_source: string;
  surface: string;
  is_oneway: boolean;
  directionality_status: 'VERIFIED_ONEWAY' | 'VERIFIED_BIDIRECTIONAL' | 'UNKNOWN_DIRECTIONALITY';
  is_direction_assumed: boolean;
  is_bridge: boolean;
  is_tunnel: boolean;
  layer: number;
  access: string;
  geometry_geojson?: {
    type: string;
    coordinates: number[][];
  };
}

export interface NetworkStatusResponse {
  status: 'READY' | 'REBUILDING' | 'DEGRADED' | 'ERROR';
  graph_name: string;
  graph_type: string;
  build_timestamp_utc: string;
  source_dataset: string;
  source_features_count: number;
  node_count: number;
  edge_count: number;
  parallel_edges_count: number;
  connected_components_count: number;
  largest_component_nodes: number;
  largest_component_percentage: number;
  isolated_nodes_count: number;
  total_mapped_length_km: number;
  snap_tolerance_meters: number;
  directionality_breakdown: Record<string, number>;
  snapping_audit: Record<string, any>;
  data_quality_status: string;
  coverage_warning: string;
}

export interface NetworkStatisticsResponse {
  total_source_features: number;
  graph_type: string;
  total_nodes: number;
  total_edges: number;
  parallel_edges_count: number;
  total_length_km: number;
  connected_components: number;
  largest_component_nodes: number;
  largest_component_percentage: number;
  highway_breakdown: Record<string, number>;
  highway_length_km: Record<string, number>;
  oneway_breakdown: Record<string, number>;
  directionality_breakdown: Record<string, number>;
  surface_breakdown: Record<string, number>;
  speed_limit_coverage: {
    tagged_count: number;
    default_count: number;
    observed_speeds: Record<string, number>;
  };
  speed_source_breakdown: Record<string, number>;
  snapping_audit: Record<string, any>;
  degree_distribution: Record<string, number>;
  top_component_sizes: number[];
  bridges_count: number;
  tunnels_count: number;
  dead_ends_count: number;
  intersections_count: number;
}

export interface RoadsPaginatedResponse {
  total: number;
  limit: number;
  offset: number;
  items: GraphEdgeItem[];
}

export interface NodesPaginatedResponse {
  total: number;
  limit: number;
  offset: number;
  items: GraphNodeItem[];
}

export interface RebuildResponse {
  success: boolean;
  message: string;
  nodes_built: number;
  edges_built: number;
  elapsed_seconds: number;
  timestamp_utc: string;
}

// ============================================================================
// PHASE 3.2: FLOOD-AWARE EVACUATION & SHELTER INTELLIGENCE TYPES
// ============================================================================

export type RoadSafetyStatus = 'SAFE' | 'CAUTION' | 'HAZARDOUS' | 'IMPASSABLE';
export type ExposureTier = 'LOW_EXPOSURE' | 'MODERATE_EXPOSURE' | 'HIGH_EXPOSURE' | 'CRITICAL_EXPOSURE' | 'UNKNOWN_EXPOSURE';
export type ShelterVerificationStatus = 'VERIFIED_SHELTER' | 'CANDIDATE_SHELTER' | 'UNVERIFIED_FACILITY' | 'INACTIVE_SHELTER';
export type EvacuationCostProfile = 'FASTEST' | 'SAFEST' | 'BALANCED';

export interface RoadExposureItem {
  edge_id: string;
  source_node: number;
  destination_node: number;
  road_name: string;
  highway: string;
  length_m: number;
  min_elevation_m: number;
  mean_elevation_m: number;
  relative_elevation_m: number;
  waterway_distance_m: number;
  local_slope_deg: number;
  exposure_tier: ExposureTier;
  exposure_reason: string;
  is_chronic_hotspot: boolean;
  evidence_provenance: string;
  assessment_timestamp_utc: string;
}

export interface RoadSafetyItem {
  edge_id: string;
  road_name: string;
  highway: string;
  exposure_tier: string;
  operational_status: RoadSafetyStatus;
  is_blocked: boolean;
  closure_reason?: string | null;
  closure_authority?: string | null;
  directionality_status: string;
  is_direction_assumed: boolean;
  is_bridge: boolean;
  is_tunnel: boolean;
  dynamic_travel_penalty_sec: number;
  safety_summary: string;
}

export interface InfrastructureSafetyItem {
  id: string;
  name: string;
  infrastructure_type: 'BRIDGE' | 'LOW_CAUSEWAY' | 'UNDERPASS' | 'FLYOVER' | string;
  osm_id?: number | null;
  latitude: number;
  longitude: number;
  waterway_proximity_m: number;
  terrain_elevation_m: number;
  status: string;
  status_reason: string;
  unverified_operational_reference_cfs?: number | null;
  submergence_reference_cfs?: number | null;
  scenario_type?: string | null;
  provenance_note?: string | null;
  is_closed: boolean;
  is_submerged_simulated?: boolean;
  connected_edge_ids: string[];
  last_assessment_utc: string;
}

export interface RoadClosureItem {
  id: number;
  edge_id: string;
  road_name: string;
  closure_status: string;
  reason: string;
  verification_source: string;
  reporting_authority: string;
  is_active: boolean;
  effective_from: string;
  effective_to?: string | null;
  created_at: string;
}

export interface RoadClosureCreate {
  edge_id: string;
  road_name: string;
  reason: string;
  closure_status?: string;
  closure_type?: string;
  verification_source?: string;
  reporting_authority: string;
  operator_notes?: string;
  is_active?: boolean;
  effective_hours?: number;
}

export interface ShelterItem {
  id: number;
  facility_id: string;
  osm_id?: string | null;
  name: string;
  facility_type: string;
  verification_status: ShelterVerificationStatus;
  address?: string | null;
  latitude: number;
  longitude: number;
  total_capacity?: number | null;
  current_occupancy?: number | null;
  available_capacity?: number | null;
  has_medical_support: boolean;
  is_wheelchair_accessible: boolean;
  has_generator_power: boolean;
  emergency_contact?: string | null;
  source: string;
  evidence_document?: string | null;
  evidence_date?: string | null;
  verified_by?: string | null;
  verified_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ShelterCreate {
  name: string;
  facility_type?: string;
  verification_status?: ShelterVerificationStatus;
  address?: string | null;
  latitude: number;
  longitude: number;
  total_capacity?: number | null;
  has_medical_support?: boolean;
  is_wheelchair_accessible?: boolean;
  has_generator_power?: boolean;
  emergency_contact?: string | null;
  source?: string;
  verified_by?: string | null;
}

export interface ShelterUpdate {
  total_capacity?: number | null;
  current_occupancy?: number | null;
  verification_status?: ShelterVerificationStatus;
  has_medical_support?: boolean;
  is_wheelchair_accessible?: boolean;
  notes?: string | null;
  updated_by?: string;
}

export interface RouteRequest {
  origin_lat: number;
  origin_lon: number;
  destination_lat?: number | null;
  destination_lon?: number | null;
  destination_shelter_id?: number | null;
  cost_profile: EvacuationCostProfile;
  vehicle_type?: string;
  algorithm?: 'A_STAR' | 'DIJKSTRA';
  avoid_closed_roads?: boolean;
  find_alternatives?: boolean;
}

export interface RouteAlternativeItem {
  route_id: string;
  route_label: string;
  profile: string;
  algorithm: string;
  total_distance_m: number;
  total_travel_time_sec: number;
  steps_count: number;
  exposure_summary: Record<string, number>;
  hazardous_segments_count: number;
  caution_segments_count: number;
  assumed_direction_segments_count: number;
  shared_edges_count?: number;
  shared_distance_m?: number;
  overlap_percentage?: number;
  data_freshness_utc?: string;
  directionality_uncertainty_note?: string;
  speed_assumptions_note?: string;
  geometry_geojson: {
    type: string;
    coordinates: [number, number][];
  };
  explanation: string;
}

export interface RoutePlanResponse {
  status: 'SUCCESS' | 'NO_PATH' | 'OUT_OF_BOUNDS' | 'ERROR';
  origin_snapped_node: number;
  origin_snap_distance_m: number;
  destination_snapped_node: number;
  destination_snap_distance_m: number;
  chosen_profile: string;
  algorithm_used: string;
  primary_route: RouteAlternativeItem | null;
  alternatives: RouteAlternativeItem[];
  avoided_closures_count: number;
  warnings: string[];
  disclaimer: string;
  generated_at_utc: string;
}

export interface ShelterRecommendationItem {
  shelter: ShelterItem;
  distance_to_origin_m: number;
  estimated_travel_time_sec: number;
  safest_route_hazard_tier: string;
  is_reachable: boolean;
  suitability_score: number;
  ranking_rationale: string;
  capacity_status: string;
}

export interface ShelterRecommendationResponse {
  origin_lat: number;
  origin_lon: number;
  status?: string;
  total_evaluated: number;
  recommendations: ShelterRecommendationItem[];
  candidate_facilities_for_review?: ShelterRecommendationItem[];
  warnings: string[];
  generated_at_utc: string;
}

export interface EvacuationStatusResponse {
  status: string;
  graph_type: string;
  total_network_edges: number;
  total_safe_edges: number;
  total_caution_edges: number;
  total_hazardous_edges: number;
  total_impassable_edges: number;
  active_road_closures: number;
  total_registered_shelters: number;
  verified_shelters_count: number;
  candidate_shelters_count: number;
  critical_bridges_count: number;
  submerged_bridges_simulated: number;
  last_assessment_timestamp_utc: string;
  data_quality_disclaimer: string;
}

export interface EvacuationStatisticsResponse {
  exposure_tier_distribution: Record<string, number>;
  operational_status_distribution: Record<string, number>;
  shelter_status_distribution: Record<string, number>;
  total_verified_capacity: number | null;
  total_verified_occupancy: number;
  active_closures_count: number;
  infrastructure_monitored_count: number;
}


// ============================================================================
// Phase 4: Emergency Resource Optimization & Decision Intelligence Types
// ============================================================================

export type ResourceCategory = 'EMERGENCY_VEHICLE' | 'HUMAN_RESOURCE' | 'RELIEF_RESOURCE' | 'INFRASTRUCTURE';
export type ResourceOperationalStatus = 'AVAILABLE' | 'ALLOCATED' | 'DEPLOYED' | 'UNAVAILABLE' | 'UNDER_MAINTENANCE' | 'UNKNOWN_STATUS';
export type PriorityLevel = 'CRITICAL_PRIORITY' | 'HIGH_PRIORITY' | 'MODERATE_PRIORITY' | 'LOW_PRIORITY' | 'INSUFFICIENT_DATA';

export interface ResourceItem {
  id: number;
  resource_id: string;
  category: string;
  resource_type: string;
  name: string;
  description?: string | null;
  total_quantity: number;
  available_quantity: number;
  allocated_quantity: number;
  operational_status: string;
  latitude?: number | null;
  longitude?: number | null;
  base_address?: string | null;
  assigned_location_name?: string | null;
  responsible_authority: string;
  capacity_specs?: Record<string, any> | null;
  is_simulated: boolean;
  data_source: string;
  verification_status: string;
  created_at: string;
  updated_at: string;
}

export interface ResourceListResponse {
  total: number;
  limit: number;
  offset: number;
  available_total: number;
  allocated_total: number;
  items: ResourceItem[];
}

export interface ResourceCreateRequest {
  resource_id: string;
  category: string;
  resource_type: string;
  name: string;
  description?: string;
  total_quantity: number;
  available_quantity: number;
  operational_status?: string;
  latitude?: number;
  longitude?: number;
  base_address?: string;
  responsible_authority?: string;
  is_simulated?: boolean;
}

export interface DemandAssessmentItem {
  sector_id: string;
  sector_name: string;
  latitude: number;
  longitude: number;
  priority_level: string;
  priority_score: number;
  risk_score: number;
  demand_score: number;
  accessibility_score: number;
  infrastructure_score: number;
  evidence_type: string;
  required_ambulances: number;
  required_rescue_teams: number;
  required_food_packets: number;
  required_water_liters: number;
  required_medical_kits: number;
  required_blankets: number;
  urgency_reason?: string | null;
  missing_data_notes?: string | null;
  is_simulated: boolean;
  assessed_at: string;
}

export interface DemandAssessmentResponse {
  assessment_timestamp: string;
  total_sectors_assessed: number;
  critical_sectors_count: number;
  high_sectors_count: number;
  total_ambulances_demanded: number;
  total_rescue_teams_demanded: number;
  total_food_packets_demanded: number;
  total_water_liters_demanded: number;
  data_freshness_note: string;
  sectors: DemandAssessmentItem[];
}

export interface PriorityAreaItem {
  rank: number;
  sector_id: string;
  sector_name: string;
  latitude: number;
  longitude: number;
  priority_level: string;
  priority_score: number;
  score_breakdown: Record<string, number>;
  primary_risk_driver: string;
  contributing_indicators: string[];
  missing_data_disclaimer: string;
  recommended_tactical_action: string;
}

export interface PriorityRankingResponse {
  ranked_at: string;
  methodology: string;
  weight_formula: string;
  ranked_areas: PriorityAreaItem[];
}

export interface OptimizationRunRequest {
  objective?: 'MINIMIZE_RESPONSE_TIME' | 'MAXIMIZE_COVERAGE' | 'BALANCED';
  target_sectors?: string[];
  resource_categories?: string[];
  max_travel_time_sec?: number;
  avoid_closed_roads?: boolean;
  enforce_capacity_limits?: boolean;
  additional_closed_edge_ids?: string[];
  only_verified_resources?: boolean;
}

export interface OptimizationAssignmentItem {
  assignment_id: string;
  resource_id: string;
  resource_name: string;
  resource_category: string;
  resource_type: string;
  from_location: string;
  from_coordinates: { lat: number; lon: number };
  target_sector_id: string;
  target_sector_name: string;
  target_coordinates: { lat: number; lon: number };
  assigned_quantity: number;
  estimated_travel_time_sec: number;
  estimated_travel_time_minutes: number;
  estimated_distance_m: number;
  route_is_feasible: boolean;
  route_uncertainty_note?: string | null;
  route_edge_count: number;
  route_geojson?: any;
  is_simulated?: boolean;
  verification_status?: string;
}

export interface UnmetDemandItem {
  sector_id: string;
  sector_name: string;
  resource_type: string;
  demanded_quantity: number;
  allocated_quantity: number;
  shortage_quantity: number;
  reason: string;
}

export interface OptimizationRunResponse {
  run_id: string;
  solver_name: string;
  solver_status: string;
  is_optimal: boolean;
  objective_value?: number | null;
  execution_duration_ms: number;
  resources_considered_count?: number;
  total_assigned_resources: number;
  demand_fulfilled_count?: number;
  total_unmet_demand_count: number;
  verified_resources_assigned?: number;
  simulated_resources_assigned?: number;
  demand_coverage_pct: number;
  resource_utilization_pct?: number;
  total_response_time_minutes: number;
  infeasible_assignments_count?: number;
  assignments: OptimizationAssignmentItem[];
  unmet_demands: UnmetDemandItem[];
  shelter_capacity_note: string;
  constraints_enforced: string[];
  disclaimer: string;
}

export interface ResourceAllocationItem {
  id: number;
  allocation_id: string;
  optimization_run_id?: number | null;
  resource_id: number;
  resource_name: string;
  demand_sector_id: string;
  demand_sector_name: string;
  assigned_quantity: number;
  status: string;
  estimated_travel_time_sec?: number | null;
  estimated_distance_m?: number | null;
  route_uncertainty_note?: string | null;
  allocated_by: string;
  is_simulated?: boolean;
  verification_status?: string;
  approved_by?: string | null;
  approved_at?: string | null;
  created_at: string;
}

export interface ScenarioSimulationRequest {
  scenario_name?: string;
  rainfall_multiplier: number;
  dam_discharge_cfs: number;
  additional_closed_edge_ids?: string[];
  resource_availability_factor: number;
  demand_surge_factor: number;
}

export interface ScenarioDeltaMetric {
  metric_name: string;
  baseline_value: number;
  simulated_value: number;
  absolute_change: number;
  pct_change: number;
  interpretation: string;
}

export interface ScenarioSimulationResponse {
  scenario_id: string;
  scenario_name: string;
  is_simulated: boolean;
  executed_at: string;
  rainfall_multiplier: number;
  dam_discharge_cfs: number;
  dam_submergence_benchmarks_triggered: string[];
  newly_impassable_roads_count: number;
  baseline_demand_total: number;
  simulated_demand_total: number;
  baseline_coverage_pct: number;
  simulated_coverage_pct: number;
  resource_shortage_critical_sectors: string[];
  delta_metrics: ScenarioDeltaMetric[];
  tactical_recommendations: string[];
  isolation_guarantee: string;
}

export interface NugenStatusResponse {
  service_name: string;
  is_available: boolean;
  status: string;
  endpoint_configured: boolean;
  auth_credentials_configured: boolean;
  active_provider: string;
  model_version?: string | null;
  missing_configuration_notes?: string | null;
}

export interface DecisionAdvisoryRequest {
  focus_sector_id?: string;
  include_shortage_analysis?: boolean;
  include_sop_guidelines?: boolean;
}

export interface TacticalActionItem {
  priority_level: string;
  target_sector: string;
  action_type: string;
  description: string;
  assigned_unit_type: string;
  urgency: string;
  regulatory_reference: string;
}

export interface DecisionAdvisoryResponse {
  advisory_id: string;
  generated_at: string;
  intelligence_provider: string;
  is_simulated_advisory: boolean;
  executive_summary: string;
  critical_observations: string[];
  priority_sector_rankings: Array<Record<string, any>>;
  resource_shortage_summary: Record<string, number>;
  tactical_action_plan: TacticalActionItem[];
  route_caution_summary: string[];
  ndma_compliance_notes: string;
  official_disclaimer: string;
}

// Phase 5 Impact Assessment & Task Separation Types

export interface ExposedFacility {
  facility_type: string;
  name: string;
  osm_id?: string | null;
  distance_to_hazard_m: number;
  exposure_tier: string;
  latitude: number;
  longitude: number;
  access_threatened: boolean;
  operational_impact: string;
  exposure_nature?: string;
}

export interface ExposedBridge {
  name: string;
  osm_id?: string | null;
  waterway: string;
  inundation_risk: string;
  submerged: boolean;
  critical_threshold_cfs: number;
  latitude: number;
  longitude: number;
  operational_status: string;
  threshold_classification?: string;
  is_simulated?: boolean;
}

export interface RoadImpactSummary {
  total_road_network_km: number;
  inundated_road_km: number;
  inundated_percentage: number;
  closed_or_blocked_segments_count: number;
  critical_corridors_affected: string[];
  confirmed_closed_segments_count?: number;
  proximity_exposed_segments_count?: number;
  hazard_evaluation_type?: string;
  distinction_disclaimer?: string;
  disclaimer?: string;
}

export interface PopulationExposureSummary {
  data_status: string;
  estimated_exposed_population: number | null;
  lower_bound_estimate: number | null;
  upper_bound_estimate: number | null;
  primary_wards_affected: string[];
  methodology: string;
  estimation_uncertainty_caveat: string;
  missing_data_explanation?: string;
}

export interface HazardMetadata {
  hazard_source: string;
  scene_or_event_name: string;
  verification_status?: string;
  backscatter_threshold_db?: number | null;
  slope_cutoff_deg: number;
  permanent_water_masked: boolean;
  urban_double_bounce_masked: boolean;
  depth_inference_disclaimer: string;
}

export interface ImpactAssessmentResponse {
  assessment_id: string;
  scenario_name: string;
  timestamp_utc: string;
  pilot_region: string;
  hazard_metadata: HazardMetadata;
  population_exposure: PopulationExposureSummary;
  healthcare_impact: ExposedFacility[];
  education_impact: ExposedFacility[];
  bridges_impact: ExposedBridge[];
  road_network_impact: RoadImpactSummary;
  overall_severity: string;
  key_recommendations: string[];
  data_provenance: Record<string, any>;
}

export interface ImpactScenarioComparison {
  scenario_id: string;
  scenario_name: string;
  event_date: string;
  khadakwasla_discharge_cfs: number;
  rainfall_24h_mm: number;
  estimated_exposed_population: number;
  inundated_road_km: number;
  affected_healthcare_count: number;
  affected_bridges_count: number;
  severity_level: string;
  description: string;
}

export interface ImpactScenariosResponse {
  baseline_scenario: ImpactScenarioComparison;
  historical_scenarios: ImpactScenarioComparison[];
  disclaimer: string;
}

export interface ImpactLayersResponse {
  hazard_source: string;
  flood_extent_geojson: Record<string, any>;
  exposed_infrastructure_geojson: Record<string, any>;
  critical_bridges_geojson: Record<string, any>;
  high_risk_roads_geojson: Record<string, any>;
  metadata: Record<string, any>;
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

export interface TaskSeparationItem {
  task_id: string;
  task_name: string;
  purpose: string;
  temporal_frame: string;
  data_sources: string[];
  model_or_engine: string;
  output_type: string;
  validation_status: string;
  operational_readiness: string;
}

export interface TaskSeparationResponse {
  framework_title: string;
  rationale: string;
  tasks: TaskSeparationItem[];
}

// =========================================================================
// PHASE 5.1: AUTHENTICATION, COOKIE SESSIONS & CSRF
// =========================================================================

export interface LoginRequest {
  token: string;
  actor?: string;
}

export interface LoginResponse {
  status: string;
  actor: string;
  role: string;
  csrf_token: string;
  expires_in: number;
  token_type: string;
}

export interface LogoutResponse {
  status: string;
  message: string;
}

export interface SessionInfoResponse {
  authenticated: boolean;
  actor: string;
  role: string;
  token_type: string;
}

export interface CsrfTokenResponse {
  csrf_token: string;
  header_name: string;
  cookie_name: string;
}


