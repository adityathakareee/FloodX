"""Comprehensive Pytest test suite for FLOOD-X Phase 2.2 / Phase 2.2.1 Machine Learning pipeline.

Tests:
- Historical event label validation and audit
- Zero-leakage daily dataset construction and temporal partition integrity
- Pure physical geomorphic Spatial Flood Susceptibility Index (SFSI) calculation (zero circularity)
- Model training, evaluation metrics, and threshold transparency (Random Forest vs XGBoost)
- Model serialization and inference in retrospective daily diagnostic mode
- REST API endpoints under /api/v1/ml/* with all audit-required fields
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ml.label_validation import label_validation_service
from app.services.ml.dataset_builder import dataset_builder_service
from app.services.ml.model_trainer import model_trainer_service, FEATURE_COLS
from app.services.ml.inference import model_inference_service
from app.services.ml.spatial_susceptibility import spatial_susceptibility_service

client = TestClient(app)


def test_label_validation_audit():
    """Verify historical event audit correctly identifies duplicates, corrections, and true events."""
    audit = label_validation_service.audit_historical_events()
    assert audit["candidates_in_2020_2024_window"] == 28
    assert audit["date_corrected_events_count"] == 3
    assert audit["duplicate_events_count"] == 5
    assert audit["flagged_non_flood_events_count"] == 12
    assert audit["unique_validated_physical_events"] == 11
    assert audit["total_positive_flood_days"] == 39

    labels = label_validation_service.get_validated_daily_labels()
    assert len(labels) == 1827
    assert (labels["flood_event_occurred"] == 1).sum() == 39


def test_dataset_construction_and_no_leakage():
    """Verify daily training dataset shape, zero nulls, and chronological partitions."""
    df = dataset_builder_service.construct_daily_dataset()
    assert len(df) == 1827
    assert set(FEATURE_COLS).issubset(df.columns)
    assert "split" in df.columns
    assert "flood_event_occurred" in df.columns

    # Verify no nulls in any feature column
    for col in FEATURE_COLS:
        assert df[col].isna().sum() == 0, f"Feature column {col} contains unexpected nulls"

    # Verify chronological partitions
    assert (df["split"] == "train").sum() == 1096
    assert (df["split"] == "validation").sum() == 365
    assert (df["split"] == "test").sum() == 366

    # Verify 2023 validation partition has zero positive events (audit finding)
    val_pos = (df[df["split"] == "validation"]["flood_event_occurred"] == 1).sum()
    assert val_pos == 0, "Validation set must reflect true 2023 zero-flood year"

    # Verify 2024 test partition has exactly 3 positive days (July 24-26, 2024 single disaster event)
    test_pos = (df[df["split"] == "test"]["flood_event_occurred"] == 1).sum()
    assert test_pos == 3

    # Verify antecedent precipitation shift (Day 0 must have 0 antecedent rain)
    assert df.loc[0, "antecedent_precip_3d"] == 0.0


def test_spatial_susceptibility_calculation():
    """Verify pure physical geomorphic SFSI scoring (zero circular target weighting)."""
    # Test high hazard coordinate (Bhide bridge / riverbank: dist=30m, slope=1.0deg, rel_elev=0.5m)
    # SFSI = 0.40(1.0) + 0.30(1.0) + 0.30(1.0) = 1.00
    res_high = spatial_susceptibility_service.calculate_point_susceptibility(
        latitude=18.5178,
        longitude=73.8441,
        dist_waterway_m=30.0,
        slope_deg=1.0,
        elevation_masl=548.0,
        relative_elevation_m=0.5
    )
    assert res_high["spatial_flood_susceptibility_index"] >= 0.75
    assert res_high["susceptibility_tier"] == "CRITICAL_CHRONIC"
    assert "scientific_boundary" in res_high

    # Component scores must NOT contain chronic_spot_score (eliminated circularity)
    assert "chronic_spot_score" not in res_high["component_scores"]
    assert "river_proximity_score" in res_high["component_scores"]
    assert "slope_score" in res_high["component_scores"]
    assert "relative_elevation_score" in res_high["component_scores"]

    # Test upland coordinate (dist=2500m, slope=12deg, rel_elev=15m)
    # SFSI = 0.40(0.10) + 0.30(0.10) + 0.30(0.10) = 0.10
    res_low = spatial_susceptibility_service.calculate_point_susceptibility(
        latitude=18.4500,
        longitude=73.8800,
        dist_waterway_m=2500.0,
        slope_deg=12.0,
        elevation_masl=680.0,
        relative_elevation_m=15.0
    )
    assert res_low["spatial_flood_susceptibility_index"] < 0.35
    assert res_low["susceptibility_tier"] == "LOW"

    # Verify overview contains canopy bias note and 6 independent benchmarks
    overview = spatial_susceptibility_service.get_susceptibility_overview()
    assert "surface_canopy_bias_note" in overview
    assert overview["hotspots_count"] == 6
    assert overview["validation_status"] == "INDEPENDENT_BENCHMARK_EVALUATION — No circular target weighting"


def test_model_training_and_evaluation_report():
    """Verify training pipeline evaluates baseline and candidate models with threshold transparency."""
    report = model_trainer_service.train_and_compare_all_models()
    assert "models_evaluated" in report
    assert len(report["models_evaluated"]) == 6

    # Verify threshold audit note
    assert "threshold_audit_note" in report
    assert "Random Forest (Balanced)" in report["threshold_audit_note"]

    models_by_name = {m["model_name"]: m for m in report["models_evaluated"]}

    # Random Forest (Balanced) achieves 100% recall at default uncalibrated θ=0.50
    rf_eval = [v for k, v in models_by_name.items() if "Random Forest" in k][0]
    assert rf_eval["decision_threshold"] == 0.50
    assert rf_eval["recall"] == 1.0
    assert rf_eval["confusion_matrix"]["true_positives"] == 3
    assert rf_eval["roc_auc"] > 0.93

    # XGBoost at default θ=0.50 has 0.0 recall
    xgb_default = [v for k, v in models_by_name.items() if "Default θ=0.50" in k][0]
    assert xgb_default["decision_threshold"] == 0.50
    assert xgb_default["recall"] == 0.0

    # XGBoost at post-hoc θ=0.25 has 1.0 recall
    xgb_tuned = [v for k, v in models_by_name.items() if "Post-Hoc θ=0.25" in k][0]
    assert xgb_tuned["decision_threshold"] == 0.25
    assert xgb_tuned["recall"] == 1.0
    assert xgb_tuned["threshold_type"] == "post_hoc_exploratory_test_tuned"


def test_model_inference():
    """Verify retrospective daily diagnostic inference outputs valid probabilities and guidance."""
    # Dry day input
    dry_res = model_inference_service.predict_flood_risk({
        "precip_total_24h": 0.0,
        "antecedent_precip_3d": 0.0,
        "is_monsoon": 0
    })
    assert dry_res["prediction_status"] == "SUCCESS"
    assert dry_res["prediction_task"] == "RETROSPECTIVE_DAILY_DIAGNOSTIC"
    assert dry_res["decision_threshold"] == 0.50
    assert 0.0 <= dry_res["flood_event_risk_probability"] <= 1.0
    assert dry_res["risk_tier"] == "NORMAL"
    assert len(dry_res["key_driving_factors"]) > 0

    # Actual flood conditions input (from July 2024 disaster)
    flood_res = model_inference_service.predict_flood_risk({
        "precip_total_24h": 80.0,
        "precip_max_1h": 35.0,
        "antecedent_precip_3d": 85.0,
        "soil_moisture_0_7cm_mean": 0.51,
        "soil_moisture_0_7cm_max": 0.52,
        "soil_moisture_7_28cm_mean": 0.51,
        "vpd_mean_kpa": 0.25,
        "relative_humidity_mean": 92.0,
        "surface_pressure_mean": 936.0,
        "pressure_drop_24h": 4.0,
        "is_monsoon": 1
    })
    assert flood_res["flood_event_risk_probability"] > dry_res["flood_event_risk_probability"]
    assert "scientific_boundary" in flood_res


def test_api_ml_status():
    """Verify GET /api/v1/ml/status endpoint."""
    response = client.get("/api/v1/ml/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY"
    assert data["prediction_task"] == "RETROSPECTIVE_DAILY_DIAGNOSTIC"
    assert data["operational_readiness"] == "EXPERIMENTAL_RESEARCH_BASELINE"
    assert "training_data_coverage" in data
    assert data["training_data_coverage"]["total_days"] == 1827


def test_api_ml_models():
    """Verify GET /api/v1/ml/models endpoint."""
    response = client.get("/api/v1/ml/models")
    assert response.status_code == 200
    models = response.json()
    assert len(models) >= 3
    assert any(m["model_name"] == "XGBoost Classifier v1.0" for m in models)
    assert any(m["model_name"] == "Random Forest Classifier (Balanced)" for m in models)
    for m in models:
        assert m["prediction_task"] == "RETROSPECTIVE_DAILY_DIAGNOSTIC"
        assert m["default_decision_threshold"] == 0.50


def test_api_ml_evaluation():
    """Verify GET /api/v1/ml/evaluation endpoint."""
    response = client.get("/api/v1/ml/evaluation")
    assert response.status_code == 200
    data = response.json()
    assert "models_evaluated" in data
    assert len(data["models_evaluated"]) == 6
    assert data["scientific_verdict"] == "APPROVED WITH LIMITATIONS"
    assert data["prediction_task"] == "RETROSPECTIVE_DAILY_DIAGNOSTIC (24-Hour Completed Day Conditions)"
    assert "threshold_audit_note" in data
    assert data["test_events_count"] == 1
    assert data["validation_events_count"] == 0


def test_api_ml_predict():
    """Verify POST /api/v1/ml/predict endpoint."""
    payload = {
        "precip_total_24h": 65.0,
        "precip_max_1h": 25.0,
        "antecedent_precip_3d": 45.0,
        "soil_moisture_0_7cm_mean": 0.45,
        "relative_humidity_mean": 90.0,
        "is_monsoon": 1
    }
    response = client.post("/api/v1/ml/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction_status"] == "SUCCESS"
    assert data["prediction_task"] == "RETROSPECTIVE_DAILY_DIAGNOSTIC"
    assert data["decision_threshold"] == 0.50
    assert "flood_event_risk_probability" in data
    assert "risk_tier" in data
    assert "key_driving_factors" in data


def test_api_ml_explainability():
    """Verify GET /api/v1/ml/explainability endpoint."""
    response = client.get("/api/v1/ml/explainability")
    assert response.status_code == 200
    data = response.json()
    assert "top_features" in data
    assert len(data["top_features"]) == 10
    assert "physical_hydrology_explanation" in data


def test_api_ml_spatial_susceptibility():
    """Verify GET /api/v1/ml/spatial-susceptibility endpoint."""
    response = client.get("/api/v1/ml/spatial-susceptibility")
    assert response.status_code == 200
    data = response.json()
    assert "chronic_hotspots" in data
    assert len(data["chronic_hotspots"]) == 6
    assert "tier_distribution" in data
    assert data["model_type"] == "PHYSICAL_GEOMORPHIC_TERRAIN"
    assert "surface_canopy_bias_note" in data
