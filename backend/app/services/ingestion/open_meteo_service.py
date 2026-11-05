"""Ingestion service for Open-Meteo numerical weather forecasts and historical reanalysis."""
import os
import json
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.observation import WeatherObservation
from app.services.ingestion.base import BaseIngestionService

logger = logging.getLogger("floodx.ingestion.open_meteo")
IST = ZoneInfo("Asia/Kolkata")


class OpenMeteoIngestionService(BaseIngestionService):
    """Ingests Open-Meteo forecast and reanalysis JSON datasets into weather_observations."""

    source_name = "OPEN_METEO"
    source_type = "NUMERICAL_WEATHER_PREDICTION"
    provider = "Open-Meteo ECMWF / DWD / GFS"
    description = (
        "Numerical weather prediction and reanalysis surface & soil parameters for Pune. "
        "Captures temperature, humidity, precipitation, wind speed/direction, and soil moisture."
    )
    data_format = "JSON"
    units = "°C, %, mm, km/h, degrees, m³/m³"
    temporal_resolution = "HOURLY"
    spatial_resolution = "POINT (18.5204N, 73.8567E)"

    def ingest(
        self,
        db: Session,
        forecast_path: Optional[str] = None,
        historical_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingests historical reanalysis and forecast weather datasets."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if forecast_path is None:
            forecast_path = os.path.join(
                project_root, "data", "raw", "weather", "open_meteo_forecast_pune.json"
            )
        if historical_path is None:
            historical_path = os.path.join(
                project_root, "data", "raw", "weather", "open_meteo_historical_202407_pune.json"
            )

        metadata = {
            "api_endpoint": "https://api.open-meteo.com/v1/forecast & archive",
            "pilot_latitude": 18.5204,
            "pilot_longitude": 73.8567,
            "timezone": "Asia/Kolkata",
            "utc_offset_seconds": 19800,
        }

        source = self.get_or_create_source(db, metadata_json=metadata)
        log = self.start_log(db, source_id=source.id, file_name="open_meteo_batch")

        files_to_process = [
            (historical_path, "OBSERVED"),
            (forecast_path, "FORECAST"),
        ]

        total_read = 0
        total_inserted = 0
        total_skipped = 0
        total_failed = 0

        for file_path, category in files_to_process:
            if not os.path.exists(file_path):
                logger.warning("Weather file not found: %s", file_path)
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                lat = float(data.get("latitude", 18.5204))
                lon = float(data.get("longitude", 73.8567))
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])

                temps = hourly.get("temperature_2m", [])
                humidities = hourly.get("relative_humidity_2m", [])
                precips = hourly.get("precipitation", [])
                winds = hourly.get("wind_speed_10m", [])
                dirs = hourly.get("wind_direction_10m", [])
                soils = hourly.get("soil_moisture_0_to_7cm", [])

                records_to_insert: List[Dict[str, Any]] = []

                for idx, t_str in enumerate(times):
                    try:
                        naive_dt = datetime.fromisoformat(t_str)
                        aware_dt = naive_dt.replace(tzinfo=IST).astimezone(timezone.utc)

                        temp_v = float(temps[idx]) if idx < len(temps) and temps[idx] is not None else None
                        hum_v = float(humidities[idx]) if idx < len(humidities) and humidities[idx] is not None else None
                        precip_v = float(precips[idx]) if idx < len(precips) and precips[idx] is not None else None
                        wind_v = float(winds[idx]) if idx < len(winds) and winds[idx] is not None else None
                        dir_v = float(dirs[idx]) if idx < len(dirs) and dirs[idx] is not None else None
                        soil_v = float(soils[idx]) if idx < len(soils) and soils[idx] is not None else None

                        # Quality check
                        flag = "VALID"
                        if temp_v is not None and (temp_v < -10 or temp_v > 60):
                            flag = "SUSPECT"
                        if precip_v is not None and precip_v < 0:
                            flag = "INVALID"
                            precip_v = 0.0

                        meta = {
                            "source_file": os.path.basename(file_path),
                        }
                        if "precipitation_probability" in hourly and idx < len(hourly["precipitation_probability"]):
                            meta["precip_prob_pct"] = hourly["precipitation_probability"][idx]
                        if "weather_code" in hourly and idx < len(hourly["weather_code"]):
                            meta["weather_code"] = hourly["weather_code"][idx]

                        records_to_insert.append({
                            "source_id": source.id,
                            "location_name": "Pune, Maharashtra",
                            "latitude": lat,
                            "longitude": lon,
                            "observation_time": aware_dt,
                            "data_category": category,
                            "temperature": temp_v,
                            "relative_humidity": hum_v,
                            "precipitation": precip_v,
                            "wind_speed": wind_v,
                            "wind_direction": dir_v,
                            "soil_moisture": soil_v,
                            "quality_flag": flag,
                            "metadata_json": meta,
                        })

                    except Exception as row_e:
                        logger.warning("Error parsing weather index %d: %s", idx, row_e)
                        total_failed += 1

                total_read += len(records_to_insert)

                if records_to_insert:
                    stmt = pg_insert(WeatherObservation).values(records_to_insert).on_conflict_do_nothing(
                        index_elements=["source_id", "location_name", "observation_time", "data_category"]
                    )
                    res = db.execute(stmt)
                    db.commit()
                    inserted_cnt = res.rowcount if res.rowcount >= 0 else len(records_to_insert)
                    total_inserted += inserted_cnt
                    total_skipped += (len(records_to_insert) - inserted_cnt)

            except Exception as file_e:
                db.rollback()
                logger.exception("Failed processing weather file %s: %s", file_path, file_e)
                total_failed += 1

        status = "COMPLETED" if total_failed == 0 else "PARTIAL"
        self.finish_log(
            db,
            log,
            status=status,
            records_read=total_read,
            records_inserted=total_inserted,
            records_skipped=total_skipped,
            records_failed=total_failed,
        )

        return {
            "source": self.source_name,
            "status": status,
            "records_read": total_read,
            "records_inserted": total_inserted,
            "records_skipped": total_skipped,
            "records_failed": total_failed,
        }
