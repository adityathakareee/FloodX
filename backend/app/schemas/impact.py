"""Pydantic schemas for FLOOD-X Phase 5 Flood Impact Assessment & SAR Integration."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ExposedFacility(BaseModel):
    """Infrastructure facility within or adjacent to flood hazard zone."""
    facility_type: str = Field(..., description="HEALTHCARE, EDUCATION, or CIVIC")
    name: str = Field(..., description="Name of facility")
    osm_id: Optional[str] = None
    distance_to_hazard_m: float = Field(..., description="Distance to nearest inundation boundary (0.0 if inside)")
    exposure_tier: str = Field(..., description="CRITICAL, HIGH, MODERATE, or LOW")
    latitude: float
    longitude: float
    access_threatened: bool
    operational_impact: str
    exposure_nature: str = Field(
        "PROXIMITY_BUFFER_EVALUATION",
        description="PROXIMITY_BUFFER_EVALUATION, SIMULATED_HAZARD_EXPOSURE, or OBSERVED_FLOOD_IMPACT (evaluated buffer overlap, not confirmed physical destruction)"
    )


class ExposedBridge(BaseModel):
    """Bridge or causeway crossing the Mula or Mutha river."""
    name: str
    osm_id: Optional[str] = None
    waterway: str
    inundation_risk: str = Field(..., description="SUBMERGED, HIGH_RISK, or CLEAR")
    submerged: bool
    critical_threshold_cfs: float
    threshold_classification: str = Field(
        "ILLUSTRATIVE_SCENARIO",
        description="VERIFIED_OPERATIONAL_THRESHOLD, OBSERVED_EVENT_REFERENCE, UNVERIFIED_OPERATIONAL_REFERENCE, or ILLUSTRATIVE_SCENARIO"
    )
    is_simulated: bool = Field(True, description="True if threshold is an illustrative or unverified simulation benchmark")
    latitude: float
    longitude: float
    operational_status: str


class RoadImpactSummary(BaseModel):
    """Aggregate transportation disruption metrics with clear provenance distinction."""
    total_road_network_km: float
    inundated_road_km: float
    inundated_percentage: float
    closed_or_blocked_segments_count: int
    critical_corridors_affected: List[str]
    confirmed_closed_segments_count: int = Field(0, description="Official municipal closures verified in database")
    proximity_exposed_segments_count: int = Field(0, description="Evaluated segments within hazard proximity buffer")
    hazard_evaluation_type: str = Field(
        "PROXIMITY_EXPOSURE_EVALUATION",
        description="Distinguishes CONFIRMED_BLOCKED, TERRAIN_SUSCEPTIBILITY, PROXIMITY_EXPOSURE, SIMULATED_HAZARD, or OBSERVED_IMPACT"
    )
    disclaimer: str = Field(
        "Evaluations reflect proximity-based spatial overlap or simulation benchmarks, NOT field-confirmed road washouts unless marked as CONFIRMED_BLOCKED.",
        description="Mandatory distinction disclaimer"
    )


class PopulationExposureSummary(BaseModel):
    """Demographic exposure summary across affected Pune wards."""
    data_status: str = Field(
        "DATA_INSUFFICIENT",
        description="Data provenance status for demographic exposure: DATA_INSUFFICIENT when no audited census or gridded population raster is ingested"
    )
    estimated_exposed_population: Optional[int] = Field(
        None,
        description="Estimated population exposed. Null when ground-truth demographic raster is unavailable"
    )
    lower_bound_estimate: Optional[int] = Field(
        None,
        description="Lower confidence interval. Null when unsupported by empirical data"
    )
    upper_bound_estimate: Optional[int] = Field(
        None,
        description="Upper confidence interval. Null when unsupported by empirical data"
    )
    primary_wards_affected: List[str]
    methodology: str
    estimation_uncertainty_caveat: str
    missing_data_explanation: str = Field(
        "Official Census of India 2011 ward polygons and high-resolution gridded population rasters (WorldPop/LandScan) are not ingested in the repository. Numerical population figures are withheld to prevent false scientific precision.",
        description="Explanation of missing demographic data layers"
    )


class HazardMetadata(BaseModel):
    """Provenance and scientific processing parameters of the hazard layer."""
    hazard_source: str = Field(
        ...,
        description="OBSERVED_SAR_EXTENT (Illustrative analog), MODEL_DERIVED_INUNDATION, TERRAIN_SUSCEPTIBILITY, PROXIMITY_EXPOSURE, SIMULATED_SCENARIO, or ILLUSTRATIVE_HISTORICAL_EVENT"
    )
    scene_or_event_name: str
    verification_status: str = Field(
        "UNVERIFIED_ILLUSTRATIVE_EXTENT (No raw SAR raster processed in repo)",
        description="Scientific data verification state"
    )
    backscatter_threshold_db: Optional[float] = Field(None, description="Nominal dB threshold for SAR analog or None if unverified raster")
    slope_cutoff_deg: float = Field(5.0, description="Copernicus DEM slope mask cutoff")
    permanent_water_masked: bool = True
    urban_double_bounce_masked: bool = True
    depth_inference_disclaimer: str = Field(
        "SAR C-band backscatter detects open water surface extent only. It CANNOT measure flood depth. Never infer depth from SAR alone.",
        description="Mandatory scientific disclaimer"
    )


class ImpactAssessmentResponse(BaseModel):
    """Complete multi-sector flood impact assessment report."""
    assessment_id: str
    scenario_name: str
    timestamp_utc: str
    pilot_region: str
    hazard_metadata: HazardMetadata
    population_exposure: PopulationExposureSummary
    healthcare_impact: List[ExposedFacility]
    education_impact: List[ExposedFacility]
    bridges_impact: List[ExposedBridge]
    road_network_impact: RoadImpactSummary
    overall_severity: str = Field(..., description="LOW, MODERATE, SEVERE, or CATASTROPHIC")
    key_recommendations: List[str]
    data_provenance: Dict[str, Any]


class ImpactScenarioComparison(BaseModel):
    """Historical or simulated disaster scenario comparison metric."""
    scenario_id: str
    scenario_name: str
    event_date: str
    khadakwasla_discharge_cfs: float
    rainfall_24h_mm: float
    estimated_exposed_population: Optional[int] = Field(None, description="Documented PMC municipal evacuation estimate or None if unquantified")
    inundated_road_km: float
    affected_healthcare_count: int
    affected_bridges_count: int
    severity_level: str
    description: str


class ImpactScenariosResponse(BaseModel):
    """Catalog of historical and scenario flood impacts."""
    baseline_scenario: ImpactScenarioComparison
    historical_scenarios: List[ImpactScenarioComparison]
    disclaimer: str


class ImpactAssessmentRequest(BaseModel):
    """Payload to trigger a multi-sector impact assessment."""
    hazard_source: str = Field(
        "SIMULATED_SCENARIO",
        description="OBSERVED_SAR_EXTENT, ILLUSTRATIVE_HISTORICAL_EVENT, MODEL_DERIVED_INUNDATION, TERRAIN_SUSCEPTIBILITY, PROXIMITY_EXPOSURE, or SIMULATED_SCENARIO"
    )
    simulated_discharge_cfs: Optional[float] = Field(None, description="Khadakwasla Dam discharge in cfs")
    rain_rate_mmh: Optional[float] = Field(None, description="Convective rain rate in mm/h")
    scenario_name: Optional[str] = Field("Custom Simulated Assessment", description="Scenario label")


class ImpactLayersResponse(BaseModel):
    """GeoJSON FeatureCollections for map rendering."""
    hazard_source: str
    flood_extent_geojson: Dict[str, Any]
    exposed_infrastructure_geojson: Dict[str, Any]
    critical_bridges_geojson: Dict[str, Any]
    high_risk_roads_geojson: Dict[str, Any]
    metadata: Dict[str, Any]

