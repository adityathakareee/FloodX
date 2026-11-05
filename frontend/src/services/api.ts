/**
 * Centralized API Service for FLOOD-X Authority Dashboard.
 * Interacts with backend FastAPI v1 endpoints with failover handling.
 */

import {
  HealthResponse,
  SystemInfoResponse,
  IngestionOverview,
  DataSourceItem,
  IngestionLogItem,
  RainfallObservationItem,
  RainfallSummary,
  WeatherObservationItem,
  RiverLevelObservationItem,
  SpatialFeatureItem,
  GISSummary,
  DataQualitySummary,
  DataQualityIssueItem,
  PaginatedResult,
  FeatureDatasetItem,
  FeatureSummary,
  IntegratedSampleRecord,
  MLStatusResponse,
  MLModelMetadata,
  MLEvaluationResponse,
  MLPredictionRequest,
  MLPredictionResponse,
  MLExplainabilityResponse,
  SpatialSusceptibilityResponse,
  ProspectiveStatusResponse,
  ProspectiveForecastResponse,
  ProspectiveSourcesResponse,
  ProspectiveAssessmentResponse,
  ScenarioAssessmentRequest,
  ScenarioAssessmentResponse,
  NetworkStatusResponse,
  NetworkStatisticsResponse,
  RoadsPaginatedResponse,
  NodesPaginatedResponse,
  RebuildResponse,
  EvacuationStatusResponse,
  EvacuationStatisticsResponse,
  RoadExposureItem,
  RoadSafetyItem,
  InfrastructureSafetyItem,
  RoadClosureItem,
  RoadClosureCreate,
  ShelterItem,
  ShelterCreate,
  RouteRequest,
  RoutePlanResponse,
  ShelterRecommendationResponse,
  ResourceItem,
  ResourceListResponse,
  ResourceCreateRequest,
  DemandAssessmentResponse,
  PriorityRankingResponse,
  OptimizationRunRequest,
  OptimizationRunResponse,
  ResourceAllocationItem,
  ScenarioSimulationRequest,
  ScenarioSimulationResponse,
  NugenStatusResponse,
  DecisionAdvisoryRequest,
  DecisionAdvisoryResponse,
  ImpactAssessmentResponse,
  ImpactScenariosResponse,
  ImpactLayersResponse,
  CurrentConditionResponse,
  TaskSeparationResponse,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  SessionInfoResponse,
  CsrfTokenResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'));
  return match ? decodeURIComponent(match[3]) : null;
}

class ApiService {
  private baseUrl: string;
  private authorityToken: string | null = null;
  private csrfToken: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  public setAuthorityToken(token: string | null): void {
    // Strictly in-memory token storage (mitigates persistent XSS credential exfiltration)
    this.authorityToken = token ? token.trim() : null;
  }

  public getAuthorityToken(): string | null {
    return this.authorityToken;
  }

  public hasAuthorityToken(): boolean {
    return Boolean(this.authorityToken);
  }

  public clearAuthorityToken(): void {
    this.authorityToken = null;
  }

  public setCsrfToken(token: string | null): void {
    this.csrfToken = token ? token.trim() : null;
  }

  public getCsrfTokenValue(): string | null {
    return this.csrfToken || getCookie('floodx_csrf_token');
  }

  private async fetchJson<T>(endpoint: string, options?: RequestInit, timeoutMs = 6000): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    const method = (options?.method || 'GET').toUpperCase();
    const headers: Record<string, string> = {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(options?.headers as Record<string, string> || {}),
    };

