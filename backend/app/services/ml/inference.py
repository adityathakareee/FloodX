"""Real-time Model Inference and Explainability Service for FLOOD-X Phase 2.2.

Updated in Phase 2.2.1 Independent Scientific Model Validation:
- Explicitly flags prediction task as RETROSPECTIVE_DAILY_DIAGNOSTIC.
- Surfaces decision threshold (θ = 0.50) and operational readiness boundary.
- Transparently distinguishes statistical risk diagnosis from early-warning forecasting.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd

from app.services.ml.model_trainer import (
    BEST_MODEL_PATH,
    RF_MODEL_PATH,
    SCALER_PATH,
    FEATURE_COLS,
    EVAL_REPORT_PATH
)

logger = logging.getLogger(__name__)

# Climate baseline defaults for Pune basin
PUNE_CLIMATE_DEFAULTS = {
    "precip_total_24h": 0.0,
    "precip_max_1h": 0.0,
    "precip_max_3h": 0.0,
    "precip_max_6h": 0.0,
    "precip_max_12h": 0.0,
    "precip_intensity_mean": 0.0,
    "antecedent_precip_3d": 0.0,
    "antecedent_precip_7d": 0.0,
    "antecedent_precip_14d": 0.0,
    "temp_2m_mean": 25.5,
    "temp_2m_max": 30.0,
    "temp_2m_min": 21.0,
    "relative_humidity_mean": 65.0,
    "relative_humidity_max": 85.0,
    "surface_pressure_mean": 948.0,
    "surface_pressure_min": 945.0,
    "pressure_drop_24h": 0.0,
    "soil_moisture_0_7cm_mean": 0.25,
    "soil_moisture_0_7cm_max": 0.30,
    "soil_moisture_7_28cm_mean": 0.28,
    "soil_moisture_7_28cm_max": 0.32,
    "soil_saturation_ratio_0_7cm": 0.55,
    "soil_saturation_ratio_7_28cm": 0.62,
    "vpd_mean_kpa": 1.15,
    "wind_speed_max": 15.0,
    "wind_u_mean": -2.5,
    "wind_v_mean": 1.2,
    "is_monsoon": 1
}


class ModelInferenceService:
    """Manages model loading, prediction generation, and feature contribution scoring."""

    def __init__(self):
        self.model = None
        self.scaler = None
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads serialized model and scaler from disk."""
        if os.path.exists(BEST_MODEL_PATH):
            try:
                self.model = joblib.load(BEST_MODEL_PATH)
                logger.info("Loaded model from %s", BEST_MODEL_PATH)
            except Exception as e:
                logger.error("Failed to load model from %s: %s", BEST_MODEL_PATH, e)

        if os.path.exists(SCALER_PATH):
            try:
                self.scaler = joblib.load(SCALER_PATH)
            except Exception as e:
                logger.error("Failed to load scaler from %s: %s", SCALER_PATH, e)

    def predict_flood_risk(self, input_features: Dict[str, Any]) -> Dict[str, Any]:
        """Generate flood risk probability and diagnostic guidance for given environmental inputs."""
        if self.model is None:
            self._load_artifacts()
            if self.model is None:
                raise RuntimeError("ML model is not trained yet. Run model training first.")

        # Build complete feature vector with defaults
        feature_dict = dict(PUNE_CLIMATE_DEFAULTS)
        for k, v in input_features.items():
            if k in feature_dict and v is not None:
                feature_dict[k] = float(v)

        # Derived consistency checks
        if "precip_total_24h" in input_features and "precip_max_1h" not in input_features:
            feature_dict["precip_max_1h"] = round(feature_dict["precip_total_24h"] * 0.4, 2)
        if "precip_total_24h" in input_features and "precip_max_3h" not in input_features:
            feature_dict["precip_max_3h"] = round(feature_dict["precip_total_24h"] * 0.7, 2)
        if "precip_total_24h" in input_features and "precip_max_6h" not in input_features:
            feature_dict["precip_max_6h"] = round(feature_dict["precip_total_24h"] * 0.85, 2)
        if "precip_total_24h" in input_features and "precip_max_12h" not in input_features:
            feature_dict["precip_max_12h"] = round(feature_dict["precip_total_24h"] * 0.95, 2)

        # Update soil saturation ratios
        feature_dict["soil_saturation_ratio_0_7cm"] = round(min(feature_dict["soil_moisture_0_7cm_mean"] / 0.45, 1.0), 4)
        feature_dict["soil_saturation_ratio_7_28cm"] = round(min(feature_dict["soil_moisture_7_28cm_mean"] / 0.45, 1.0), 4)

        X_vec = np.array([[feature_dict[col] for col in FEATURE_COLS]])

        # Model Inference
        raw_prob = float(self.model.predict_proba(X_vec)[0, 1])
        prob = round(raw_prob, 4)

        # Risk Tier Classification for Retrospective Daily Diagnostic
        if prob >= 0.70:
            risk_tier = "EMERGENCY"
            alert_color = "red"
            action = "RETROSPECTIVE DIAGNOSTIC CRITICAL: Day meteorological and soil conditions indicate severe catchment inundation risk. Low-lying corridors (Ekta Nagari, Pulachi Wadi, Bhide Bridge) expected submerged."
        elif prob >= 0.45:
            risk_tier = "WARNING"
            alert_color = "orange"
            action = "RETROSPECTIVE DIAGNOSTIC HIGH: Environmental conditions indicate high riverine runoff and urban nala overflow potential. Low-lying causeways vulnerable."
        elif prob >= 0.20:
            risk_tier = "WATCH"
            alert_color = "yellow"
            action = "RETROSPECTIVE DIAGNOSTIC ELEVATED: Elevated soil saturation and antecedent precipitation indicate heightened runoff responsiveness."
        else:
            risk_tier = "NORMAL"
            alert_color = "green"
            action = "RETROSPECTIVE DIAGNOSTIC ROUTINE: Base environmental conditions within non-inundating historical envelope."

        # Compute Top Contributing Drivers for this instance
        importances = dict(zip(FEATURE_COLS, getattr(self.model, "feature_importances_", [1.0 / len(FEATURE_COLS)] * len(FEATURE_COLS))))
        contributions = []
        for col in FEATURE_COLS:
            val = feature_dict[col]
            imp = importances.get(col, 0.0)
            contributions.append({
                "feature": col,
                "input_value": val,
                "importance_weight": round(float(imp), 4),
            })
        contributions.sort(key=lambda x: x["importance_weight"], reverse=True)

        return {
            "prediction_status": "SUCCESS",
            "prediction_task": "RETROSPECTIVE_DAILY_DIAGNOSTIC",
            "operational_readiness": "EXPERIMENTAL_RESEARCH_BASELINE — Not validated for real-time prospective early warning",
            "model_version": "XGBoost v1.0",
            "flood_event_risk_probability": prob,
            "decision_threshold": 0.50,
            "threshold_source": "DEFAULT_BALANCED_UNCALIBRATED",
            "test_independent_events_count": 1,
            "validation_status": "VALIDATED_WITH_LIMITATIONS",
            "risk_tier": risk_tier,
            "alert_color": alert_color,
            "operational_action_guidance": action,
            "key_driving_factors": contributions[:6],
            "input_summary": {
                "precip_total_24h_mm": feature_dict["precip_total_24h"],
                "antecedent_precip_3d_mm": feature_dict["antecedent_precip_3d"],
                "antecedent_precip_7d_mm": feature_dict["antecedent_precip_7d"],
                "soil_saturation_ratio_7_28cm": feature_dict["soil_saturation_ratio_7_28cm"],
                "pressure_drop_24h_hpa": feature_dict["pressure_drop_24h"],
                "relative_humidity_mean_pct": feature_dict["relative_humidity_mean"],
            },
            "scientific_boundary": (
                "Predicts daily regional flood event occurrence for the Pune / Mula-Mutha basin based on completed "
                "24-hour meteorological and soil conditions. This is a retrospective diagnostic classifier, NOT an "
                "operational early-warning forecast, and does NOT predict continuous street-level water depths in centimeters."
            )
        }


# Default singleton instance
model_inference_service = ModelInferenceService()
