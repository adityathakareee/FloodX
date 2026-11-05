"""Ingestion service for CWC river level telemetry with strict regional reference categorization."""
import os
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.observation import RiverLevelObservation
from app.services.ingestion.base import BaseIngestionService

logger = logging.getLogger("floodx.ingestion.cwc")
IST = ZoneInfo("Asia/Kolkata")


class CWCIngestionService(BaseIngestionService):
    """Ingests CWC river water level telemetry, classifying Ankali Bridge (Sangli) as regional reference."""

    source_name = "CWC_TELEMETRY"
    source_type = "RIVER_LEVEL_TELEMETRY"
    provider = "Central Water Commission / WRIS"
    description = (
        "Hydrological river water level telemetry from Central Water Commission (CWC). "
        "Ankali Bridge on Krishna River (Sangli) is maintained as regional reference baseline."
    )
    data_format = "CSV"
    units = "meters (MSL)"
    temporal_resolution = "15-MINUTE / HOURLY"
    spatial_resolution = "POINT (16.8028N, 74.5664E)"

    def ingest(
        self,
        db: Session,
        csv_path: Optional[str] = None,
        batch_size: int = 1000,
        max_rows: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Ingests river water level telemetry into river_level_observations."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if csv_path is None:
            csv_path = os.path.join(
                project_root,
                "data",
                "raw",
                "river_levels",
                "rwl_tel_hr_maharashtra_sw_007_sample.csv",
            )

        metadata = {
            "station_id": "MAHARASHTRA_SW_007",
            "station_name": "Ankali Bridge (Sangli)",
            "river_name": "Krishna",
            "district": "Sangli",
            "geographic_distance_to_pune_km": 205.3,
            "relevance_guidance": "REGIONAL_REFERENCE_ONLY. Do not trigger local Pune alerts.",
            "rl_of_zero_gauge": 520.0,
            "mean_sea_level_datum": "MSL",
        }

        source = self.get_or_create_source(db, metadata_json=metadata)
        log = self.start_log(db, source_id=source.id, file_name=os.path.basename(csv_path))

        if not os.path.exists(csv_path):
            err_msg = f"CWC river level CSV not found: {csv_path}"
            logger.error(err_msg)
            self.finish_log(db, log, status="FAILED", records_read=0, records_inserted=0, records_skipped=0, records_failed=0, error_message=err_msg)
            return {"status": "FAILED", "error": err_msg}

        try:
            df = pd.read_csv(csv_path)
            level_col = "River Water Level Telemetry Hourly (meter)"
            initial_count = len(df)
            df = df.dropna(subset=["Data Acquisition Time", level_col])
            dropped_nulls = initial_count - len(df)

            if max_rows:
                df = df.head(max_rows)
            records_read = len(df)

            df["parsed_dt"] = pd.to_datetime(df["Data Acquisition Time"], format="%d-%m-%Y %H:%M")
            df = df.sort_values("parsed_dt").reset_index(drop=True)

            station_name = "Ankali Bridge (Sangli)"
            river_name = "Krishna"
            lat = 16.8028
            lon = 74.5664

            records_to_insert: List[Dict[str, Any]] = []

            for _, row in df.iterrows():
                naive_dt = row["parsed_dt"]
                aware_dt = naive_dt.replace(tzinfo=IST).astimezone(timezone.utc)
                raw_level = float(row[level_col])

                q_flag = "VALID"
                if raw_level < 400 or raw_level > 700:
                    q_flag = "SUSPECT"

                records_to_insert.append({
                    "source_id": source.id,
                    "station_name": station_name,
                    "river_name": river_name,
                    "station_code": "SW_007",
                    "latitude": lat,
                    "longitude": lon,
                    "observation_time": aware_dt,
                    "water_level": raw_level,
                    "level_unit": "m",
                    "vertical_datum": "MSL",
                    "geographic_relevance": "REGIONAL_REFERENCE_ONLY",
                    "quality_flag": q_flag,
                    "metadata_json": {
                        "district": "Sangli",
                        "distance_to_pune_km": 205.3,
                        "raw_column": level_col,
                    },
                })

            total_inserted = 0
            for i in range(0, len(records_to_insert), batch_size):
                chunk = records_to_insert[i : i + batch_size]
                stmt = pg_insert(RiverLevelObservation).values(chunk).on_conflict_do_nothing(
                    index_elements=["source_id", "station_name", "observation_time"]
                )
                res = db.execute(stmt)
                db.commit()
                inserted_cnt = res.rowcount if res.rowcount >= 0 else len(chunk)
                total_inserted += inserted_cnt

            records_skipped = len(records_to_insert) - total_inserted

            # Record Data Quality Issue for geographic displacement
            self.record_quality_issue(
                db=db,
                source_id=source.id,
                issue_type="GEOGRAPHIC_DISPLACEMENT",
                severity="HIGH",
                description=(
                    "Station Ankali Bridge is in Sangli district on the Krishna River (205.3 km south of Pune). "
                    "Assigned classification REGIONAL_REFERENCE_ONLY; must not be assimilated into Pune Mula-Mutha "
                    "hydrological models as local river stage."
                ),
                affected_record_count=records_read,
                metadata_json={
                    "station_name": station_name,
                    "distance_km": 205.3,
                    "river": river_name,
                    "classification": "REGIONAL_REFERENCE_ONLY",
                },
            )

            if dropped_nulls > 0:
                self.record_quality_issue(
                    db=db,
                    source_id=source.id,
                    issue_type="NULL_TELEMETRY_RECORDS",
                    severity="LOW",
                    description=f"Filtered out {dropped_nulls} malformed row(s) with missing timestamp or water level.",
                    affected_record_count=dropped_nulls,
                )

            self.finish_log(
                db,
                log,
                status="COMPLETED",
                records_read=records_read,
                records_inserted=total_inserted,
                records_skipped=records_skipped,
                records_failed=0,
                metadata_json={"geographic_relevance": "REGIONAL_REFERENCE_ONLY", "sample_count": records_read},
            )

            return {
                "source": self.source_name,
                "status": "COMPLETED",
                "records_read": records_read,
                "records_inserted": total_inserted,
                "records_skipped": records_skipped,
                "records_failed": 0,
            }

        except Exception as exc:
            db.rollback()
            err_msg = f"CWC ingestion failed: {exc}"
            logger.exception(err_msg)
            self.finish_log(
                db,
                log,
                status="FAILED",
                records_read=0,
                records_inserted=0,
                records_skipped=0,
                records_failed=0,
                error_message=err_msg,
            )
            return {"source": self.source_name, "status": "FAILED", "error": err_msg}
