"""Pydantic schemas and data models for FLOOD-X Phase 3.2 Evacuation Intelligence."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class RoadExposureItem(BaseModel):
    """Represents flood hazard exposure metrics for a single directed road graph edge."""
    edge_id: str
    source_node: int
    destination_node: int
    road_name: str
    highway: str
    length_m: float
    min_elevation_m: float
    mean_elevation_m: float
    relative_elevation_m: float
    waterway_distance_m: float
    local_slope_deg: float
    exposure_tier: str = Field(..., description="LOW_EXPOSURE, MODERATE_EXPOSURE, HIGH_EXPOSURE, CRITICAL_EXPOSURE, UNKNOWN_EXPOSURE")
    exposure_reason: str
    is_chronic_hotspot: bool = False
    evidence_type: str = "TERRAIN_SUSCEPTIBILITY"
    relative_exposure_classification: str = "LOW_RELATIVE_EXPOSURE"
    evidence_provenance: str
    assessment_timestamp_utc: str


class RoadSafetyItem(BaseModel):
    """Operational safety assessment combining exposure, infrastructure status, and closures."""
    edge_id: str
    road_name: str
    highway: str
    exposure_tier: str
    operational_status: str = Field(..., description="SAFE, CAUTION, HAZARDOUS, IMPASSABLE")
    relative_exposure_classification: str = Field(..., description="LOW_RELATIVE_EXPOSURE, MODERATE_RELATIVE_EXPOSURE, HIGH_RELATIVE_EXPOSURE, CONFIRMED_BLOCKED, UNKNOWN_STATUS")
    evidence_type: str = "TERRAIN_SUSCEPTIBILITY"
    is_blocked: bool
    closure_reason: Optional[str] = None
    closure_authority: Optional[str] = None
    directionality_status: str
    is_direction_assumed: bool
    is_bridge: bool
    is_tunnel: bool
    dynamic_travel_penalty_sec: float
    safety_summary: str


class InfrastructureSafetyItem(BaseModel):
    """Bridge, causeway, or underpass structural safety assessment."""
    id: str
    name: str
    infrastructure_type: str = Field(..., description="BRIDGE, LOW_CAUSEWAY, UNDERPASS, FLYOVER")
    latitude: float
    longitude: float
    osm_id: Optional[int | str] = None
    waterway_proximity_m: float
    terrain_elevation_m: float
    status: str = Field(..., description="NORMAL, POTENTIALLY_EXPOSED, REQUIRES_VERIFICATION, CONFIRMED_BLOCKED, DATA_INSUFFICIENT, SIMULATED_BLOCKAGE")
    status_reason: str
    submergence_reference_cfs: Optional[float] = None
    unverified_operational_reference_cfs: Optional[float] = None
    is_closed: bool = False
    is_submerged_simulated: bool = False
    is_unverified_reference: bool = True
    scenario_type: Optional[str] = "BASELINE"
    provenance_note: Optional[str] = None
    connected_edge_ids: List[str] = Field(default_factory=list)
    last_assessment_utc: str


class RoadClosureItem(BaseModel):
    """Record of a verified or simulated road closure / barricade."""
    id: int
    edge_id: str
    road_name: str
    closure_status: str
    reason: str
    verification_source: str
    reporting_authority: str
    is_active: bool
    effective_from: datetime
    effective_to: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RoadClosureCreate(BaseModel):
    """Request payload to register a municipal road closure."""
    edge_id: str
    road_name: Optional[str] = None
    closure_status: str = "CONFIRMED_BLOCKED"
    reason: str
    verification_source: str = "PMC Traffic Police Dispatch"
    reporting_authority: str = "PMC Disaster Management Cell"
    is_active: bool = True
    effective_hours: Optional[float] = 12.0


class RoadClosureUpdate(BaseModel):
    """Request payload to update or clear a road closure."""
    closure_status: Optional[str] = None
    is_active: Optional[bool] = None
    reason: Optional[str] = None


class RouteStepItem(BaseModel):
    """Turn-by-turn road segment in an evacuation route."""
    step_index: int
    edge_id: str
    road_name: str
    highway: str
    length_m: float
    estimated_travel_time_sec: float
    exposure_tier: str
    operational_status: str
    is_oneway: bool
    directionality_status: str
    is_direction_assumed: bool
    is_bridge: bool
    is_tunnel: bool
    speed_limit_kmh: float


class RouteAlternativeItem(BaseModel):
    """Alternative evacuation route option."""
    route_id: str
    route_label: str = Field(..., description="PRIMARY, ALTERNATIVE_1, ALTERNATIVE_2")
    profile: str
    algorithm: str
    total_distance_m: float
    total_travel_time_sec: float
    steps_count: int
    exposure_summary: Dict[str, int]
    hazardous_segments_count: int
    caution_segments_count: int
    assumed_direction_segments_count: int
    shared_edges_count: int = 0
    shared_distance_m: float = 0.0
    overlap_percentage: float = 0.0
    data_freshness_utc: Optional[str] = None
    directionality_uncertainty_note: Optional[str] = None
    speed_assumptions_note: Optional[str] = None
    geometry_geojson: Dict[str, Any]
    explanation: str


class RouteRequest(BaseModel):
    """Request payload for evacuation route planning."""
    origin_lat: float
    origin_lon: float
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None
    destination_shelter_id: Optional[int] = None
    cost_profile: str = "SAFEST"  # FASTEST, SAFEST, BALANCED
    algorithm: str = "A_STAR"     # A_STAR, DIJKSTRA
    vehicle_type: str = "LIGHT_VEHICLE"
    avoid_closed_roads: bool = True
    generate_alternatives: bool = True


class RoutePlanResponse(BaseModel):
    """Full evacuation routing response envelope."""
    status: str = Field(..., description="SUCCESS, NO_PATH, OUT_OF_BOUNDS, ERROR")
    origin_snapped_node: int
    origin_snap_distance_m: float
    destination_snapped_node: int
    destination_snap_distance_m: float
    chosen_profile: str
    algorithm_used: str
    primary_route: Optional[RouteAlternativeItem] = None
    alternatives: List[RouteAlternativeItem] = Field(default_factory=list)
    avoided_closures_count: int = 0
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str
    generated_at_utc: str


class ShelterItem(BaseModel):
    """Emergency evacuation shelter registry item."""
    id: int
    facility_id: Optional[int] = None
    osm_id: Optional[str] = None
    name: str
    facility_type: str
    verification_status: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    total_capacity: Optional[int] = None
    current_occupancy: Optional[int] = None
    available_capacity: Optional[int] = None
    has_medical_support: bool = False
    is_wheelchair_accessible: bool = False
    has_generator_power: bool = False
    emergency_contact: Optional[str] = None
    source: str
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    evidence_document: Optional[str] = None
    evidence_date: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ShelterCreate(BaseModel):
    """Payload to register a new verified shelter."""
    name: str
    facility_type: str = "COMMUNITY_CENTRE"
    verification_status: str = "CANDIDATE_SHELTER"
    address: Optional[str] = None
    latitude: float
    longitude: float
    total_capacity: Optional[int] = None
    current_occupancy: Optional[int] = None
    has_medical_support: bool = False
    is_wheelchair_accessible: bool = False
    has_generator_power: bool = False
    emergency_contact: Optional[str] = None
    source: str = "Municipal Relief Register"
    verified_by: Optional[str] = None
    evidence_document: Optional[str] = None
    evidence_date: Optional[str] = None


class ShelterUpdate(BaseModel):
    """Payload to update shelter status or occupancy."""
    total_capacity: Optional[int] = None
    current_occupancy: Optional[int] = None
    verification_status: Optional[str] = None
    has_medical_support: Optional[bool] = None
    is_wheelchair_accessible: bool = False
    evidence_document: Optional[str] = None
    evidence_date: Optional[str] = None
    notes: Optional[str] = None
    updated_by: str = "Authority Officer"


class ShelterRecommendationItem(BaseModel):
    """Ranked shelter recommendation for an evacuating citizen/ward."""
    shelter: ShelterItem
    distance_to_origin_m: float
    estimated_travel_time_sec: float
    safest_route_hazard_tier: str
    is_reachable: bool
    suitability_score: float
    ranking_rationale: str
    capacity_status: str


class ShelterRecommendationResponse(BaseModel):
    """List of ranked shelter destinations with reachability metrics."""
    status: str = Field("SUCCESS", description="SUCCESS, NO_VERIFIED_SHELTER_AVAILABLE, OUT_OF_BOUNDS, ERROR")
    origin_lat: float
    origin_lon: float
    total_evaluated: int
    recommendations: List[ShelterRecommendationItem] = Field(default_factory=list, description="Officially verified shelters ONLY")
    candidate_facilities_for_review: List[ShelterRecommendationItem] = Field(default_factory=list, description="Candidate facilities requiring manual verification")
    warnings: List[str] = Field(default_factory=list)
    generated_at_utc: str


class EvacuationStatusResponse(BaseModel):
    """Overall operational readiness status of the evacuation intelligence subsystem."""
    status: str = "READY"
    graph_type: str = "MultiDiGraph"
    total_network_edges: int
    total_safe_edges: int
    total_caution_edges: int
    total_hazardous_edges: int
    total_impassable_edges: int
    active_road_closures: int
    total_registered_shelters: int
    verified_shelters_count: int
    candidate_shelters_count: int
    critical_bridges_count: int
    submerged_bridges_simulated: int
    last_assessment_timestamp_utc: str
    data_quality_disclaimer: str


class EvacuationStatisticsResponse(BaseModel):
    """Summary statistics across exposure tiers, closures, and shelter capacities."""
    exposure_tier_distribution: Dict[str, int]
    operational_status_distribution: Dict[str, int]
    shelter_status_distribution: Dict[str, int]
    total_verified_capacity: Optional[int] = None
    total_verified_occupancy: int = 0
    active_closures_count: int
    infrastructure_monitored_count: int