    if (this.authorityToken && !headers['X-Authority-Token']) {
      headers['X-Authority-Token'] = this.authorityToken;
    }

    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const csrf = this.csrfToken || getCookie('floodx_csrf_token');
      if (csrf && !headers['X-CSRF-Token']) {
        headers['X-CSRF-Token'] = csrf;
      }
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        credentials: options?.credentials || 'same-origin',
        signal: controller.signal,
        headers,
      });

      if (!response.ok) {
        throw new Error(`Request to ${endpoint} returned HTTP ${response.status}`);
      }

      return (await response.json()) as T;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Fetches real-time system health and database ping.
   */
  async getHealth(): Promise<HealthResponse> {
    return this.fetchJson<HealthResponse>('/health');
  }

  /**
   * Fetches complete system info, pilot region data, and module status catalogue.
   */
  async getSystemInfo(): Promise<SystemInfoResponse> {
    return this.fetchJson<SystemInfoResponse>('/system/info');
  }

  // ==========================================
  // Ingestion & Pipeline Services
  // ==========================================

  async getIngestionOverview(): Promise<IngestionOverview> {
    return this.fetchJson<IngestionOverview>('/ingestion/overview');
  }

  async getDataSources(): Promise<DataSourceItem[]> {
    return this.fetchJson<DataSourceItem[]>('/ingestion/sources');
  }

  async getIngestionLogs(limit = 15): Promise<IngestionLogItem[]> {
    return this.fetchJson<IngestionLogItem[]>(`/ingestion/logs?limit=${limit}`);
  }

  async triggerIngestion(source = 'all', fastMode = false): Promise<any> {
    return this.fetchJson<any>('/ingestion/run', {
      method: 'POST',
      body: JSON.stringify({ source, fast_mode: fastMode }),
    }, 60000); // Allow up to 60s for ingestion trigger
  }

  // ==========================================
  // Environmental Observation Services
  // ==========================================

  async getRainfallObservations(params?: {
    measurement_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResult<RainfallObservationItem>> {
    const query = new URLSearchParams();
    if (params?.measurement_type) query.append('measurement_type', params.measurement_type);
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.offset) query.append('offset', params.offset.toString());
    return this.fetchJson<PaginatedResult<RainfallObservationItem>>(`/environment/rainfall?${query.toString()}`);
  }

  async getRainfallSummary(): Promise<RainfallSummary> {
    return this.fetchJson<RainfallSummary>('/environment/rainfall/summary');
  }

  async getWeatherObservations(params?: {
    data_category?: string;
    limit?: number;
  }): Promise<PaginatedResult<WeatherObservationItem>> {
    const query = new URLSearchParams();
    if (params?.data_category) query.append('data_category', params.data_category);
    if (params?.limit) query.append('limit', (params.limit || 20).toString());
    return this.fetchJson<PaginatedResult<WeatherObservationItem>>(`/environment/weather?${query.toString()}`);
  }

  async getRiverLevelObservations(params?: {
    limit?: number;
  }): Promise<PaginatedResult<RiverLevelObservationItem>> {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', (params.limit || 20).toString());
    return this.fetchJson<PaginatedResult<RiverLevelObservationItem>>(`/environment/river-levels?${query.toString()}`);
  }

  // ==========================================
  // GIS & Spatial Infrastructure Services
  // ==========================================

  async getGISSummary(): Promise<GISSummary> {
    return this.fetchJson<GISSummary>('/gis/summary');
  }

  async getGISFeatures(params?: {
    feature_type?: string;
    limit?: number;
  }): Promise<PaginatedResult<SpatialFeatureItem>> {
    const query = new URLSearchParams();
    if (params?.feature_type) query.append('feature_type', params.feature_type);
    if (params?.limit) query.append('limit', (params.limit || 25).toString());
    return this.fetchJson<PaginatedResult<SpatialFeatureItem>>(`/gis/features?${query.toString()}`);
  }

  // ==========================================
  // Data Quality & Audit Services
  // ==========================================

  async getDataQualitySummary(): Promise<DataQualitySummary> {
    return this.fetchJson<DataQualitySummary>('/data-quality/summary');
  }

  async getDataQualityIssues(severity?: string): Promise<DataQualityIssueItem[]> {
    const query = severity ? `?severity=${severity}` : '';
    return this.fetchJson<DataQualityIssueItem[]>(`/data-quality/issues${query}`);
  }

  // ==========================================
  // Hydrological Features & Intelligence
  // ==========================================

  async getFeaturesSummary(): Promise<FeatureSummary> {
    return this.fetchJson<FeatureSummary>('/features/summary');
  }

  async getFeatureDatasets(category?: string): Promise<FeatureDatasetItem[]> {
    const query = category ? `?category=${category}` : '';
    return this.fetchJson<FeatureDatasetItem[]>(`/features/datasets${query}`);
  }

  async getFeatureDatasetByName(name: string): Promise<FeatureDatasetItem> {
    return this.fetchJson<FeatureDatasetItem>(`/features/datasets/${encodeURIComponent(name)}`);
  }

  async getIntegratedFeaturesSample(limit = 24, offset = 0): Promise<{
    total_records: number;
    temporal_range: string;
    local_river_gauge_status: string;
    records: IntegratedSampleRecord[];
  }> {
    return this.fetchJson<{
      total_records: number;
      temporal_range: string;
      local_river_gauge_status: string;
      records: IntegratedSampleRecord[];
    }>(`/features/integrated/sample?limit=${limit}&offset=${offset}`);
  }

  // ==================== PHASE 2.2: ML FLOOD INTELLIGENCE ====================

  async getMLStatus(): Promise<MLStatusResponse> {
    return this.fetchJson<MLStatusResponse>('/ml/status');
  }

  async getMLModels(): Promise<MLModelMetadata[]> {
    return this.fetchJson<MLModelMetadata[]>('/ml/models');
  }

  async getMLEvaluation(): Promise<MLEvaluationResponse> {
    return this.fetchJson<MLEvaluationResponse>('/ml/evaluation');
  }

  async predictFloodRisk(req: MLPredictionRequest): Promise<MLPredictionResponse> {
    return this.fetchJson<MLPredictionResponse>('/ml/predict', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  async getMLExplainability(): Promise<MLExplainabilityResponse> {
    return this.fetchJson<MLExplainabilityResponse>('/ml/explainability');
  }

  async getSpatialSusceptibility(): Promise<SpatialSusceptibilityResponse> {
    return this.fetchJson<SpatialSusceptibilityResponse>('/ml/spatial-susceptibility');
  }

  // ==================== PHASE 2.3: PROSPECTIVE RISK INTELLIGENCE ====================

  async getProspectiveStatus(): Promise<ProspectiveStatusResponse> {
    return this.fetchJson<ProspectiveStatusResponse>('/prospective/status');
  }

  async getProspectiveForecast(horizon_hours: number = 48): Promise<ProspectiveForecastResponse> {
    return this.fetchJson<ProspectiveForecastResponse>(`/prospective/forecast?horizon_hours=${horizon_hours}`);
  }

  async getProspectiveSources(): Promise<ProspectiveSourcesResponse> {
    return this.fetchJson<ProspectiveSourcesResponse>('/prospective/sources');
  }

  async getDamBenchmarks(): Promise<Record<string, any>> {
    return this.fetchJson<Record<string, any>>('/prospective/benchmarks');
  }

  async assessProspectiveRisk(simulated_dam_discharge_cfs?: number): Promise<ProspectiveAssessmentResponse> {
    const query = simulated_dam_discharge_cfs !== undefined ? `?simulated_dam_discharge_cfs=${simulated_dam_discharge_cfs}` : '';
    return this.fetchJson<ProspectiveAssessmentResponse>(`/prospective/assess${query}`, {
      method: 'POST',
    });
  }

  async assessWhatIfScenario(req: ScenarioAssessmentRequest): Promise<ScenarioAssessmentResponse> {
    return this.fetchJson<ScenarioAssessmentResponse>('/prospective/scenario', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  // ==================== PHASE 3.1: ROAD NETWORK & GIS GRAPH ====================

  async getRoutingStatus(): Promise<NetworkStatusResponse> {
    return this.fetchJson<NetworkStatusResponse>('/routing/network/status');
  }

  async getRoutingStatistics(): Promise<NetworkStatisticsResponse> {
    return this.fetchJson<NetworkStatisticsResponse>('/routing/network/statistics');
  }

  async getRoutingRoads(params?: {
    limit?: number;
    offset?: number;
    highway?: string;
    min_lat?: number;
    max_lat?: number;
    min_lon?: number;
    max_lon?: number;
  }): Promise<RoadsPaginatedResponse> {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    if (params?.highway) query.set('highway', params.highway);
    if (params?.min_lat) query.set('min_lat', String(params.min_lat));
    if (params?.max_lat) query.set('max_lat', String(params.max_lat));
    if (params?.min_lon) query.set('min_lon', String(params.min_lon));
    if (params?.max_lon) query.set('max_lon', String(params.max_lon));

    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.fetchJson<RoadsPaginatedResponse>(`/routing/network/roads${qs}`);
  }

  async getRoutingNodes(params?: {
    limit?: number;
    offset?: number;
    min_lat?: number;
    max_lat?: number;
    min_lon?: number;
    max_lon?: number;
  }): Promise<NodesPaginatedResponse> {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    if (params?.min_lat) query.set('min_lat', String(params.min_lat));
    if (params?.max_lat) query.set('max_lat', String(params.max_lat));
    if (params?.min_lon) query.set('min_lon', String(params.min_lon));
    if (params?.max_lon) query.set('max_lon', String(params.max_lon));

    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.fetchJson<NodesPaginatedResponse>(`/routing/network/nodes${qs}`);
  }

  async rebuildRoutingGraph(token: string): Promise<RebuildResponse> {
    return this.fetchJson<RebuildResponse>('/routing/network/rebuild', {
      method: 'POST',
      headers: {
        'X-Routing-Token': token,
      },
    });
  }

  // --------------------------------------------------------------------------
  // Phase 3.2: Evacuation Intelligence APIs
  // --------------------------------------------------------------------------

  async getEvacuationStatus(): Promise<EvacuationStatusResponse> {
    return this.fetchJson<EvacuationStatusResponse>('/evacuation/status');
  }

  async getEvacuationStatistics(): Promise<EvacuationStatisticsResponse> {
    return this.fetchJson<EvacuationStatisticsResponse>('/evacuation/statistics');
  }

  async getRoadExposures(tier?: string, limit: number = 100, offset: number = 0): Promise<{ total: number; limit: number; offset: number; items: RoadExposureItem[] }> {
    const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (tier) qs.set('tier', tier);
    return this.fetchJson(`/evacuation/roads/exposure?${qs.toString()}`);
  }

  async getRoadEdgeSafety(edgeId: string): Promise<RoadSafetyItem> {
    return this.fetchJson<RoadSafetyItem>(`/evacuation/roads/${edgeId}/safety`);
  }

  async getEvacuationInfrastructure(dischargeCfs?: number): Promise<InfrastructureSafetyItem[]> {
    const qs = dischargeCfs !== undefined ? `?discharge_cfs=${dischargeCfs}` : '';
    return this.fetchJson<InfrastructureSafetyItem[]>(`/evacuation/infrastructure${qs}`);
  }

  async getEvacuationClosures(activeOnly: boolean = true): Promise<RoadClosureItem[]> {
    return this.fetchJson<RoadClosureItem[]>(`/evacuation/closures?active_only=${activeOnly}`);
  }

  async createRoadClosure(payload: RoadClosureCreate): Promise<RoadClosureItem> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const token = this.getAuthorityToken();
    if (token) {
      headers['X-Authority-Token'] = token;
    }
    return this.fetchJson<RoadClosureItem>('/evacuation/closures', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
  }

  async deleteRoadClosure(closureId: number, clearedBy: string = 'Authority Officer'): Promise<{ status: string }> {
    const headers: Record<string, string> = {};
    const token = this.getAuthorityToken();
    if (token) {
      headers['X-Authority-Token'] = token;
    }
    return this.fetchJson(`/evacuation/closures/${closureId}?cleared_by=${encodeURIComponent(clearedBy)}`, {
      method: 'DELETE',
      headers,
    });
  }

  async planEvacuationRoute(request: RouteRequest): Promise<RoutePlanResponse> {
    return this.fetchJson<RoutePlanResponse>('/evacuation/routes/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
  }

  async getShelters(params?: {
    status?: string;
    hasMedical?: boolean;
    isWheelchairAccessible?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<{ total: number; limit: number; offset: number; items: ShelterItem[] }> {
    const qs = new URLSearchParams();
    if (params?.status) qs.set('status', params.status);
    if (params?.hasMedical !== undefined) qs.set('has_medical', String(params.hasMedical));
    if (params?.isWheelchairAccessible !== undefined) qs.set('is_wheelchair_accessible', String(params.isWheelchairAccessible));
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.offset) qs.set('offset', String(params.offset));
    return this.fetchJson(`/evacuation/shelters?${qs.toString()}`);
  }

  async getShelterRecommendations(
    originLat: number,
    originLon: number,
    costProfile: string = 'BALANCED',
    needMedical?: boolean,
    needWheelchair?: boolean,
    maxResults: number = 5
  ): Promise<ShelterRecommendationResponse> {
    const qs = new URLSearchParams({
      origin_lat: String(originLat),
      origin_lon: String(originLon),
      cost_profile: costProfile,
      max_results: String(maxResults),
    });
    if (needMedical !== undefined) qs.set('need_medical', String(needMedical));
    if (needWheelchair !== undefined) qs.set('need_wheelchair', String(needWheelchair));
    return this.fetchJson<ShelterRecommendationResponse>(`/evacuation/shelters/recommendations?${qs.toString()}`);
  }

  async createShelter(payload: ShelterCreate): Promise<ShelterItem> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const token = this.getAuthorityToken();
    if (token) {
      headers['X-Authority-Token'] = token;
    }
    return this.fetchJson<ShelterItem>('/evacuation/shelters', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
  }

  // ==========================================================================
  // Phase 4: Emergency Resource Optimization & Decision Intelligence
  // ==========================================================================

  async listResources(category?: string, operationalStatus?: string, limit: number = 100, offset: number = 0): Promise<ResourceListResponse> {
    const qs = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (category) qs.set('category', category);
    if (operationalStatus) qs.set('operational_status', operationalStatus);
    return this.fetchJson<ResourceListResponse>(`/resources?${qs.toString()}`);
  }

  async createResource(payload: ResourceCreateRequest): Promise<ResourceItem> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    const token = this.getAuthorityToken();
    if (token) headers['X-Authority-Token'] = token;
    return this.fetchJson<ResourceItem>('/resources', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
  }

  async updateResourceQuantity(resourceId: number, availableQuantity: number, notes?: string): Promise<ResourceItem> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    const token = this.getAuthorityToken();
    if (token) headers['X-Authority-Token'] = token;
    return this.fetchJson<ResourceItem>(`/resources/${resourceId}/quantity`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ available_quantity: availableQuantity, notes }),
    });
  }

  async deleteResource(resourceId: number): Promise<{ message: string; deleted: boolean }> {
    const headers: Record<string, string> = {};
    const token = this.getAuthorityToken();
    if (token) headers['X-Authority-Token'] = token;
    return this.fetchJson<{ message: string; deleted: boolean }>(`/resources/${resourceId}`, {
      method: 'DELETE',
      headers,
    });
  }

  async seedDemoResources(force: boolean = false): Promise<{ message: string; count: number }> {
    const headers: Record<string, string> = {};
    const token = this.getAuthorityToken();
    if (token) headers['X-Authority-Token'] = token;
    return this.fetchJson<{ message: string; count: number }>(`/resources/seed-demo?force=${force}`, {
      method: 'POST',
      headers,
    });
  }

  async listAllocations(status?: string, sectorId?: string, limit: number = 50): Promise<ResourceAllocationItem[]> {
    const qs = new URLSearchParams({ limit: String(limit) });
    if (status) qs.set('status', status);
    if (sectorId) qs.set('sector_id', sectorId);
    return this.fetchJson<ResourceAllocationItem[]>(`/resources/allocations?${qs.toString()}`);
  }

  async approveAllocations(allocationIds: number[]): Promise<ResourceAllocationItem[]> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    const token = this.getAuthorityToken();
    if (token) headers['X-Authority-Token'] = token;
    return this.fetchJson<ResourceAllocationItem[]>('/resources/allocations/approve', {
      method: 'POST',
      headers,
      body: JSON.stringify({ allocation_ids: allocationIds }),
    });
  }

  async releaseAllocation(allocationId: number, notes?: string): Promise<ResourceAllocationItem> {
    const headers: Record<string, string> = {};
    const token = this.getAuthorityToken();
    if (token) headers['X-Authority-Token'] = token;
    const qs = notes ? `?notes=${encodeURIComponent(notes)}` : '';
    return this.fetchJson<ResourceAllocationItem>(`/resources/allocations/${allocationId}/release${qs}`, {
      method: 'POST',
      headers,
    });
  }

  async getDemandAssessments(rainfallMultiplier: number = 1.0, damDischargeCfs: number = 0.0): Promise<DemandAssessmentResponse> {
    const qs = new URLSearchParams({
      rainfall_multiplier: String(rainfallMultiplier),
      dam_discharge_cfs: String(damDischargeCfs),
    });
    return this.fetchJson<DemandAssessmentResponse>(`/demand/assessments?${qs.toString()}`);
  }

  async getPriorityRankings(): Promise<PriorityRankingResponse> {
    return this.fetchJson<PriorityRankingResponse>('/decision/priorities');
  }

  async executeOptimization(payload: OptimizationRunRequest): Promise<OptimizationRunResponse> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    const token = this.getAuthorityToken();
    if (token) headers['X-Authority-Token'] = token;
    return this.fetchJson<OptimizationRunResponse>('/optimization/run', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
  }

  async listOptimizationRuns(limit: number = 20): Promise<any[]> {
    return this.fetchJson<any[]>(`/optimization/runs?limit=${limit}`);
  }

  async simulateScenario(payload: ScenarioSimulationRequest): Promise<ScenarioSimulationResponse> {
    return this.fetchJson<ScenarioSimulationResponse>('/scenarios/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }

  async getNugenStatus(): Promise<NugenStatusResponse> {
    return this.fetchJson<NugenStatusResponse>('/nugen/status');
  }

  async generateDecisionAdvisory(payload: DecisionAdvisoryRequest = {}): Promise<DecisionAdvisoryResponse> {
    return this.fetchJson<DecisionAdvisoryResponse>('/nugen/advisory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }

  // Phase 5 Multi-Sector Impact Assessment APIs
  async getImpactLatest(hazardSource: string = 'OBSERVED_SAR_EXTENT'): Promise<ImpactAssessmentResponse> {
    return this.fetchJson<ImpactAssessmentResponse>(`/impact/latest?hazard_source=${hazardSource}`);
  }

  async assessImpactScenario(payload: {
    hazard_source?: string;
    simulated_discharge_cfs?: number;
    rain_rate_mmh?: number;
    scenario_name?: string;
  }): Promise<ImpactAssessmentResponse> {
    return this.fetchJson<ImpactAssessmentResponse>('/impact/assess', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }

  async getImpactScenarios(): Promise<ImpactScenariosResponse> {
    return this.fetchJson<ImpactScenariosResponse>('/impact/scenarios');
  }

  async getImpactLayers(hazardSource: string = 'OBSERVED_SAR_EXTENT'): Promise<ImpactLayersResponse> {
    return this.fetchJson<ImpactLayersResponse>(`/impact/layers?hazard_source=${hazardSource}`);
  }

  // Phase 5 Task B Current Conditions & Task Separation APIs
  async getCurrentConditions(): Promise<CurrentConditionResponse> {
    return this.fetchJson<CurrentConditionResponse>('/ml/current-conditions');
  }

  async getTaskSeparation(): Promise<TaskSeparationResponse> {
    return this.fetchJson<TaskSeparationResponse>('/ml/task-separation');
  }

  async getEventValidationReport(): Promise<any> {
    return this.fetchJson<any>('/ml/event-validation');
  }

  // Phase 5.1: Authority Authentication & Sessions
  async login(payload: LoginRequest): Promise<LoginResponse> {
    const res = await this.fetchJson<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (res.csrf_token) {
      this.csrfToken = res.csrf_token;
    }
    return res;
  }

  async logout(): Promise<LogoutResponse> {
    const res = await this.fetchJson<LogoutResponse>('/auth/logout', {
      method: 'POST',
    });
    this.csrfToken = null;
    this.authorityToken = null;
    return res;
  }

  async getSession(): Promise<SessionInfoResponse> {
    return this.fetchJson<SessionInfoResponse>('/auth/session');
  }

  async getCsrfToken(): Promise<CsrfTokenResponse> {
    const res = await this.fetchJson<CsrfTokenResponse>('/auth/csrf-token');
    if (res.csrf_token) {
      this.csrfToken = res.csrf_token;
    }
    return res;
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }
}

export const apiService = new ApiService(API_BASE_URL);
