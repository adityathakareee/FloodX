"""Hydrological feature engineering service for rainfall telemetry and satellite observations."""
import os
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.observation import RainfallObservation
from app.models.data_source import DataSource

logger = logging.getLogger("floodx.features.rainfall")
IST = ZoneInfo("Asia/Kolkata")

# Rolling window definitions: (window_name, window_steps_5min, duration_hours)
ROLLING_WINDOWS = [
    ("15m", 3, 0.25),
    ("30m", 6, 0.5),
    ("1h", 12, 1.0),
    ("3h", 36, 3.0),
    ("6h", 72, 6.0),
    ("12h", 144, 12.0),
    ("24h", 288, 24.0),
]


class RainfallFeatureService:
    """Computes rolling accumulation, multi-scale intensity, incomplete window flags,

    and spatial satellite statistics for flood forecasting and hydrological modeling.
    """

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            self.project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../..")
            )
        else:
            self.project_root = project_root

        self.output_dir = os.path.join(self.project_root, "data", "features", "rainfall")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_cwprs_features(self, db: Session) -> Dict[str, Any]:
        """Loads CWPRS Khadakwasla 5-minute incremental rainfall observations from DB,

        computes rolling sums (15m, 30m, 1h, 3h, 6h, 12h, 24h), rolling intensity stats,
        and incomplete window tracking. Saves to Parquet and CSV.
        """
        logger.info("Generating CWPRS rolling rainfall features...")

        # 1. Query INCREMENTAL observations
        stmt = (
            select(RainfallObservation)
            .where(
                RainfallObservation.station_name == "Khadakwasla (CWPRS)",
                RainfallObservation.measurement_type == "INCREMENTAL",
            )
            .order_by(RainfallObservation.observation_time.asc())
        )
        obs_list = db.execute(stmt).scalars().all()

        if not obs_list:
            # Fallback to loading directly from processed/raw sample if DB not populated
            csv_path = os.path.join(
                self.project_root,
                "data",
                "raw",
                "rainfall",
                "rainfall_tel_hr_cwprs_mh_sample.csv",
            )
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"Neither DB records nor raw file found: {csv_path}")
            logger.info("Loading directly from raw CWPRS CSV: %s", csv_path)
            raw_df = pd.read_csv(csv_path)
            raw_df["parsed_dt"] = pd.to_datetime(
                raw_df["Data Acquisition Time"], format="%d-%m-%Y %H:%M"
            )
            raw_df = raw_df.sort_values("parsed_dt").reset_index(drop=True)
            # Reconstruct increments
            data = []
            prev_v = None
            for _, r in raw_df.iterrows():
                naive_dt = r["parsed_dt"]
                utc_dt = naive_dt.replace(tzinfo=IST).astimezone(timezone.utc)
                v = float(r["Telemetry Hourly Rainfall (mm)"])
                if prev_v is None or v < prev_v:
                    inc = v
                    is_rst = prev_v is not None and v < prev_v
                else:
                    inc = round(v - prev_v, 4)
                    is_rst = False
                prev_v = v
                data.append({
                    "observation_time": utc_dt,
                    "rainfall_value": max(0.0, inc),
                    "raw_cumulative": v,
                    "is_reset": is_rst,
                })
            df = pd.DataFrame(data)
        else:
            records = []
            for o in obs_list:
                meta = o.metadata_json or {}
                records.append({
                    "observation_time": o.observation_time,
                    "rainfall_value": o.rainfall_value,
                    "raw_cumulative": meta.get("raw_cumulative_reading", np.nan),
                    "is_reset": meta.get("is_reset", False),
                    "quality_flag": o.quality_flag,
                })
            df = pd.DataFrame(records)

        df["observation_time"] = pd.to_datetime(df["observation_time"], utc=True)
        df = df.sort_values("observation_time").reset_index(drop=True)

        # Timestamps in IST for local reporting & 08:30 reset alignment
        df["observation_time_ist"] = df["observation_time"].dt.tz_convert(IST).dt.strftime("%Y-%m-%d %H:%M:%S+05:30")
        df["station_name"] = "Khadakwasla (CWPRS)"
        df["latitude"] = 18.4419
        df["longitude"] = 73.7661
        df["increment_mm"] = df["rainfall_value"].astype(float)

        # 2. Check sampling intervals and gaps
        time_diff_mins = df["observation_time"].diff().dt.total_seconds() / 60.0
        df["step_gap_minutes"] = time_diff_mins.fillna(5.0)

        # 3. Compute rolling features for each defined window
        for w_name, w_steps, dur_hours in ROLLING_WINDOWS:
            # Rolling window sum, mean, max, std
            r_window = df["increment_mm"].rolling(w_steps, min_periods=1)
            sum_col = f"rolling_sum_{w_name}_mm"
            mean_col = f"rolling_mean_{w_name}_mm"
            max_col = f"rolling_max_{w_name}_mm"
            std_col = f"rolling_std_{w_name}_mm"
            intensity_col = f"intensity_{w_name}_mmh"
            status_col = f"window_status_{w_name}"
            completeness_col = f"completeness_{w_name}_frac"

            df[sum_col] = r_window.sum().round(3)
            df[mean_col] = r_window.mean().round(3)
            df[max_col] = r_window.max().round(3)
            df[std_col] = r_window.std().fillna(0.0).round(3)
            # Intensity in mm/h = rolling_sum / duration_hours
            df[intensity_col] = (df[sum_col] / dur_hours).round(3)

            # Incomplete window tracking:
            # 1. Number of rows in rolling window
            actual_count = r_window.count()
            row_frac = (actual_count / float(w_steps)).clip(upper=1.0)

            # 2. Wall-clock elapsed duration across preceding w_steps
            # Flags gaps whenever telemetry dropouts occur within the window
            time_span_sec = (df["observation_time"] - df["observation_time"].shift(w_steps - 1)).dt.total_seconds()
            expected_sec = dur_hours * 3600.0
            time_frac = np.where(
                time_span_sec > 0,
                np.minimum(1.0, expected_sec / np.maximum(expected_sec, time_span_sec)),
                row_frac,
            )
            # Joint completeness fraction: minimum of available rows and elapsed continuity
            joint_frac = np.minimum(row_frac, time_frac).round(3)
            df[completeness_col] = joint_frac
            # Flag INCOMPLETE if completeness < 0.8 (at start of series or across telemetry dropouts)
            df[status_col] = np.where(joint_frac >= 0.8, "COMPLETE", "INCOMPLETE")

        # 4. Save to Parquet and CSV
        csv_file = os.path.join(self.output_dir, "cwprs_rainfall_features.csv")
        parquet_file = os.path.join(self.output_dir, "cwprs_rainfall_features.parquet")

        # Format observation_time as ISO 8601 string for CSV clarity
        df_export = df.copy()
        df_export["observation_time"] = df_export["observation_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        df_export.to_csv(csv_file, index=False)
        df.to_parquet(parquet_file, index=False, engine="pyarrow")

        logger.info(
            "CWPRS features generated: %d records -> %s, %s",
            len(df),
            csv_file,
            parquet_file,
        )

        # Summary statistics
        peak_1h = float(df["intensity_1h_mmh"].max())
        peak_24h_sum = float(df["rolling_sum_24h_mm"].max())
        total_resets = int(df["is_reset"].sum()) if "is_reset" in df else 0

        return {
            "feature_set_name": "CWPRS_RAINFALL_ROLLING_FEATURES",
            "category": "RAINFALL",
            "total_records": len(df),
            "file_path_csv": csv_file,
            "file_path_parquet": parquet_file,
            "columns": list(df.columns),
            "temporal_range": f"{df_export['observation_time'].iloc[0]} to {df_export['observation_time'].iloc[-1]}",
            "spatial_domain": "Khadakwasla Dam, Pune (18.4419N, 73.7661E)",
            "summary_metrics": {
                "peak_1h_intensity_mmh": peak_1h,
                "peak_24h_accumulation_mm": peak_24h_sum,
                "detected_resets": total_resets,
                "rolling_windows": [w[0] for w in ROLLING_WINDOWS],
            },
            "quality_notes": (
                "Rolling sums and intensity metrics computed on derived 5-minute incremental rainfall. "
                "Daily 08:30 IST bucket resets are isolated; cumulative bucket peaks (e.g. 145.6 mm) are preserved. "
                "Incomplete windows flagged when completeness fraction < 0.8."
            ),
        }

    def generate_chirps_features(self) -> Dict[str, Any]:
        """Loads CHIRPS v3 daily peak monsoon time series, computes basin spatial statistics,

        spatial variability, and extreme event classifications across 2020-2024.
        """
        logger.info("Generating CHIRPS v3 spatial daily rainfall features...")

        csv_source = os.path.join(
            self.project_root,
            "data",
            "processed",
            "rainfall",
            "chirps_v3_pune_daily_2020_2024_timeseries.csv",
        )
        if not os.path.exists(csv_source):
            raise FileNotFoundError(f"CHIRPS source CSV not found: {csv_source}")

        df = pd.read_csv(csv_source)

        # Derived spatial and hydrological metrics
        df["spatial_range_mm"] = (df["max_mm_day"] - df["min_mm_day"]).round(2)
        # Ratio of 90th percentile to basin mean (indicator of localized cloudburst concentration)
        df["p90_to_mean_ratio"] = (df["p90_mm_day"] / df["mean_mm_day"].replace(0, np.nan)).round(2)
        # Coefficient of spatial variation proxy: (p90 - mean) / mean
        df["spatial_concentration_index"] = (
            (df["p90_mm_day"] - df["mean_mm_day"]) / df["mean_mm_day"].replace(0, np.nan)
        ).round(2).fillna(0.0)

        # Event severity categorization (IMD monsoon intensity thresholds)
        conditions = [
            (df["mean_mm_day"] >= 100.0) | (df["max_mm_day"] >= 300.0),
            (df["mean_mm_day"] >= 64.5) | (df["max_mm_day"] >= 200.0),
            (df["mean_mm_day"] >= 35.5) | (df["max_mm_day"] >= 100.0),
            (df["mean_mm_day"] >= 15.6),
        ]
        choices = [
            "EXTREMELY_HEAVY_RAINFALL",
            "VERY_HEAVY_RAINFALL",
            "HEAVY_RAINFALL",
            "MODERATE_RAINFALL",
        ]
        df["imd_severity_category"] = np.select(conditions, choices, default="LIGHT_RAINFALL")
        df["is_cloudburst_epoch"] = (df["max_mm_day"] >= 200.0).astype(bool)

        # Save to Parquet and CSV
        csv_file = os.path.join(self.output_dir, "chirps_daily_features.csv")
        parquet_file = os.path.join(self.output_dir, "chirps_daily_features.parquet")

        df.to_csv(csv_file, index=False)
        df.to_parquet(parquet_file, index=False, engine="pyarrow")

        logger.info(
            "CHIRPS features generated: %d records -> %s, %s",
            len(df),
            csv_file,
            parquet_file,
        )

        return {
            "feature_set_name": "CHIRPS_DAILY_SPATIAL_FEATURES",
            "category": "RAINFALL",
            "total_records": len(df),
            "file_path_csv": csv_file,
            "file_path_parquet": parquet_file,
            "columns": list(df.columns),
            "temporal_range": f"{df['date'].min()} to {df['date'].max()} (25 targeted peak monsoon dates)",
            "spatial_domain": "Pune / Mula-Mutha River Basin (73.30E to 74.25E, 18.20N to 18.80N)",
            "summary_metrics": {
                "max_single_cell_rainfall_mm": float(df["max_mm_day"].max()),
                "max_basin_mean_rainfall_mm": float(df["mean_mm_day"].max()),
                "peak_date": str(df.loc[df["max_mm_day"].idxmax(), "date"]),
                "cloudburst_epochs_count": int(df["is_cloudburst_epoch"].sum()),
            },
            "quality_notes": (
                "Captures 25 authoritative peak monsoon dates across 2020-2024. "
                "CHIRPS v3 satellite observations at 0.05° (~5.5 km) resolution. "
                "Dataset represents targeted flood epochs, NOT a continuous 365-day time series."
            ),
        }

