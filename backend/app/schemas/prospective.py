"""Pydantic schemas for FLOOD-X Phase 2.3 Prospective Flood-Risk Intelligence.

Provides strongly typed schemas for:
- Data source assessment & telemetry provenance
- Multi-horizon forward-looking forecast data (6h, 12h, 24h, 48h)
- Separated Riverine and Pluvial flood risk assessments
- Live prospective assessments and What-If simulated scenarios
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SourceAssessmentItem(BaseModel):
    """Assessment details for a candidate meteorological or hydrological data source."""
    official_name: str
    url: str
    variables_available: List[str]
    geographic_coverage: str
    update_frequency: str
    forecast_horizon: str
    timestamp_conventions: str
    authentication_requirements: str
    license_restrictions: str
    reliability_limitations: str
    access_mode: str = Field(..., description="AUTOMATIC, MANUAL_REGISTRATION, or RESTRICTED_DEPARTMENTAL")
    operational_integration_status: str


class ProspectiveSourcesResponse(BaseModel):
    """Catalog of investigated forecast and telemetry sources."""
    title: str
    audit_date: str
    sources: List[SourceAssessmentItem]
    live_dam_telemetry_status: str
    recommendations: List[str]


class ProspectiveStatusResponse(BaseModel):
    """Operational status of the prospective flood intelligence engine."""
    status: str = Field(..., description="Operational status: READY, DEGRADED, STALE, or ERROR")
    engine_name: str = "FLOOD-X Prospective Hydrometeorological Risk Engine v1.0"
    engine_type: str = "EXPERIMENTAL_RULE_BASED_ENGINE"
    prediction_task: str = "PROSPECTIVE_RISK_ASSESSMENT"
    horizons_supported: List[str] = Field(
        default=["6h", "12h", "24h", "48h"],
        description="Forward-looking outlook horizons"
    )
    forecast_source: str = "Open-Meteo High-Resolution Numerical Weather Prediction"
    forecast_freshness_status: str = Field(
        ...,
        description="LIVE_FRESH, CACHED_VALID, STALE, EXPIRED, or DATA_INSUFFICIENT"
    )
    forecast_issue_time_utc: str
    api_retrieval_time_utc: Optional[str] = None
    cache_age_hours: Optional[float] = None
    forecast_age_hours: Optional[float] = None
    freshness_warning: Optional[str] = None
    dam_telemetry_status: str = Field(
        "DATA_INSUFFICIENT",
        description="Real-time Khadakwasla Dam discharge feed status"
    )
    human_verification_required: bool = True
    timestamp_utc: str


class ForecastHourlyPoint(BaseModel):
    """Single hourly forecast prediction point."""
    valid_time_iso: str
    valid_time_utc: str
    lead_hours: int
    precipitation_mm: float
    precipitation_probability_pct: int
    rain_mm: float
    temperature_2m_c: float
    relative_humidity_pct: float
    surface_pressure_hpa: float
    wind_speed_10m_kmh: float
    wind_direction_10m_deg: float
    soil_moisture_0_7cm: float


class ProspectiveForecastResponse(BaseModel):
    """Structured forward-looking hourly forecast series."""
    pilot_region: str
    issue_time_utc: str
    timezone: str = "Asia/Kolkata"
    forecast_horizon_hours: int
    record_count: int
    forecast_points: List[ForecastHourlyPoint]
    source_metadata: Dict[str, Any]
    data_freshness_status: str = Field("CACHED_VALID", description="LIVE_FRESH, CACHED_VALID, STALE, EXPIRED, DATA_INSUFFICIENT")


class PluvialRiskAssessment(BaseModel):
    """Independent assessment of urban surface pluvial flood and drainage choke risk."""
    flood_mechanism: str = "URBAN_PLUVIAL"
    risk_tier: str = Field(..., description="NORMAL, WATCH, WARNING, or EMERGENCY")
    risk_score: float = Field(..., description="Rule-based pluvial index from 0 to 100")
    drainage_threshold_mmh: float = Field(25.0, description="Assumed municipal storm drain capacity proxy (mm/h)")
    drainage_threshold_status: str = Field(
        "UNVALIDATED_ENGINEERING_PROXY",
        description="Validation status of the drainage threshold"
    )
    peak_forecast_intensity_mmh: float
    forecast_accumulation_mm: float
    antecedent_soil_saturation_ratio: float = Field(
        ...,
        description="Assumed topsoil wetness proxy ratio (0.0 to 1.0)"
    )
    soil_wetness_indicator: float = Field(
        ...,
        description="Assumed topsoil wetness proxy ratio (0.0 to 1.0)"
    )
    contributing_factors: List[str]
    physical_reasoning: str
    threshold_audit_metadata: Optional[Dict[str, Any]] = None


class RiverineRiskAssessment(BaseModel):
    """Independent assessment of Mula-Mutha riverine overbank and dam release risk."""
    flood_mechanism: str = "RIVERINE_OVERBANK"
    risk_tier: str = Field(..., description="NORMAL, WATCH, WARNING, EMERGENCY, or DATA_INSUFFICIENT")
    risk_score: Optional[float] = Field(None, description="Riverine index 0-100 or None if DATA_INSUFFICIENT")
    dam_telemetry_status: str = Field(..., description="DATA_INSUFFICIENT, SIMULATED_SCENARIO, or VERIFIED_FEED")
    simulated_dam_discharge_cfs: Optional[float] = None
    bhide_causeway_threshold_cfs: float = 15000.0
    july2024_disaster_threshold_cfs: float = 35574.0
    benchmark_verification_status: Optional[str] = Field(
        None,
        description="UNVERIFIED_OPERATIONAL_REFERENCE, OBSERVED_HISTORICAL_EVENT_BENCHMARK, or ILLUSTRATIVE_SCENARIO_BENCHMARK"
    )
    contributing_factors: List[str]
    physical_reasoning: str
    benchmark_metadata: Optional[Dict[str, Any]] = None


class HorizonProspectiveAssessment(BaseModel):
    """Multi-horizon prospective assessment packet for a specific forward window."""
    horizon_label: str = Field(..., description="6h, 12h, 24h, or 48h")
    horizon_hours: int
    valid_from_utc: str
    valid_to_utc: str
    forecast_rain_accumulation_mm: float
    max_1h_rainfall_intensity_mmh: float
    mean_precipitation_probability_pct: int
    antecedent_3d_rain_mm: float
    antecedent_soil_moisture: float
    pluvial_risk: PluvialRiskAssessment
    riverine_risk: RiverineRiskAssessment
    overall_alert_level: str
    alert_color: str
    operational_action_guidance: str
    human_verification_required: bool = True


class ProspectiveAssessmentResponse(BaseModel):
    """Complete multi-horizon prospective flood risk outlook."""
    assessment_id: str
    issue_time_utc: str
    valid_until_utc: str
    pilot_region: str
    data_provenance: Dict[str, Any]
    horizons: Dict[str, HorizonProspectiveAssessment]
    overall_summary: str
    scientific_boundaries: str
    human_verification_notice: str


class ScenarioAssessmentRequest(BaseModel):
    """Input payload for What-If emergency scenario simulation."""
    scenario_name: str = Field(..., description="Descriptive scenario label")
    rainfall_multiplier: float = Field(1.0, ge=0.0, le=5.0, description="Precipitation scaling factor")
    override_peak_1h_mmh: Optional[float] = Field(None, ge=0.0, le=150.0, description="Forced peak 1h intensity (mm/h)")
    simulated_dam_discharge_cfs: Optional[float] = Field(None, ge=0.0, le=100000.0, description="Khadakwasla Dam release (cfs)")
    override_soil_moisture: Optional[float] = Field(None, ge=0.10, le=0.52, description="Surface soil moisture (m3/m3)")
    override_antecedent_3d_mm: Optional[float] = Field(None, ge=0.0, le=300.0, description="Prior 3-day rainfall (mm)")


class ScenarioAssessmentResponse(BaseModel):
    """Output for What-If emergency scenario simulation."""
    scenario_name: str
    is_simulated: bool = True
    simulation_tag: str = "SIMULATED_SCENARIO"
    simulated_dam_discharge_cfs: Optional[float]
    horizons: Dict[str, HorizonProspectiveAssessment]
    comparison_with_baseline: Dict[str, Any]
    operational_disclaimer: str

