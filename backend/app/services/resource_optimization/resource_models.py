"""Pydantic schemas for FLOOD-X Phase 4 Emergency Resource Optimization & Decision Intelligence."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Emergency Resource Schemas
# ---------------------------------------------------------------------------

class ResourceCreate(BaseModel):
    resource_id: str = Field(..., description="Unique code e.g. AMB-PUNE-01, RESCUE-NDRF-01")
    category: str = Field(..., description="EMERGENCY_VEHICLE, HUMAN_RESOURCE, RELIEF_RESOURCE, INFRASTRUCTURE")
    resource_type: str = Field(..., description="Specific type e.g. AMBULANCE_ALS, RESCUE_BOAT, FOOD_PACKETS")
    name: str = Field(..., description="Display name e.g. 108 Emergency Ambulance #12")
    description: Optional[str] = None
    total_quantity: int = Field(1, ge=1)
    available_quantity: int = Field(1, ge=0)
    operational_status: str = Field("AVAILABLE", description="AVAILABLE, ALLOCATED, DEPLOYED, UNAVAILABLE")
    latitude: Optional[float] = Field(None, ge=18.0, le=19.0)
    longitude: Optional[float] = Field(None, ge=73.0, le=75.0)
    base_address: Optional[str] = None
    assigned_location_name: Optional[str] = None
    responsible_authority: str = Field("PMC Disaster Management Cell")
    capacity_specs: Optional[Dict[str, Any]] = None
    is_simulated: bool = Field(True, description="Always true for unverified demo/drill resources")
    verification_status: Optional[str] = Field(None, description="VERIFIED, UNVERIFIED, SIMULATED, UNAVAILABLE")
    data_source: Optional[str] = Field(None, description="Source provenance of asset record")


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    total_quantity: Optional[int] = Field(None, ge=0)
    available_quantity: Optional[int] = Field(None, ge=0)
    allocated_quantity: Optional[int] = Field(None, ge=0)
    operational_status: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    base_address: Optional[str] = None
    assigned_location_name: Optional[str] = None
    responsible_authority: Optional[str] = None
    capacity_specs: Optional[Dict[str, Any]] = None
    verification_status: Optional[str] = None
    data_source: Optional[str] = None
    is_simulated: Optional[bool] = None


class ResourceQuantityUpdate(BaseModel):
    available_quantity: int = Field(..., ge=0)
    operational_status: Optional[str] = None
    notes: Optional[str] = None


class ResourceItem(BaseModel):
    id: int
    resource_id: str
    category: str
    resource_type: str
    name: str
    description: Optional[str] = None
    total_quantity: int
    available_quantity: int
    allocated_quantity: int
    operational_status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    base_address: Optional[str] = None
    assigned_location_name: Optional[str] = None
    responsible_authority: str
    capacity_specs: Optional[Dict[str, Any]] = None
    is_simulated: bool
    data_source: str
    verification_status: str
    created_at: datetime
    updated_at: datetime


class ResourceListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    available_total: int
    allocated_total: int
    items: List[ResourceItem]


# ---------------------------------------------------------------------------
# 2. Demand Estimation & Response Prioritization Schemas
# ---------------------------------------------------------------------------

class DemandAssessmentItem(BaseModel):
    sector_id: str
    sector_name: str
    latitude: float
    longitude: float
    priority_level: str
    priority_score: float
    risk_score: float
    demand_score: float
    accessibility_score: float
    infrastructure_score: float
    evidence_type: str
    required_ambulances: int
    required_rescue_teams: int
    required_food_packets: int
    required_water_liters: int
    required_medical_kits: int
    required_blankets: int
    urgency_reason: Optional[str] = None
    missing_data_notes: Optional[str] = None
    is_simulated: bool
    assessed_at: datetime


class DemandAssessmentResponse(BaseModel):
    assessment_timestamp: datetime
    total_sectors_assessed: int
    critical_sectors_count: int
    high_sectors_count: int
    total_ambulances_demanded: int
    total_rescue_teams_demanded: int
    total_food_packets_demanded: int
    total_water_liters_demanded: int
    data_freshness_note: str
    sectors: List[DemandAssessmentItem]


class PriorityAreaItem(BaseModel):
    rank: int
    sector_id: str
    sector_name: str
    latitude: float
    longitude: float
    priority_level: str
    priority_score: float
    score_breakdown: Dict[str, float]
    primary_risk_driver: str
    contributing_indicators: List[str]
    missing_data_disclaimer: str
    recommended_tactical_action: str


class PriorityRankingResponse(BaseModel):
    ranked_at: datetime
    methodology: str
    weight_formula: str
    ranked_areas: List[PriorityAreaItem]


# ---------------------------------------------------------------------------
# 3. Google OR-Tools Constrained Optimization Schemas
# ---------------------------------------------------------------------------

class OptimizationRunRequest(BaseModel):
    objective: str = Field("MINIMIZE_RESPONSE_TIME", description="MINIMIZE_RESPONSE_TIME, MAXIMIZE_COVERAGE, BALANCED")
    target_sectors: Optional[List[str]] = Field(None, description="Optional list of sector IDs to optimize for (default all)")
    resource_categories: Optional[List[str]] = Field(None, description="Optional list of categories to include")
    max_travel_time_sec: float = Field(3600.0, description="Max acceptable travel time per dispatch (default 60 mins)")
    avoid_closed_roads: bool = Field(True, description="Strictly exclude confirmed blocked roads")
    enforce_capacity_limits: bool = Field(True, description="Ensure resources do not exceed available quantities")
    additional_closed_edge_ids: Optional[List[str]] = Field(None, description="Optional simulated extra road closures")
    only_verified_resources: bool = Field(False, description="Strictly restrict dispatch to verified non-simulated inventory")


class OptimizationAssignmentItem(BaseModel):
    assignment_id: str
    resource_id: str
    resource_name: str
    resource_category: str
    resource_type: str
    from_location: str
    from_coordinates: Dict[str, float]
    target_sector_id: str
    target_sector_name: str
    target_coordinates: Dict[str, float]
    assigned_quantity: int
    estimated_travel_time_sec: float
    estimated_travel_time_minutes: float
    estimated_distance_m: float
    route_is_feasible: bool
    route_uncertainty_note: Optional[str] = None
    route_edge_count: int
    route_geojson: Optional[Dict[str, Any]] = None
    is_simulated: bool = Field(True, description="Whether assigned asset is simulated")
    verification_status: str = Field("SIMULATED", description="VERIFIED, UNVERIFIED, SIMULATED")


class UnmetDemandItem(BaseModel):
    sector_id: str
    sector_name: str
    resource_type: str
    demanded_quantity: int
    allocated_quantity: int
    shortage_quantity: int
    reason: str


class OptimizationRunResponse(BaseModel):
    run_id: str
    solver_name: str
    solver_status: str
    is_optimal: bool
    objective_value: Optional[float] = None
    execution_duration_ms: float
    resources_considered_count: int = 0
    total_assigned_resources: int
    demand_fulfilled_count: int = 0
    total_unmet_demand_count: int
    verified_resources_assigned: int = 0
    simulated_resources_assigned: int = 0
    demand_coverage_pct: float
    resource_utilization_pct: float = 0.0
    total_response_time_minutes: float
    infeasible_assignments_count: int = 0
    assignments: List[OptimizationAssignmentItem]
    unmet_demands: List[UnmetDemandItem]
    shelter_capacity_note: str
    constraints_enforced: List[str]
    disclaimer: str


# ---------------------------------------------------------------------------
# 4. Resource Allocation & Deployment Schemas
# ---------------------------------------------------------------------------

class ResourceAllocateRequest(BaseModel):
    resource_id: int
    demand_sector_id: str
    assigned_quantity: int = Field(1, ge=1)
    notes: Optional[str] = None


class ResourceAllocationItem(BaseModel):
    id: int
    allocation_id: str
    optimization_run_id: Optional[int] = None
    resource_id: int
    resource_name: str
    demand_sector_id: str
    demand_sector_name: str
    assigned_quantity: int
    status: str
    estimated_travel_time_sec: Optional[float] = None
    estimated_distance_m: Optional[float] = None
    route_uncertainty_note: Optional[str] = None
    allocated_by: str
    is_simulated: bool = True
    verification_status: str = "SIMULATED"
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime


class AllocationApprovalRequest(BaseModel):
    allocation_ids: List[int] = Field(..., description="List of allocation DB IDs to approve")
    officer_name: Optional[str] = Field("Command Duty Officer")


# ---------------------------------------------------------------------------
# 5. What-If Scenario Simulation Schemas
# ---------------------------------------------------------------------------

class ScenarioSimulationRequest(BaseModel):
    scenario_name: str = Field("Drill Scenario", description="Label for simulation run")
    rainfall_multiplier: float = Field(1.0, ge=0.5, le=5.0, description="Precipitation surge multiplier")
    dam_discharge_cfs: float = Field(0.0, ge=0.0, le=100000.0, description="Simulated Khadakwasla Dam release in cfs")
    additional_closed_edge_ids: Optional[List[str]] = Field(None, description="Edge IDs to simulate as closed")
    resource_availability_factor: float = Field(1.0, ge=0.1, le=1.0, description="Available fleet ratio (e.g. 0.7 = 30% offline)")
    demand_surge_factor: float = Field(1.0, ge=0.5, le=4.0, description="Emergency demand escalation factor")


class ScenarioDeltaMetric(BaseModel):
    metric_name: str
    baseline_value: float
    simulated_value: float
    absolute_change: float
    pct_change: float
    interpretation: str


class ScenarioSimulationResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    is_simulated: bool = True
    executed_at: datetime
    rainfall_multiplier: float
    dam_discharge_cfs: float
    dam_submergence_benchmarks_triggered: List[str]
    newly_impassable_roads_count: int
    baseline_demand_total: int
    simulated_demand_total: int
    baseline_coverage_pct: float
    simulated_coverage_pct: float
    resource_shortage_critical_sectors: List[str]
    delta_metrics: List[ScenarioDeltaMetric]
    tactical_recommendations: List[str]
    isolation_guarantee: str = (
        "CONFIRMED: This scenario simulation operated strictly in-memory. "
        "No database records, confirmed road closures, or real resource quantities were altered."
    )


# ---------------------------------------------------------------------------
# 6. Nugen Decision Intelligence & Advisory Schemas
# ---------------------------------------------------------------------------

class NugenStatusResponse(BaseModel):
    service_name: str = "Nugen Decision Intelligence"
    is_available: bool
    status: str
    endpoint_configured: bool
    auth_credentials_configured: bool
    active_provider: str  # "NUGEN_API_LIVE" or "RULE_BASED_DECISION_FALLBACK"
    model_version: Optional[str] = None
    missing_configuration_notes: Optional[str] = None


class DecisionAdvisoryRequest(BaseModel):
    focus_sector_id: Optional[str] = None
    include_shortage_analysis: bool = True
    include_sop_guidelines: bool = True


class TacticalActionItem(BaseModel):
    priority_level: str
    target_sector: str
    action_type: str
    description: str
    assigned_unit_type: str
    urgency: str
    regulatory_reference: str  # e.g., "NDMA Flood SOP Section 4.2"


class DecisionAdvisoryResponse(BaseModel):
    advisory_id: str
    generated_at: datetime
    intelligence_provider: str
    is_simulated_advisory: bool
    executive_summary: str
    critical_observations: List[str]
    priority_sector_rankings: List[Dict[str, Any]]
    resource_shortage_summary: Dict[str, int]
    tactical_action_plan: List[TacticalActionItem]
    route_caution_summary: List[str]
    ndma_compliance_notes: str
    official_disclaimer: str

