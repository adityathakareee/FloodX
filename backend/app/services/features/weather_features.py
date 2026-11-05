"""Hydrological and meteorological feature engineering service for Open-Meteo reanalysis & NWP forecasts."""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.observation import WeatherObservation

logger = logging.getLogger("floodx.features.weather")

# Topsoil saturation limit (volumetric moisture content at field capacity / saturation in Pune Vertisols)
SOIL_SATURATION_CAPACITY = 0.45  # m³/m³


class WeatherFeatureService:
    """Computes meteorological features: Vapor Pressure Deficit (VPD), wind u/v components,

    soil moisture saturation index, and rolling antecedent precipitation.
    Strictly preserves isolation between OBSERVED reanalysis and FORECAST NWP tracks.
    """

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            self.project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../..")
            )
        else:
            self.project_root = project_root

        self.output_dir = os.path.join(self.project_root, "data", "features", "weather")
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def calculate_vpd_kpa(temp_c: float, rel_humidity_pct: float) -> float:
        """Calculates Vapor Pressure Deficit (VPD in kPa) using the Tetens formula."""
        if pd.isna(temp_c) or pd.isna(rel_humidity_pct):
            return np.nan
        # Saturation vapor pressure e_s in kPa
        e_s = 0.61078 * np.exp((17.27 * temp_c) / (temp_c + 237.3))
        # Actual vapor pressure e_a in kPa
        e_a = e_s * (rel_humidity_pct / 100.0)
        return float(max(0.0, e_s - e_a))

    @staticmethod
    def calculate_wind_components(wind_speed_kmh: float, wind_dir_deg: float) -> tuple[float, float]:
        """Decomposes meteorological wind speed (km/h) and direction (deg) into u (East) and v (North) m/s."""
        if pd.isna(wind_speed_kmh) or pd.isna(wind_dir_deg):
            return np.nan, np.nan
        speed_ms = wind_speed_kmh / 3.6
        rad = np.radians(wind_dir_deg)
        # In meteorology, direction is where wind is coming from:
        u = -speed_ms * np.sin(rad)
        v = -speed_ms * np.cos(rad)
        return float(round(u, 3)), float(round(v, 3))

    def generate_weather_features(self, db: Session) -> Dict[str, Any]:
        """Loads weather observations from database, engineers variables across

        OBSERVED and FORECAST tracks, and outputs Parquet and CSV files.
        """
        logger.info("Generating Open-Meteo weather and soil saturation features...")

        stmt = select(WeatherObservation).order_by(
            WeatherObservation.data_category.asc(),
            WeatherObservation.observation_time.asc(),
        )
        obs_list = db.execute(stmt).scalars().all()

        records: List[Dict[str, Any]] = []
        for o in obs_list:
            records.append({
                "observation_time": o.observation_time,
                "data_category": o.data_category,  # OBSERVED or FORECAST
                "location_name": o.location_name,
                "latitude": o.latitude,
                "longitude": o.longitude,
                "temperature_c": o.temperature,
                "relative_humidity_pct": o.relative_humidity,
                "precipitation_mm": o.precipitation or 0.0,
                "wind_speed_kmh": o.wind_speed,
                "wind_direction_deg": o.wind_direction,
                "soil_moisture_m3m3": o.soil_moisture,
                "quality_flag": o.quality_flag,
            })

        df = pd.DataFrame(records)
        df["observation_time"] = pd.to_datetime(df["observation_time"], utc=True)

        # Process each data category independently to avoid data leakage between forecast and historical
        processed_partitions = []

        for cat, part in df.groupby("data_category"):
            part = part.sort_values("observation_time").reset_index(drop=True)

            # 1. Vapor Pressure Deficit (VPD in kPa)
            part["vpd_kpa"] = part.apply(
                lambda r: self.calculate_vpd_kpa(r["temperature_c"], r["relative_humidity_pct"]),
                axis=1,
            ).round(3)

            # 2. Wind u (East) and v (North) components (m/s)
            wind_comps = part.apply(
                lambda r: self.calculate_wind_components(r["wind_speed_kmh"], r["wind_direction_deg"]),
                axis=1,
            )
            part["wind_u_ms"] = [c[0] for c in wind_comps]
            part["wind_v_ms"] = [c[1] for c in wind_comps]

            # 3. Soil Moisture Saturation Index (0.0 to 1.0)
            part["soil_saturation_index"] = (
                (part["soil_moisture_m3m3"] / SOIL_SATURATION_CAPACITY).clip(0.0, 1.0).round(3)
            )
            # Categorical saturation state
            sat_conditions = [
                part["soil_saturation_index"] >= 0.90,
                part["soil_saturation_index"] >= 0.75,
                part["soil_saturation_index"] >= 0.50,
            ]
            sat_labels = ["SATURATED", "HIGH_MOISTURE", "MODERATE_MOISTURE"]
            part["soil_saturation_state"] = np.select(
                sat_conditions, sat_labels, default="LOW_MOISTURE"
            )

            # 4. Rolling precipitation accumulation (hourly intervals)
            precip = part["precipitation_mm"].fillna(0.0)
            part["rolling_precip_3h_mm"] = precip.rolling(3, min_periods=1).sum().round(2)
            part["rolling_precip_6h_mm"] = precip.rolling(6, min_periods=1).sum().round(2)
            part["rolling_precip_12h_mm"] = precip.rolling(12, min_periods=1).sum().round(2)
            part["rolling_precip_24h_mm"] = precip.rolling(24, min_periods=1).sum().round(2)
            part["peak_hourly_intensity_24h_mmh"] = (
                precip.rolling(24, min_periods=1).max().round(2)
            )

            # 5. Potential Runoff Risk Multiplier:
            # Combination of soil saturation fraction and antecedent 6h rainfall
            part["runoff_risk_proxy"] = (
                part["soil_saturation_index"] * part["rolling_precip_6h_mm"]
            ).round(3)

            processed_partitions.append(part)

        featured_df = pd.concat(processed_partitions, ignore_index=True)
        featured_df = featured_df.sort_values(["data_category", "observation_time"]).reset_index(drop=True)

        # Output files
        csv_file = os.path.join(self.output_dir, "open_meteo_weather_features.csv")
        parquet_file = os.path.join(self.output_dir, "open_meteo_weather_features.parquet")

        df_export = featured_df.copy()
        df_export["observation_time"] = df_export["observation_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        df_export.to_csv(csv_file, index=False)
        featured_df.to_parquet(parquet_file, index=False, engine="pyarrow")

        logger.info(
            "Weather features generated: %d records -> %s, %s",
            len(featured_df),
            csv_file,
            parquet_file,
        )

        obs_count = int((featured_df["data_category"] == "OBSERVED").sum())
        fcst_count = int((featured_df["data_category"] == "FORECAST").sum())
        max_soil_sat = float(featured_df["soil_saturation_index"].max())
        peak_precip_24h = float(featured_df["rolling_precip_24h_mm"].max())

        return {
            "feature_set_name": "OPEN_METEO_WEATHER_FEATURES",
            "category": "WEATHER",
            "total_records": len(featured_df),
            "file_path_csv": csv_file,
            "file_path_parquet": parquet_file,
            "columns": list(featured_df.columns),
            "temporal_range": f"{df_export['observation_time'].min()} to {df_export['observation_time'].max()}",
            "spatial_domain": "Pune Urban Center (18.5204N, 73.8567E)",
            "summary_metrics": {
                "observed_records": obs_count,
                "forecast_records": fcst_count,
                "max_soil_saturation_index": max_soil_sat,
                "peak_24h_precipitation_mm": peak_precip_24h,
            },
            "quality_notes": (
                "Meteorological variables computed with physical formulas (Tetens VPD, u/v wind decomposition). "
                "Antecedent rainfall rolling accumulations calculated strictly within category partition. "
                "Contains separate OBSERVED (July 20-31, 2024 reanalysis) and FORECAST (7-day NWP) tracks. "
                "Soil moisture saturation index represents an assumed pedological reference proxy based on regional "
                "Deccan Vertisol (black cotton soil) field capacity (0.45 m³/m³), NOT in-situ measured ground saturation."
            ),
        }
