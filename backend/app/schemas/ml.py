"""Pydantic schemas for FLOOD-X Phase 2.2 Machine Learning services.

Updated in Phase 2.2.1 Independent Scientific Model Validation:
- Explicit separation of prediction tasks (Retrospective Diagnostic vs Early Warning).
- Transparent decision thresholds and threshold provenance.
- Non-circular spatial susceptibility index metadata and canopy bias disclosure.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MLStatusResponse(BaseModel):
    """Overall status of ML model services."""
    status: str = Field(..., description="Operational status: READY, TRAINING, or ERROR")
    active_model: str = Field(..., description="Name of the active production model")
    prediction_task: str = Field(
        "RETROSPECTIVE_DAILY_DIAGNOSTIC",
        description="Prediction task type: RETROSPECTIVE_DAILY_DIAGNOSTIC, NOT prospective early warning"
    )
    operational_readiness: str = Field(
        "EXPERIMENTAL_RESEARCH_BASELINE",
        description="Operational readiness level: Not validated for real-time emergency dispatch"
    )
    training_data_coverage: Dict[str, Any] = Field(..., description="Start/end dates, partitions, and counts")
    scientific_limitations_acknowledged: bool = Field(True, description="Strict boundaries accepted")
    timestamp_utc: str = Field(..., description="Status check timestamp")


class MLModelMetadataResponse(BaseModel):
    """Metadata describing a trained ML model."""
    model_name: str
    model_type: str
    version: str
    artifact_path: str
    feature_count: int
    features: List[str]
    target_variable: str
    prediction_task: str
    training_period: str
    validation_period: str
    test_period: str
    class_imbalance_handling: str
    default_decision_threshold: float = 0.50


class MLEvaluationMetric(BaseModel):
    """Model evaluation metrics on chronological test set."""
    model_name: str
    decision_threshold: float = 0.50
    threshold_type: str = "default_uncalibrated"
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: Optional[float]
    pr_auc: Optional[float]
    test_events_detected: Optional[str] = None
    confusion_matrix: Dict[str, int]
    class_distribution_test: Dict[str, int]


class MLEvaluationResponse(BaseModel):
    """Comparison of baseline and candidate models."""
    title: str
    pilot_region: str
    target_variable: str
    prediction_task: str
    models_evaluated: List[MLEvaluationMetric]
    best_model_name: str
    scientific_verdict: str
    threshold_audit_note: str
    test_events_count: int = 1
    validation_events_count: int = 0
    scientific_limitations: List[str]


class MLPredictionRequest(BaseModel):
    """Prediction input payload for daily retrospective flood diagnostic assessment."""
    precip_total_24h: Optional[float] = Field(None, description="24-hour accumulated rainfall (mm)")
    precip_max_1h: Optional[float] = Field(None, description="Peak 1-hour rainfall intensity (mm/h)")
    antecedent_precip_3d: Optional[float] = Field(None, description="Preceding 3-day accumulated rainfall (mm)")
    antecedent_precip_7d: Optional[float] = Field(None, description="Preceding 7-day accumulated rainfall (mm)")
    temp_2m_mean: Optional[float] = Field(None, description="Mean temperature (°C)")
    relative_humidity_mean: Optional[float] = Field(None, description="Mean relative humidity (%)")
    surface_pressure_mean: Optional[float] = Field(None, description="Mean atmospheric surface pressure (hPa)")
    pressure_drop_24h: Optional[float] = Field(None, description="24-hour pressure drop (hPa)")
    soil_moisture_0_7cm_mean: Optional[float] = Field(None, description="Surface soil moisture (m3/m3)")
    soil_moisture_0_7cm_max: Optional[float] = Field(None, description="Peak surface soil moisture (m3/m3)")
    soil_moisture_7_28cm_mean: Optional[float] = Field(None, description="Root-zone soil moisture (m3/m3)")
    vpd_mean_kpa: Optional[float] = Field(None, description="Vapor pressure deficit (kPa)")
    wind_speed_max: Optional[float] = Field(None, description="Peak wind speed (km/h)")
    is_monsoon: Optional[int] = Field(1, description="1 if monsoon season (Jun-Oct), else 0")


class MLFeatureContribution(BaseModel):
    """Contribution score of a single environmental variable."""
    feature: str
    input_value: float
    importance_weight: float


class MLPredictionResponse(BaseModel):
    """Flood risk prediction output."""
    prediction_status: str
    prediction_task: str = Field(
        "RETROSPECTIVE_DAILY_DIAGNOSTIC",
        description="Prediction task: Diagnostic assessment of completed daily conditions"
    )
    operational_readiness: str = Field(
        "EXPERIMENTAL_RESEARCH_BASELINE — Not validated for real-time prospective early warning",
        description="Operational readiness boundary"
    )
    model_version: str
    flood_event_risk_probability: float
    decision_threshold: float = Field(0.50, description="Decision threshold applied")
    threshold_source: str = Field("DEFAULT_BALANCED_UNCALIBRATED", description="Source of decision threshold")
    test_independent_events_count: int = Field(1, description="Count of independent flood events in test partition")
    validation_status: str = Field("VALIDATED_WITH_LIMITATIONS", description="Audit verdict")
    risk_tier: str
    alert_color: str
    operational_action_guidance: str
    key_driving_factors: List[MLFeatureContribution]
    input_summary: Dict[str, Any]
    scientific_boundary: str


class MLExplainabilityResponse(BaseModel):
    """Feature importance analysis and physical explanation."""
    model_name: str
    methodology: str
    top_features: List[Dict[str, Any]]
    all_features_importance: List[Dict[str, Any]]
    physical_hydrology_explanation: str
    scientific_caveats: str


class SpatialSusceptibilityResponse(BaseModel):
    """Geospatial susceptibility assessment."""
    title: str
    pilot_basin: str
    model_type: str = "PHYSICAL_GEOMORPHIC_TERRAIN"
    validation_status: str = "INDEPENDENT_BENCHMARK_EVALUATION — No circular target weighting"
    methodology: str
    hotspots_count: int
    tier_distribution: Dict[str, int]
    chronic_hotspots: List[Dict[str, Any]]
    surface_canopy_bias_note: str = Field(
        ...,
        description="Copernicus GLO-90 DSM elevation includes vegetation canopy and urban structures"
    )
    disclaimer: str


class ObservedMetrics(BaseModel):
    """Observed real-time hydrometeorological and network telemetry metrics."""
    precipitation_rate_mmh: float = Field(..., description="Instantaneous precipitation rate (mm/h)")
    rainfall_accum_24h_mm: float = Field(..., description="Observed trailing past 24-hour rainfall (mm)")
    forecasted_next_24h_precip_mm: Optional[float] = Field(None, description="Prospective 24h NWP forecast accumulation (mm)")
    trailing_24h_source: Optional[str] = Field("POSTGIS_HOURLY_OBSERVATIONS", description="Provenance of trailing past 24h rainfall metric")
    surface_soil_moisture_m3m3: float = Field(..., description="Surface soil volumetric moisture (m3/m3)")
    soil_saturation_pct: float = Field(..., description="Relative surface soil wetness (%)")
    river_telemetry_status: str = Field(..., description="Status of Pune river gauge telemetry")
    active_road_closures_count: int = Field(..., description="Count of currently flooded or closed road segments")
    khadakwasla_discharge_cfs: Optional[float] = Field(None, description="Observed or estimated dam discharge (cfs)")


class CurrentConditionResponse(BaseModel):
    """Task B: Current Flood Condition Assessment response."""
    condition_status: str = Field(..., description="NORMAL, ELEVATED_PLUVIAL_RISK, SEVERE_INUNDATION_RISK, or DATA_INSUFFICIENT")
    data_freshness_status: str = Field(..., description="LIVE_FRESH, CACHED_VALID, STALE, EXPIRED, or DATA_INSUFFICIENT")
    data_freshness_age_hours: float = Field(..., description="Age of latest telemetry/observations in hours")
    data_insufficient_reason: Optional[str] = Field(None, description="Reason if data is insufficient")
    pilot_region: str = Field(..., description="Basin name")
    timestamp_utc: str = Field(..., description="Timestamp of evaluation")
    observed_metrics: ObservedMetrics
    active_warnings: List[str]
    operational_action_recommendation: str
    data_provenance: Dict[str, Any]
    scientific_boundary: str


class TaskSeparationItem(BaseModel):
    """Specification of an isolated flood intelligence task."""
    task_id: str
    task_name: str
    purpose: str
    temporal_frame: str
    data_sources: List[str]
    model_or_engine: str
    output_type: str
    validation_status: str
    operational_readiness: str


class TaskSeparationResponse(BaseModel):
    """Formal three-way task separation framework response."""
    framework_title: str
    rationale: str
    tasks: List[TaskSeparationItem]


class EventValidationResponse(BaseModel):
    """GroupKFold event-based model cross-validation results."""
    validation_framework: str
    leakage_safeguard: str
    total_records: int
    total_positive_days: int
    total_independent_flood_events: Optional[int] = None
    positive_class_ratio_pct: float
    fold_details: Optional[List[Dict[str, Any]]] = None
    sample_size_limitation: Optional[str] = None
    models_evaluated: List[Dict[str, Any]]
    scientific_takeaway: str

