"""FastAPI REST endpoints for Machine Learning Flood Risk Prediction and Susceptibility.

PCCOE International Grand Challenge 2026.
FLOOD-X Phase 2.2 / 2.2.1: AI/ML Flood Prediction & Vulnerability Analysis.
"""

import os
from datetime import datetime, timezone
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status

from app.schemas.ml import (
    MLStatusResponse,
    MLModelMetadataResponse,
    MLEvaluationResponse,
    MLPredictionRequest,
    MLPredictionResponse,
    MLExplainabilityResponse,
    SpatialSusceptibilityResponse,
    CurrentConditionResponse,
    TaskSeparationResponse,
    EventValidationResponse,
)
from app.services.ml.model_trainer import model_trainer_service, FEATURE_COLS, BEST_MODEL_PATH
from app.services.ml.inference import model_inference_service
from app.services.ml.spatial_susceptibility import spatial_susceptibility_service
from app.services.ml.label_validation import label_validation_service
from app.services.ml.current_condition_service import current_condition_service
from app.services.ml.event_validation import event_validation_service

logger = logging.getLogger("floodx.api.ml")
router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.get("/status", response_model=MLStatusResponse)
def get_ml_status() -> MLStatusResponse:
    """Returns the operational status and scientific boundaries of the ML flood intelligence engine."""
    model_exists = os.path.exists(BEST_MODEL_PATH)
    return MLStatusResponse(
        status="READY" if model_exists else "TRAINING_REQUIRED",
        active_model="XGBoost Classifier v1.0" if model_exists else "None",
        prediction_task="RETROSPECTIVE_DAILY_DIAGNOSTIC",
        operational_readiness="EXPERIMENTAL_RESEARCH_BASELINE",
        training_data_coverage={
            "start_date": "2020-01-01",
            "end_date": "2024-12-31",
            "total_days": 1827,
            "train_days": 1096,
            "validation_days": 365,
            "test_days": 366,
            "total_positive_flood_days": 39,
            "pilot_region": "Pune / Mula-Mutha River Basin (18.40N-18.65N, 73.70E-74.05E)"
        },
        scientific_limitations_acknowledged=True,
        timestamp_utc=datetime.now(timezone.utc).isoformat()
    )


@router.get("/models", response_model=List[MLModelMetadataResponse])
def list_ml_models() -> List[MLModelMetadataResponse]:
    """Lists all investigated baseline and production candidate models."""
    return [
        MLModelMetadataResponse(
            model_name="XGBoost Classifier v1.0",
            model_type="Gradient Boosted Decision Trees",
            version="1.0.0",
            artifact_path=BEST_MODEL_PATH,
            feature_count=len(FEATURE_COLS),
            features=FEATURE_COLS,
            target_variable="flood_event_occurred",
            prediction_task="RETROSPECTIVE_DAILY_DIAGNOSTIC",
            training_period="2020-01-01 to 2022-12-31 (1,096 days)",
            validation_period="2023-01-01 to 2023-12-31 (365 days)",
            test_period="2024-01-01 to 2024-12-31 (366 days)",
            class_imbalance_handling="scale_pos_weight=29.44",
            default_decision_threshold=0.50
        ),
        MLModelMetadataResponse(
            model_name="Random Forest Classifier (Balanced)",
            model_type="Bagged Decision Trees Ensemble",
            version="1.0.0",
            artifact_path="data/models/floodx_rf_model.joblib",
            feature_count=len(FEATURE_COLS),
            features=FEATURE_COLS,
            target_variable="flood_event_occurred",
            prediction_task="RETROSPECTIVE_DAILY_DIAGNOSTIC",
            training_period="2020-01-01 to 2022-12-31 (1,096 days)",
            validation_period="2023-01-01 to 2023-12-31 (365 days)",
            test_period="2024-01-01 to 2024-12-31 (366 days)",
            class_imbalance_handling="class_weight='balanced'",
            default_decision_threshold=0.50
        ),
        MLModelMetadataResponse(
            model_name="Logistic Regression (L2)",
            model_type="Linear Generalized Linear Model",
            version="1.0.0",
            artifact_path="in-memory",
            feature_count=len(FEATURE_COLS),
            features=FEATURE_COLS,
            target_variable="flood_event_occurred",
            prediction_task="RETROSPECTIVE_DAILY_DIAGNOSTIC",
            training_period="2020-01-01 to 2022-12-31 (1,096 days)",
            validation_period="2023-01-01 to 2023-12-31 (365 days)",
            test_period="2024-01-01 to 2024-12-31 (366 days)",
            class_imbalance_handling="class_weight='balanced'",
            default_decision_threshold=0.50
        )
    ]


