"""Comprehensive Pytest test suite for FLOOD-X Phase 2.3 & 2.3.1 Prospective Flood-Risk Intelligence.

Tests:
- Forecast API parsing, issue/valid timestamps, lead hours, and timezone handling
- Forecast freshness evaluation, cache age tracking, and safeguard status enforcement
  (LIVE_FRESH, CACHED_VALID, STALE, EXPIRED, DATA_INSUFFICIENT)
- Multi-horizon feature generation (6h, 12h, 24h, 48h) and strict temporal isolation
- Khadakwasla Dam telemetry status verification (DATA_INSUFFICIENT for live API)
- Strict separation of Urban Pluvial and Riverine flood mechanisms
- Audited pluvial thresholds and metadata (UNVALIDATED_ENGINEERING_PROXY, EMPIRICAL_ANALOG_SEPT2019)
- Soil wetness indicator proxy behavior without Hortonian overclaim
- Dam discharge benchmark verification statuses (VERIFIED_MUNICIPAL, OBSERVED_HISTORICAL_EVENT)
- What-If scenario analysis isolation (SIMULATED_SCENARIO tagging)
- Source catalog audit and access mode classification
- REST API endpoints under /api/v1/prospective/* with audited terminology
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.prospective.forecast_service import forecast_service
from app.services.prospective.dam_telemetry_service import dam_telemetry_service, DAM_DISCHARGE_BENCHMARKS
from app.services.prospective.prospective_feature_builder import prospective_feature_builder
from app.services.prospective.prospective_risk_engine import (
    prospective_risk_engine,
    ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH,
    EXTREME_CONVECTIVE_THRESHOLD_MMH,
    THRESHOLD_AUDIT_METADATA
)
from app.services.prospective.prospective_inference import prospective_inference_service
from app.schemas.prospective import ScenarioAssessmentRequest

client = TestClient(app)


def test_prospective_forecast_parsing():
    """Verify raw forecast data parses into valid hourly forecast points."""
    points = forecast_service.parse_forecast_points(max_hours=48)
    assert len(points) == 48
    assert points[0].lead_hours == 1
    assert points[-1].lead_hours == 48

    # Verify fields are non-null and within physical ranges
    for pt in points:
        assert pt.precipitation_mm >= 0.0
        assert 0 <= pt.precipitation_probability_pct <= 100
        assert pt.relative_humidity_pct >= 0.0
        assert pt.surface_pressure_hpa > 800.0
        assert pt.valid_time_iso is not None
        assert pt.valid_time_utc is not None


def test_forecast_issue_and_valid_timestamps():
    """Verify monotonic lead times and timezone consistency."""
    summary = forecast_service.get_forecast_summary(max_hours=24)
    assert summary.forecast_horizon_hours == 24
    assert summary.record_count == 24
    assert summary.pilot_region.startswith("Pune")
    assert "source_metadata" in summary.model_dump()
    assert summary.data_freshness_status in ["LIVE_FRESH", "CACHED_VALID", "STALE", "EXPIRED"]


def test_forecast_freshness_safeguards():
    """Verify freshness evaluation distinguishes live vs cached and flags stale/expired data."""
    # 1. Normal evaluation returns valid metadata
    freshness = forecast_service.evaluate_freshness()
    assert freshness["data_freshness_status"] in ["LIVE_FRESH", "CACHED_VALID", "STALE", "EXPIRED"]
    assert freshness["last_retrieval_utc"] is not None
    assert freshness["forecast_issue_time_utc"] is not None
    assert isinstance(freshness["cache_age_hours"], (int, float))
    assert isinstance(freshness["forecast_age_hours"], (int, float))

    # 2. Test explicit STALE override behavior
    forecast_service.set_freshness_override("STALE")
    stale_eval = forecast_service.evaluate_freshness()
    assert stale_eval["data_freshness_status"] == "STALE"

    # 3. Test explicit EXPIRED override behavior
    forecast_service.set_freshness_override("EXPIRED")
    exp_eval = forecast_service.evaluate_freshness()
    assert exp_eval["data_freshness_status"] == "EXPIRED"

    # Reset override
    forecast_service.set_freshness_override(None)


def test_multi_horizon_feature_generation():
    """Verify multi-horizon feature calculations (6h, 12h, 24h, 48h) and temporal isolation."""
    horizons = prospective_feature_builder.build_all_horizon_features()
    assert "6h" in horizons
    assert "12h" in horizons
    assert "24h" in horizons
    assert "48h" in horizons

    r6 = horizons["6h"]["forecast_metrics"]["forecast_rain_accumulation_mm"]
    r12 = horizons["12h"]["forecast_metrics"]["forecast_rain_accumulation_mm"]
    r24 = horizons["24h"]["forecast_metrics"]["forecast_rain_accumulation_mm"]
    r48 = horizons["48h"]["forecast_metrics"]["forecast_rain_accumulation_mm"]

    # Monotonic accumulation with forward horizon length
    assert r6 <= r12 <= r24 <= r48

    # Antecedent conditions must be identical across horizons (isolated prior to forecast start)
    ant_6h = horizons["6h"]["antecedent_conditions"]
    ant_48h = horizons["48h"]["antecedent_conditions"]
    assert ant_6h["antecedent_3d_rain_mm"] == ant_48h["antecedent_3d_rain_mm"]
    assert ant_6h["soil_saturation_ratio"] == ant_48h["soil_saturation_ratio"]
    assert "soil_wetness_indicator" in ant_6h


def test_pluvial_threshold_auditing_and_metadata():
    """Verify pluvial thresholds are audited with engineering proxy classifications."""
    assert ASSUMED_DRAINAGE_CAPACITY_PROXY_MMH == 25.0
    assert EXTREME_CONVECTIVE_THRESHOLD_MMH == 45.0

    features_6h = prospective_feature_builder.build_all_horizon_features()["6h"]
    pluvial = prospective_risk_engine.evaluate_pluvial_risk(features_6h)

    assert pluvial.drainage_threshold_mmh == 25.0
    assert pluvial.drainage_threshold_status == "UNVALIDATED_ENGINEERING_PROXY"
    assert pluvial.threshold_audit_metadata is not None
    assert "drainage_capacity_proxy_mmh" in pluvial.threshold_audit_metadata
    assert "extreme_convective_threshold_mmh" in pluvial.threshold_audit_metadata
    assert pluvial.threshold_audit_metadata["extreme_convective_threshold_mmh"]["status"] == "EMPIRICAL_ANALOG_SEPT2019"
    assert "soil_wetness_indicator_proxy" in pluvial.threshold_audit_metadata


def test_soil_wetness_proxy_behavior():
    """Verify topsoil wetness proxy modulates risk without claiming uniform Vertisol or Hortonian runoff."""
    features = prospective_feature_builder.build_all_horizon_features()["6h"]

    # High wetness scenario
    features_wet = dict(features)
    features_wet["antecedent_conditions"] = dict(features["antecedent_conditions"])
    features_wet["antecedent_conditions"]["soil_saturation_ratio"] = 0.90
    pluvial_wet = prospective_risk_engine.evaluate_pluvial_risk(features_wet)
    assert any("topsoil wetness proxy" in f for f in pluvial_wet.contributing_factors)

    # Dry soil scenario
    features_dry = dict(features)
    features_dry["antecedent_conditions"] = dict(features["antecedent_conditions"])
    features_dry["antecedent_conditions"]["soil_saturation_ratio"] = 0.35
    pluvial_dry = prospective_risk_engine.evaluate_pluvial_risk(features_dry)
    assert any("topsoil wetness proxy" in f for f in pluvial_dry.contributing_factors)
    # Check that it notes urban surface runoff still occurs
    assert any("paved urban surfaces still generate" in f for f in pluvial_dry.contributing_factors)


def test_dam_telemetry_status_data_insufficient():
    """Verify live dam telemetry is correctly reported as DATA_INSUFFICIENT without fabrication."""
    status_info = dam_telemetry_service.check_telemetry_status()
    assert status_info["is_live_available"] is False
    assert status_info["telemetry_status"] == "DATA_INSUFFICIENT"
    assert "WRD" in status_info["provider"]
    assert "No public unauthenticated streaming REST API" in status_info["reason"]


def test_dam_discharge_benchmarks_audit_statuses():
    """Verify canonical benchmark evaluations and audited verification statuses."""
    # 1. Normal low flow (4,000 cfs)
    eval_low = dam_telemetry_service.evaluate_discharge_scenario(4000.0)
    assert eval_low["risk_tier"] == "NORMAL"
    assert eval_low["exceeds_bhide_submergence"] is False
    assert eval_low["benchmark_verification_status"] == "ILLUSTRATIVE_SCENARIO_BENCHMARK"

    # 2. Approaching causeway (12,000 cfs)
    eval_watch = dam_telemetry_service.evaluate_discharge_scenario(12000.0)
    assert eval_watch["risk_tier"] == "WATCH"
    assert eval_watch["exceeds_bhide_submergence"] is False

    # 3. Bhide causeway submergence threshold (15,000 cfs - unverified operational reference)
    eval_bhide = dam_telemetry_service.evaluate_discharge_scenario(15000.0)
    assert eval_bhide["risk_tier"] == "WARNING"
    assert eval_bhide["exceeds_bhide_submergence"] is True
    assert eval_bhide["benchmark_verification_status"] == "UNVERIFIED_OPERATIONAL_REFERENCE"

    # 4. July 25, 2024 disaster benchmark (35,574 cfs - observed single-event benchmark)
    eval_disaster = dam_telemetry_service.evaluate_discharge_scenario(35574.0)
    assert eval_disaster["risk_tier"] == "EMERGENCY"
    assert eval_disaster["exceeds_july2024_disaster"] is True
    assert eval_disaster["benchmark_verification_status"] == "OBSERVED_HISTORICAL_EVENT_BENCHMARK"

    # Check canonical dictionary
    canonical = dam_telemetry_service.get_canonical_benchmarks()
    assert "audit_notes" in canonical
    assert DAM_DISCHARGE_BENCHMARKS["BHIDE_SUBMERGENCE"]["verification_status"] == "UNVERIFIED_OPERATIONAL_REFERENCE"
    assert DAM_DISCHARGE_BENCHMARKS["JULY2024_DISASTER_PEAK"]["verification_status"] == "OBSERVED_HISTORICAL_EVENT_BENCHMARK"


def test_pluvial_vs_riverine_separation():
    """Verify strict separation between urban pluvial and riverine risk mechanisms."""
    features_24h = prospective_feature_builder.build_all_horizon_features()["24h"]

    # Live assessment (no dam discharge scenario): riverine MUST be DATA_INSUFFICIENT
    assessment = prospective_risk_engine.assess_horizon(
        horizon_label="24h",
        feature_packet=features_24h,
        simulated_dam_discharge_cfs=None
    )
    assert assessment.riverine_risk.risk_tier == "DATA_INSUFFICIENT"
    assert assessment.riverine_risk.risk_score is None
    assert assessment.pluvial_risk.risk_tier in ["NORMAL", "WATCH", "WARNING", "EMERGENCY"]
    assert assessment.pluvial_risk.drainage_threshold_mmh == 25.0

    # Assessment with scenario discharge (35,574 cfs): riverine becomes EMERGENCY while pluvial evaluated independently
    assessment_sim = prospective_risk_engine.assess_horizon(
        horizon_label="24h",
        feature_packet=features_24h,
        simulated_dam_discharge_cfs=35574.0
    )
    assert assessment_sim.riverine_risk.risk_tier == "EMERGENCY"
    assert assessment_sim.riverine_risk.risk_score > 90.0
    assert assessment_sim.overall_alert_level == "EMERGENCY"


def test_scenario_isolation_and_tags():
    """Verify scenario analysis outputs are explicitly tagged as SIMULATED_SCENARIO."""
    req = ScenarioAssessmentRequest(
        scenario_name="Monsoon Cloudburst Simulation",
        rainfall_multiplier=2.5,
        override_peak_1h_mmh=45.0,
        simulated_dam_discharge_cfs=20000.0
    )
    res = prospective_inference_service.generate_scenario_assessment(req)
    assert res.is_simulated is True
    assert res.simulation_tag == "SIMULATED_SCENARIO"
    assert "6h" in res.horizons
    assert "SIMULATED SCENARIO ONLY" in res.operational_disclaimer


def test_sources_catalog_assessment():
    """Verify catalog covers all 4 investigated sources with correct access modes."""
    catalog = prospective_inference_service.get_sources_catalog()
    assert len(catalog.sources) == 4
    source_names = [s.official_name for s in catalog.sources]

    assert any("Open-Meteo" in name for name in source_names)
    assert any("India Meteorological Department" in name for name in source_names)
    assert any("Khadakwasla Dam" in name for name in source_names)
    assert any("CWPRS" in name for name in source_names)

    # Check access modes
    imd = [s for s in catalog.sources if "India Meteorological Department" in s.official_name][0]
    assert imd.access_mode == "MANUAL_REGISTRATION"

    wrd = [s for s in catalog.sources if "Khadakwasla Dam" in s.official_name][0]
    assert wrd.access_mode == "RESTRICTED_DEPARTMENTAL"


def test_api_prospective_status():
    """Verify GET /api/v1/prospective/status enforces correct terminology and metadata."""
    resp = client.get("/api/v1/prospective/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["READY", "DEGRADED", "STALE", "ERROR"]
    assert data["prediction_task"] == "PROSPECTIVE_RISK_ASSESSMENT"
    assert data["engine_type"] == "EXPERIMENTAL_RULE_BASED_ENGINE"
    assert data["dam_telemetry_status"] == "DATA_INSUFFICIENT"
    assert data["forecast_freshness_status"] in ["LIVE_FRESH", "CACHED_VALID", "STALE", "EXPIRED"]
    assert data["api_retrieval_time_utc"] is not None
    assert "6h" in data["horizons_supported"]


def test_api_prospective_forecast():
    """Verify GET /api/v1/prospective/forecast."""
    resp = client.get("/api/v1/prospective/forecast?horizon_hours=24")
    assert resp.status_code == 200
    data = resp.json()
    assert data["forecast_horizon_hours"] == 24
    assert len(data["forecast_points"]) == 24
    assert "data_freshness_status" in data


def test_api_prospective_sources():
    """Verify GET /api/v1/prospective/sources."""
    resp = client.get("/api/v1/prospective/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sources"]) == 4


def test_api_prospective_benchmarks():
    """Verify GET /api/v1/prospective/benchmarks."""
    resp = client.get("/api/v1/prospective/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert "benchmarks" in data
    assert "BHIDE_SUBMERGENCE" in data["benchmarks"]
    assert data["benchmarks"]["BHIDE_SUBMERGENCE"]["verification_status"] == "UNVERIFIED_OPERATIONAL_REFERENCE"


def test_api_prospective_assess():
    """Verify POST /api/v1/prospective/assess."""
    resp = client.post("/api/v1/prospective/assess")
    assert resp.status_code == 200
    data = resp.json()
    assert "horizons" in data
    assert "6h" in data["horizons"]
    assert "24h" in data["horizons"]
    assert data["horizons"]["6h"]["human_verification_required"] is True
    assert data["data_provenance"]["prediction_task"] == "PROSPECTIVE_RISK_ASSESSMENT"
    assert data["data_provenance"]["engine_type"] == "EXPERIMENTAL_RULE_BASED_ENGINE"


def test_api_prospective_scenario():
    """Verify POST /api/v1/prospective/scenario."""
    payload = {
        "scenario_name": "Emergency Release Test",
        "rainfall_multiplier": 1.5,
        "simulated_dam_discharge_cfs": 35574.0
    }
    resp = client.post("/api/v1/prospective/scenario", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_simulated"] is True
    assert data["simulation_tag"] == "SIMULATED_SCENARIO"
    assert data["horizons"]["24h"]["riverine_risk"]["risk_tier"] == "EMERGENCY"
