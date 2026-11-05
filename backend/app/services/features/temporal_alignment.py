"""Temporal alignment service creating the Master Integrated Feature Table for July 2024 flood event."""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.observation import RainfallObservation, WeatherObservation

logger = logging.getLogger("floodx.features.temporal")

# Canonical July 2024 catastrophic flood observation window (UTC)
START_UTC = datetime(2024, 7, 20, 0, 0, tzinfo=timezone.utc)
END_UTC = datetime(2024, 7, 31, 23, 0, tzinfo=timezone.utc)


class TemporalAlignmentService:
    """Fuses multi-modal observations into an authoritative, time-aligned Master Feature Table

    covering the July 2024 Pune flood event in UTC.
    """

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            self.project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../..")
            )
        else:
            self.project_root = project_root

        self.output_dir = os.path.join(self.project_root, "data", "features", "integrated")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_aligned_features(self, db: Session) -> Dict[str, Any]:
        """Aligns CWPRS Khadakwasla ground telemetry, Open-Meteo reanalysis, and CHIRPS v3 satellite

        daily statistics for July 20 to July 31, 2024 (288 hourly intervals).
        """
        logger.info("Building Master Time-Aligned Feature Table (July 2024 flood sequence)...")

        # 1. Generate full continuous hourly grid: 288 hours
        hourly_index = pd.date_range(start=START_UTC, end=END_UTC, freq="1h", tz=timezone.utc)
        master_df = pd.DataFrame({"observation_time": hourly_index})
        master_df["hour_index"] = range(1, len(master_df) + 1)
        master_df["date_str"] = master_df["observation_time"].dt.strftime("%Y-%m-%d")
        master_df["hour_of_day_utc"] = master_df["observation_time"].dt.hour

        # 2. Extract and aggregate CWPRS 5-minute increments into hourly buckets
        logger.info("Aggregating CWPRS 5-minute telemetry into hourly feature intervals...")
        cwprs_stmt = (
            select(RainfallObservation)
            .where(
                RainfallObservation.station_name == "Khadakwasla (CWPRS)",
                RainfallObservation.measurement_type == "INCREMENTAL",
                RainfallObservation.observation_time >= START_UTC - timedelta(hours=24),  # Pre-fetch for rolling
                RainfallObservation.observation_time <= END_UTC + timedelta(hours=1),
            )
            .order_by(RainfallObservation.observation_time.asc())
        )
        cwprs_records = db.execute(cwprs_stmt).scalars().all()

        cwprs_data = []
        for c in cwprs_records:
            meta = c.metadata_json or {}
            cwprs_data.append({
                "time": c.observation_time,
                "increment_mm": c.rainfall_value,
                "raw_cumulative": meta.get("raw_cumulative_reading", np.nan),
                "is_reset": meta.get("is_reset", False),
            })
        c_df = pd.DataFrame(cwprs_data)

        hourly_cwprs: Dict[datetime, Dict[str, Any]] = {}
        if not c_df.empty:
            c_df["time"] = pd.to_datetime(c_df["time"], utc=True)
            c_df = c_df.sort_values("time").reset_index(drop=True)
            c_df["hour_bucket"] = c_df["time"].dt.floor("1h")

            # Group by hour bucket
            for h_bucket, group in c_df.groupby("hour_bucket"):
                h_bucket_dt = h_bucket.to_pydatetime()
                inc_sum = float(group["increment_mm"].sum())
                # Peak 5-min increment scaled to mm/hr
                peak_5m = float(group["increment_mm"].max()) * 12.0
                sample_count = len(group)
                is_reset_in_hour = bool(group["is_reset"].any())
                last_cum = float(group["raw_cumulative"].iloc[-1]) if not group["raw_cumulative"].isna().all() else np.nan

                hourly_cwprs[h_bucket_dt] = {
                    "cwprs_rainfall_1h_sum_mm": round(inc_sum, 2),
                    "cwprs_peak_5min_intensity_mmh": round(peak_5m, 2),
                    "cwprs_hourly_samples_count": sample_count,
                    "cwprs_hourly_completeness_fraction": round(min(1.0, sample_count / 12.0), 2),
                    "cwprs_is_reset_hour": is_reset_in_hour,
                    "cwprs_last_cumulative_reading_mm": last_cum,
                }

        # Map CWPRS features to master grid
        for col in [
            "cwprs_rainfall_1h_sum_mm",
            "cwprs_peak_5min_intensity_mmh",
            "cwprs_hourly_samples_count",
            "cwprs_hourly_completeness_fraction",
            "cwprs_is_reset_hour",
            "cwprs_last_cumulative_reading_mm",
        ]:
            master_df[col] = master_df["observation_time"].map(
                lambda t: hourly_cwprs.get(t.to_pydatetime(), {}).get(col, 0.0 if "sum" in col or "peak" in col else (False if "reset" in col else np.nan))
            )

        # Compute CWPRS antecedent rolling accumulations on hourly grid
        cwprs_h_series = master_df["cwprs_rainfall_1h_sum_mm"].fillna(0.0)
        master_df["cwprs_rolling_3h_mm"] = cwprs_h_series.rolling(3, min_periods=1).sum().round(2)
        master_df["cwprs_rolling_6h_mm"] = cwprs_h_series.rolling(6, min_periods=1).sum().round(2)
        master_df["cwprs_rolling_12h_mm"] = cwprs_h_series.rolling(12, min_periods=1).sum().round(2)
        master_df["cwprs_rolling_24h_mm"] = cwprs_h_series.rolling(24, min_periods=1).sum().round(2)

        # 3. Extract Open-Meteo Reanalysis (OBSERVED) for Pune
        logger.info("Extracting Open-Meteo reanalysis weather features...")
        w_stmt = (
            select(WeatherObservation)
            .where(
                WeatherObservation.data_category == "OBSERVED",
                WeatherObservation.observation_time >= START_UTC,
                WeatherObservation.observation_time <= END_UTC,
            )
            .order_by(WeatherObservation.observation_time.asc())
        )
        weather_records = db.execute(w_stmt).scalars().all()

        weather_map: Dict[datetime, Dict[str, Any]] = {}
        for w in weather_records:
            t = w.observation_time
            temp = w.temperature
            rh = w.relative_humidity
            # VPD
            vpd = np.nan
            if temp is not None and rh is not None:
                e_s = 0.61078 * np.exp((17.27 * temp) / (temp + 237.3))
                e_a = e_s * (rh / 100.0)
                vpd = max(0.0, e_s - e_a)

            # Wind u and v components
            u_ms, v_ms = np.nan, np.nan
            if w.wind_speed is not None and w.wind_direction is not None:
                spd_ms = w.wind_speed / 3.6
                rad = np.radians(w.wind_direction)
                u_ms = -spd_ms * np.sin(rad)
                v_ms = -spd_ms * np.cos(rad)

            # Soil Saturation Index
            soil_sat = np.nan
            if w.soil_moisture is not None:
                soil_sat = min(1.0, max(0.0, w.soil_moisture / 0.45))

            weather_map[t] = {
                "weather_temperature_c": temp,
                "weather_relative_humidity_pct": rh,
                "weather_vpd_kpa": round(float(vpd), 3) if not np.isnan(vpd) else np.nan,
                "weather_precipitation_mm": w.precipitation or 0.0,
                "weather_wind_speed_kmh": w.wind_speed,
                "weather_wind_u_ms": round(float(u_ms), 3) if not np.isnan(u_ms) else np.nan,
                "weather_wind_v_ms": round(float(v_ms), 3) if not np.isnan(v_ms) else np.nan,
                "weather_soil_moisture_m3m3": w.soil_moisture,
                "weather_soil_saturation_index": round(float(soil_sat), 3) if not np.isnan(soil_sat) else np.nan,
            }

        for col in [
            "weather_temperature_c",
            "weather_relative_humidity_pct",
            "weather_vpd_kpa",
            "weather_precipitation_mm",
            "weather_wind_speed_kmh",
            "weather_wind_u_ms",
            "weather_wind_v_ms",
            "weather_soil_moisture_m3m3",
            "weather_soil_saturation_index",
        ]:
            master_df[col] = master_df["observation_time"].map(
                lambda t: weather_map.get(t.to_pydatetime(), {}).get(col, np.nan)
            )

        # 4. Extract CHIRPS daily satellite statistics for July 2024 peak event
        logger.info("Mapping CHIRPS daily satellite peak statistics...")
        chirps_file = os.path.join(
            self.project_root,
            "data",
            "processed",
            "rainfall",
            "chirps_v3_pune_daily_2020_2024_timeseries.csv",
        )
        chirps_daily_map: Dict[str, Dict[str, Any]] = {}
        if os.path.exists(chirps_file):
            ch_df = pd.read_csv(chirps_file)
            for _, r in ch_df.iterrows():
                chirps_daily_map[str(r["date"])] = {
                    "chirps_basin_mean_mm_day": float(r["mean_mm_day"]),
                    "chirps_basin_max_mm_day": float(r["max_mm_day"]),
                    "chirps_basin_p90_mm_day": float(r["p90_mm_day"]),
                }

        master_df["has_chirps_daily"] = master_df["date_str"].isin(chirps_daily_map.keys())
        master_df["chirps_basin_mean_mm_day"] = master_df["date_str"].map(
            lambda d: chirps_daily_map.get(d, {}).get("chirps_basin_mean_mm_day", np.nan)
        )
        master_df["chirps_basin_max_mm_day"] = master_df["date_str"].map(
            lambda d: chirps_daily_map.get(d, {}).get("chirps_basin_max_mm_day", np.nan)
        )
        master_df["chirps_basin_p90_mm_day"] = master_df["date_str"].map(
            lambda d: chirps_daily_map.get(d, {}).get("chirps_basin_p90_mm_day", np.nan)
        )

        # 5. Hydrological and Decision Intelligence Flags
        # Local river stage is strictly marked unavailable due to Sangli geographic displacement
        master_df["local_river_gauge_available"] = False
        master_df["river_gauge_exclusion_reason"] = (
            "CWC Ankali Bridge is in Sangli (205.3 km south); excluded from local Pune river stage."
        )

        # Combined Hydrological Runoff Susceptibility Score:
        # Scale: [0.0 to 1.0], driven by soil saturation and antecedent 24-hr CWPRS rainfall
        master_df["runoff_susceptibility_score"] = (
            master_df["weather_soil_saturation_index"].fillna(0.7)
            * (master_df["cwprs_rolling_24h_mm"] / 100.0).clip(0.0, 1.0)
        ).round(3)

        # Cloudburst / Extreme Runoff Trigger Flag
        master_df["cloudburst_trigger_flag"] = (
            (master_df["cwprs_peak_5min_intensity_mmh"] >= 40.0)
            | (master_df["cwprs_rainfall_1h_sum_mm"] >= 25.0)
            | (master_df["chirps_basin_max_mm_day"] >= 250.0)
        ).fillna(False)

        # 6. Save to Parquet and CSV
        csv_file = os.path.join(self.output_dir, "mula_mutha_july2024_aligned_features.csv")
        parquet_file = os.path.join(self.output_dir, "mula_mutha_july2024_aligned_features.parquet")

        df_export = master_df.copy()
        df_export["observation_time"] = df_export["observation_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        df_export.to_csv(csv_file, index=False)
        master_df.to_parquet(parquet_file, index=False, engine="pyarrow")

        logger.info(
            "Master Aligned Features generated: %d hours -> %s, %s",
            len(master_df),
            csv_file,
            parquet_file,
        )

        peak_1h = float(master_df["cwprs_rainfall_1h_sum_mm"].max())
        peak_24h = float(master_df["cwprs_rolling_24h_mm"].max())
        cloudburst_hours = int(master_df["cloudburst_trigger_flag"].sum())
        chirps_covered_days = int(master_df[master_df["has_chirps_daily"]]["date_str"].nunique())

        return {
            "feature_set_name": "MULA_MUTHA_JULY2024_ALIGNED_FEATURES",
            "category": "INTEGRATED",
            "total_records": len(master_df),
            "file_path_csv": csv_file,
            "file_path_parquet": parquet_file,
            "columns": list(master_df.columns),
            "temporal_range": f"{START_UTC.isoformat()} to {END_UTC.isoformat()} (288 hours)",
            "spatial_domain": "Pune / Mula-Mutha River Basin (Khadakwasla Dam to Pune Core)",
            "summary_metrics": {
                "total_hours": len(master_df),
                "peak_1h_rainfall_mm": peak_1h,
                "peak_24h_rolling_rainfall_mm": peak_24h,
                "cloudburst_trigger_hours_count": cloudburst_hours,
                "chirps_covered_monsoon_days": chirps_covered_days,
            },
            "quality_notes": (
                "Authoritative master multi-modal table for July 20-31, 2024 Pune flood sequence. "
                "Fuses CWPRS Khadakwasla ground telemetry, Open-Meteo reanalysis, and CHIRPS v3 peak satellite stats. "
                "Local river gauge is explicitly flagged as unavailable (Sangli gauge excluded). "
                "All timestamps standardized to UTC. "
                "These multi-modal features provide environmental and meteorological predictors; "
                "they do NOT represent ground-truth observed flood occurrence labels or hydrodynamic inundation extents."
            ),
        }

