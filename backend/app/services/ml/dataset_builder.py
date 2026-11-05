"""ML Training Dataset Construction Service for FLOOD-X Phase 2.2.

Constructs reproducible, leakage-free daily multi-variate hydrological datasets
combining 5-year continuous reanalysis weather with validated historical ground-truth labels.
"""

import os
import json
import logging
import hashlib
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd

from app.services.ml.label_validation import label_validation_service

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
RAW_WEATHER_JSON = os.path.join(PROJECT_ROOT, "data", "raw", "historical_weather", "open_meteo_pune_hourly_2020_2024.json")
OUTPUT_PARQUET = os.path.join(PROJECT_ROOT, "data", "processed", "ml", "daily_flood_training_dataset.parquet")
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "data", "processed", "ml", "daily_flood_training_dataset.csv")
METADATA_JSON = os.path.join(PROJECT_ROOT, "data", "metadata", "ml_daily_training_dataset_metadata.json")

VERTISOL_SATURATION_CAPACITY = 0.45  # m3/m3 proxy for Pune Black Cotton Vertisol


class DatasetBuilderService:
    """Builds and manages daily machine learning training datasets."""

    def __init__(self, weather_json_path: str = RAW_WEATHER_JSON):
        self.weather_json_path = weather_json_path

    def load_raw_hourly_weather(self) -> pd.DataFrame:
        """Load and parse Open-Meteo hourly weather time series."""
        if not os.path.exists(self.weather_json_path):
            raise FileNotFoundError(f"Weather dataset missing: {self.weather_json_path}")

        with open(self.weather_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        hourly = data.get("hourly", {})
        df = pd.DataFrame(hourly)
        df["time"] = pd.to_datetime(df["time"], utc=True)
        df.sort_values(by="time", inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Derived hourly physical variables: VPD using Tetens equation
        t = df["temperature_2m"].values
        rh = df["relative_humidity_2m"].values
        es = 0.61078 * np.exp((17.27 * t) / (t + 237.3))  # saturation vapor pressure (kPa)
        ea = es * (rh / 100.0)                             # actual vapor pressure (kPa)
        df["vpd_kpa"] = np.clip(es - ea, 0.0, None)

        # Wind vector decomposition
        ws = df["wind_speed_10m"].values
        wd_rad = np.radians(df["wind_direction_10m"].values)
        df["wind_u"] = -ws * np.sin(wd_rad)
        df["wind_v"] = -ws * np.cos(wd_rad)

        return df

    def construct_daily_dataset(self) -> pd.DataFrame:
        """Aggregate hourly time series into daily features with antecedent tracking and labels."""
        df_hourly = self.load_raw_hourly_weather()

        # Group by UTC date
        df_hourly["date_iso"] = df_hourly["time"].dt.strftime("%Y-%m-%d")

        # Compute hourly rolling precipitation windows before grouping
        df_hourly["precip_roll_3h"] = df_hourly["precipitation"].rolling(window=3, min_periods=1).sum()
        df_hourly["precip_roll_6h"] = df_hourly["precipitation"].rolling(window=6, min_periods=1).sum()
        df_hourly["precip_roll_12h"] = df_hourly["precipitation"].rolling(window=12, min_periods=1).sum()

        daily_groups = df_hourly.groupby("date_iso")

        daily_records = []
        for d_str, grp in daily_groups:
            precip = grp["precipitation"].values
            precip_total_24h = float(np.sum(precip))
            precip_max_1h = float(np.max(precip))
            precip_max_3h = float(np.max(grp["precip_roll_3h"].values))
            precip_max_6h = float(np.max(grp["precip_roll_6h"].values))
            precip_max_12h = float(np.max(grp["precip_roll_12h"].values))

            rainy_mask = precip > 0.1
            precip_intensity_mean = float(np.mean(precip[rainy_mask])) if np.any(rainy_mask) else 0.0

            t_mean = float(np.mean(grp["temperature_2m"].values))
            t_max = float(np.max(grp["temperature_2m"].values))
            t_min = float(np.min(grp["temperature_2m"].values))

            rh_mean = float(np.mean(grp["relative_humidity_2m"].values))
            rh_max = float(np.max(grp["relative_humidity_2m"].values))

            sp_mean = float(np.mean(grp["surface_pressure"].values))
            sp_min = float(np.min(grp["surface_pressure"].values))

            sm_0_7_mean = float(np.mean(grp["soil_moisture_0_to_7cm"].values))
            sm_0_7_max = float(np.max(grp["soil_moisture_0_to_7cm"].values))
            sm_7_28_mean = float(np.mean(grp["soil_moisture_7_to_28cm"].values))
            sm_7_28_max = float(np.max(grp["soil_moisture_7_to_28cm"].values))

            vpd_mean = float(np.mean(grp["vpd_kpa"].values))
            ws_max = float(np.max(grp["wind_speed_10m"].values))
            wind_u_mean = float(np.mean(grp["wind_u"].values))
            wind_v_mean = float(np.mean(grp["wind_v"].values))

            daily_records.append({
                "date_iso": d_str,
                "precip_total_24h": round(precip_total_24h, 3),
                "precip_max_1h": round(precip_max_1h, 3),
                "precip_max_3h": round(precip_max_3h, 3),
                "precip_max_6h": round(precip_max_6h, 3),
                "precip_max_12h": round(precip_max_12h, 3),
                "precip_intensity_mean": round(precip_intensity_mean, 3),
                "temp_2m_mean": round(t_mean, 2),
                "temp_2m_max": round(t_max, 2),
                "temp_2m_min": round(t_min, 2),
                "relative_humidity_mean": round(rh_mean, 2),
                "relative_humidity_max": round(rh_max, 2),
                "surface_pressure_mean": round(sp_mean, 2),
                "surface_pressure_min": round(sp_min, 2),
                "soil_moisture_0_7cm_mean": round(sm_0_7_mean, 4),
                "soil_moisture_0_7cm_max": round(sm_0_7_max, 4),
                "soil_moisture_7_28cm_mean": round(sm_7_28_mean, 4),
                "soil_moisture_7_28cm_max": round(sm_7_28_max, 4),
                "soil_saturation_ratio_0_7cm": round(min(sm_0_7_mean / VERTISOL_SATURATION_CAPACITY, 1.0), 4),
                "soil_saturation_ratio_7_28cm": round(min(sm_7_28_mean / VERTISOL_SATURATION_CAPACITY, 1.0), 4),
                "vpd_mean_kpa": round(vpd_mean, 4),
                "wind_speed_max": round(ws_max, 2),
                "wind_u_mean": round(wind_u_mean, 2),
                "wind_v_mean": round(wind_v_mean, 2),
            })

        df_daily = pd.DataFrame(daily_records)
        df_daily.sort_values(by="date_iso", inplace=True)
        df_daily.reset_index(drop=True, inplace=True)

        # Antecedent Precipitation Indices (API): Strict shift(1) to avoid data leakage!
        # Day T antecedent precipitation must ONLY sum up through Day T-1
        p_series = df_daily["precip_total_24h"]
        df_daily["antecedent_precip_3d"] = round(p_series.shift(1).rolling(window=3, min_periods=1).sum().fillna(0.0), 3)
        df_daily["antecedent_precip_7d"] = round(p_series.shift(1).rolling(window=7, min_periods=1).sum().fillna(0.0), 3)
        df_daily["antecedent_precip_14d"] = round(p_series.shift(1).rolling(window=14, min_periods=1).sum().fillna(0.0), 3)

        # 24-hour Surface Pressure Drop: pressure at T-1 minus pressure at T (positive indicates dropping pressure)
        sp_series = df_daily["surface_pressure_mean"]
        df_daily["pressure_drop_24h"] = round((sp_series.shift(1) - sp_series).fillna(0.0), 2)

        # Merge with Ground Truth Daily Labels
        df_labels = label_validation_service.get_validated_daily_labels()
        df_merged = df_daily.merge(df_labels, on="date_iso", how="inner")

        # Assign Strict Chronological Partitions
        # Train: 2020-01-01 to 2022-12-31 (3 years)
        # Validation: 2023-01-01 to 2023-12-31 (1 year)
        # Test: 2024-01-01 to 2024-12-31 (1 year - contains July 2024 benchmark!)
        def get_split(dt_str: str) -> str:
            year = int(dt_str[:4])
            if year in [2020, 2021, 2022]:
                return "train"
            elif year == 2023:
                return "validation"
            else:
                return "test"

        df_merged["split"] = df_merged["date_iso"].apply(get_split)

        # Save to processed directory
        os.makedirs(os.path.dirname(OUTPUT_PARQUET), exist_ok=True)
        df_merged.to_parquet(OUTPUT_PARQUET, index=False)
        df_merged.to_csv(OUTPUT_CSV, index=False)

        # Save metadata
        self._save_metadata(df_merged)

        logger.info(
            "Constructed daily ML dataset: %d rows, %d positive days. Saved to %s and %s",
            len(df_merged),
            (df_merged["flood_event_occurred"] == 1).sum(),
            OUTPUT_PARQUET,
            OUTPUT_CSV,
        )
        return df_merged

    def _save_metadata(self, df: pd.DataFrame) -> None:
        """Save cryptographic and statistical metadata for reproducibility."""
        os.makedirs(os.path.dirname(METADATA_JSON), exist_ok=True)

        # Parquet SHA-256
        h = hashlib.sha256()
        with open(OUTPUT_PARQUET, "rb") as pf:
            while chunk := pf.read(65536):
                h.update(chunk)
        parquet_sha = h.hexdigest()

        splits = df["split"].value_counts().to_dict()
        positive_by_split = df.groupby("split")["flood_event_occurred"].sum().to_dict()

        feature_cols = [
            "precip_total_24h", "precip_max_1h", "precip_max_3h", "precip_max_6h", "precip_max_12h",
            "precip_intensity_mean", "antecedent_precip_3d", "antecedent_precip_7d", "antecedent_precip_14d",
            "temp_2m_mean", "temp_2m_max", "temp_2m_min", "relative_humidity_mean", "relative_humidity_max",
            "surface_pressure_mean", "surface_pressure_min", "pressure_drop_24h",
            "soil_moisture_0_7cm_mean", "soil_moisture_0_7cm_max", "soil_moisture_7_28cm_mean", "soil_moisture_7_28cm_max",
            "soil_saturation_ratio_0_7cm", "soil_saturation_ratio_7_28cm",
            "vpd_mean_kpa", "wind_speed_max", "wind_u_mean", "wind_v_mean", "is_monsoon"
        ]

        meta = {
            "dataset_name": "FLOODX_PUNE_DAILY_FLOOD_ML_TRAINING_DATASET_V1",
            "temporal_range": {
                "start_date": df["date_iso"].min(),
                "end_date": df["date_iso"].max(),
                "total_days": len(df)
            },
            "partitions": {
                "train_days": splits.get("train", 0),
                "train_positive_days": int(positive_by_split.get("train", 0)),
                "validation_days": splits.get("validation", 0),
                "validation_positive_days": int(positive_by_split.get("validation", 0)),
                "test_days": splits.get("test", 0),
                "test_positive_days": int(positive_by_split.get("test", 0))
            },
            "feature_columns_count": len(feature_cols),
            "feature_columns": feature_cols,
            "target_column": "flood_event_occurred",
            "target_distribution": {
                "positive_days": int(df["flood_event_occurred"].sum()),
                "negative_days": int((df["flood_event_occurred"] == 0).sum()),
                "positive_rate_percent": round(float(df["flood_event_occurred"].mean() * 100), 3)
            },
            "file_parquet": OUTPUT_PARQUET,
            "parquet_sha256": parquet_sha,
            "file_csv": OUTPUT_CSV
        }

        with open(METADATA_JSON, "w", encoding="utf-8") as mf:
            json.dump(meta, mf, indent=2)


# Default singleton instance
dataset_builder_service = DatasetBuilderService()

