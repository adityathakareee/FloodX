"""Prospective Feature Engineering Service for FLOOD-X Phase 2.3.

Builds multi-horizon forward-looking forecast feature packets (6h, 12h, 24h, 48h)
and strictly isolated backward-looking antecedent hydrological conditions.
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np

from app.schemas.prospective import ForecastHourlyPoint
from app.services.prospective.forecast_service import forecast_service

logger = logging.getLogger("floodx.prospective.features")

# Baseline climate and antecedent defaults for Pune basin when cold-starting
PUNE_ANTECEDENT_DEFAULTS = {
    "antecedent_3d_rain_mm": 25.0,
    "antecedent_7d_rain_mm": 60.0,
    "antecedent_14d_rain_mm": 110.0,
    "soil_moisture_pre_forecast": 0.36,
    "soil_saturation_capacity": 0.45,
    "is_monsoon": 1,
    "terrain_susceptibility_sfsi": 0.65
}


class ProspectiveFeatureBuilder:
    """Builds multi-horizon prospective feature vectors with strict temporal isolation."""

    def __init__(self):
        pass

    def build_horizon_features(
        self,
        forecast_points: List[ForecastHourlyPoint],
        horizon_hours: int,
        antecedent_overrides: Optional[Dict[str, Any]] = None,
        precip_multiplier: float = 1.0,
        override_peak_1h: Optional[float] = None
    ) -> Dict[str, Any]:
        """Constructs forward and backward hydrological features for a specific lead horizon.
        
        Zero Temporal Target Leakage:
        - Forward forecast metrics are computed STRICTLY from points where 1 <= lead_hours <= horizon_hours.
        - Backward antecedent metrics are STRICTLY independent of future forecast observations.
        """
        # Slice forward forecast points within lead window
        horizon_points = [p for p in forecast_points if 1 <= p.lead_hours <= horizon_hours]
        if not horizon_points:
            raise ValueError(f"No forecast points available for lead horizon {horizon_hours}h")

        # 1. Forward-Looking Forecast Metrics
        precip_series = [p.precipitation_mm * precip_multiplier for p in horizon_points]
        if override_peak_1h is not None and override_peak_1h > 0:
            # Inject forced peak into highest precipitation hour
            max_idx = int(np.argmax(precip_series)) if len(precip_series) > 0 else 0
            precip_series[max_idx] = max(precip_series[max_idx], override_peak_1h)

        rain_accum_mm = round(float(sum(precip_series)), 2)
        peak_1h_mmh = round(float(max(precip_series)) if precip_series else 0.0, 2)

        # 3h rolling maximum
        if len(precip_series) >= 3:
            peak_3h_mm = max(sum(precip_series[i:i+3]) for i in range(len(precip_series) - 2))
        else:
            peak_3h_mm = rain_accum_mm
        peak_3h_mm = round(float(peak_3h_mm), 2)

        # 6h rolling maximum
        if len(precip_series) >= 6:
            peak_6h_mm = max(sum(precip_series[i:i+6]) for i in range(len(precip_series) - 5))
        else:
            peak_6h_mm = rain_accum_mm
        peak_6h_mm = round(float(peak_6h_mm), 2)

        mean_prob = int(round(np.mean([p.precipitation_probability_pct for p in horizon_points])))
        pressures = [p.surface_pressure_hpa for p in horizon_points]
        pressure_drop_hpa = round(float(pressures[0] - pressures[-1]) if len(pressures) > 1 else 0.0, 2)

        # 2. Backward-Looking Antecedent Conditions
        ant_state = dict(PUNE_ANTECEDENT_DEFAULTS)
        if antecedent_overrides:
            for k, v in antecedent_overrides.items():
                if v is not None and k in ant_state:
                    ant_state[k] = float(v)

        soil_moisture = ant_state["soil_moisture_pre_forecast"]
        sat_capacity = ant_state["soil_saturation_capacity"]
        # Assumed topsoil wetness proxy (normalized to assumed 0.45 m3/m3 capacity); not an in-situ spatial soil survey
        sat_ratio = round(min(soil_moisture / sat_capacity, 1.0), 3)

        return {
            "horizon_hours": horizon_hours,
            "valid_from_utc": horizon_points[0].valid_time_utc,
            "valid_to_utc": horizon_points[-1].valid_time_utc,
            "forecast_metrics": {
                "forecast_rain_accumulation_mm": rain_accum_mm,
                "peak_1h_intensity_mmh": peak_1h_mmh,
                "peak_3h_accumulation_mm": peak_3h_mm,
                "peak_6h_accumulation_mm": peak_6h_mm,
                "mean_precipitation_probability_pct": mean_prob,
                "pressure_drop_hpa": pressure_drop_hpa,
                "mean_temperature_c": round(float(np.mean([p.temperature_2m_c for p in horizon_points])), 1),
                "mean_relative_humidity_pct": round(float(np.mean([p.relative_humidity_pct for p in horizon_points])), 1)
            },
            "antecedent_conditions": {
                "antecedent_3d_rain_mm": ant_state["antecedent_3d_rain_mm"],
                "antecedent_7d_rain_mm": ant_state["antecedent_7d_rain_mm"],
                "antecedent_soil_moisture": soil_moisture,
                "soil_saturation_ratio": sat_ratio,
                "soil_wetness_indicator": sat_ratio,
                "is_monsoon": int(ant_state["is_monsoon"]),
                "terrain_susceptibility_sfsi": ant_state["terrain_susceptibility_sfsi"]
            }
        }

    def build_all_horizon_features(
        self,
        antecedent_overrides: Optional[Dict[str, Any]] = None,
        precip_multiplier: float = 1.0,
        override_peak_1h: Optional[float] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Builds standardized feature sets for the canonical 6h, 12h, 24h, and 48h horizons."""
        points = forecast_service.parse_forecast_points(max_hours=48)
        horizons = [6, 12, 24, 48]
        results = {}

        for h in horizons:
            key = f"{h}h"
            results[key] = self.build_horizon_features(
                forecast_points=points,
                horizon_hours=h,
                antecedent_overrides=antecedent_overrides,
                precip_multiplier=precip_multiplier,
                override_peak_1h=override_peak_1h
            )

        return results


# Singleton instance
prospective_feature_builder = ProspectiveFeatureBuilder()