@router.get("/evaluation", response_model=MLEvaluationResponse)
def get_model_evaluation() -> MLEvaluationResponse:
    """Returns the comprehensive chronological evaluation metrics comparing all models on the held-out 2024 test year."""
    report = model_trainer_service.get_evaluation_report()

    return MLEvaluationResponse(
        title=report["title"],
        pilot_region=report["pilot_region"],
        target_variable=report["target_variable"],
        prediction_task=report.get("prediction_task", "RETROSPECTIVE_DAILY_DIAGNOSTIC"),
        models_evaluated=report["models_evaluated"],
        best_model_name=report["best_model"]["model_name"],
        scientific_verdict="APPROVED WITH LIMITATIONS",
        threshold_audit_note=report.get("threshold_audit_note", ""),
        test_events_count=report.get("test_events_count", 1),
        validation_events_count=report.get("validation_events_count", 0),
        scientific_limitations=[
            "Strict Retrospective Diagnostic task: uses full completed 24-hour meteorological and soil conditions. Not an operational prospective early-warning forecast.",
            "Single test event constraint: the held-out 2024 test year contains exactly 1 historical flood event (July 24-26, 2024 Khadakwasla disaster, 3 positive days). Precision metrics are subject to extreme variance due to small sample size.",
            "Threshold sensitivity: At default uncalibrated θ = 0.50, Random Forest achieves 100% disaster recall (3/3 days), whereas XGBoost achieves 0% recall and required post-hoc test-set threshold tuning (θ = 0.25).",
            "CWC Ankali Bridge gauge (Sangli, 205.3 km downstream) is strictly excluded from Pune model training and evaluation."
        ]
    )


@router.post("/predict", response_model=MLPredictionResponse)
def predict_flood_risk(request: MLPredictionRequest) -> MLPredictionResponse:
    """Predicts daily flood event probability, alert level, and key contributing features for input weather conditions."""
    try:
        input_data = request.model_dump(exclude_unset=True)
        result = model_inference_service.predict_flood_risk(input_data)
        return MLPredictionResponse(**result)
    except Exception as e:
        logger.error("Error during ML flood prediction: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}"
        )


@router.get("/explainability", response_model=MLExplainabilityResponse)
def get_model_explainability() -> MLExplainabilityResponse:
    """Returns feature importance analysis and physical hydrological explanation."""
    report = model_trainer_service.get_evaluation_report()
    best_model = report["best_model"]

    return MLExplainabilityResponse(
        model_name=best_model["model_name"],
        methodology="Tree-based Gini Split Gain Importance (XGBoost)",
        top_features=best_model["top_10_features"],
        all_features_importance=best_model["all_features_importance"],
        physical_hydrology_explanation=(
            "The top three predictive drivers are: 1) Surface Soil Moisture (0-7cm max, 24.6% importance), "
            "2) Vapor Pressure Deficit (VPD, 20.5% importance), and 3) Root-zone Soil Moisture (7-28cm). "
            "This confirms established hydrological principles: in the Pune basin, rainfall on saturated "
            "Vertisol (Black Cotton) soil with near-zero atmospheric evaporative demand triggers rapid Horton "
            "and Dunne surface runoff, overwhelming natural nalas and low-elevation floodplains."
        ),
        scientific_caveats=(
            "Feature importance reflects statistical associations within the 2020-2022 empirical training sample. "
            "It does NOT assert causality and must be coupled with upstream dam release telemetry for operational dispatch."
        )
    )


@router.get("/spatial-susceptibility", response_model=SpatialSusceptibilityResponse)
def get_spatial_susceptibility() -> SpatialSusceptibilityResponse:
    """Returns the geospatial flood susceptibility index (SFSI) overview and chronic hotspot registry."""
    result = spatial_susceptibility_service.get_susceptibility_overview()
    return SpatialSusceptibilityResponse(**result)


@router.get("/current-conditions", response_model=CurrentConditionResponse)
def get_current_conditions() -> CurrentConditionResponse:
    """Task B: Real-time/recent flood condition assessment with freshness verification."""
    return current_condition_service.assess_current_conditions()


@router.get("/task-separation", response_model=TaskSeparationResponse)
def get_task_separation() -> TaskSeparationResponse:
    """Returns the formal three-way ML task separation framework (Task A vs B vs C)."""
    return current_condition_service.get_task_separation_framework()


@router.get("/event-validation", response_model=EventValidationResponse)
def get_event_validation_report() -> EventValidationResponse:
    """Returns leak-free GroupKFold cross-validation benchmark results across contiguous flood events."""
    report = event_validation_service.load_saved_report()
    if not report:
        report = event_validation_service.run_event_grouped_validation()
    return EventValidationResponse(**report)

