"""Ingestion service for CHIRPS v3 satellite rainfall observations."""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.observation import RainfallObservation
from app.services.ingestion.base import BaseIngestionService

logger = logging.getLogger("floodx.ingestion.chirps")


class CHIRPSIngestionService(BaseIngestionService):
    """Ingests CHIRPS v3 satellite rainfall time series and catalogs spatial raster products."""

    source_name = "CHIRPS_V3_RAINFALL"
    source_type = "SATELLITE_RAINFALL"
    provider = "UCSB Climate Hazards Center"
    description = (
        "CHIRPS v3 0.05-degree quasi-global precipitation dataset cropped to the Pune / "
        "Mula-Mutha river basin study area."
    )
    data_format = "CSV / GeoTIFF"
    units = "mm/day"
    temporal_resolution = "DAILY"
    spatial_resolution = "0.05 deg (~5.5km)"

    def ingest(
        self,
        db: Session,
        csv_path: Optional[str] = None,
        raster_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingests daily time series CSV and records catalog metadata."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if csv_path is None:
            csv_path = os.path.join(
                project_root,
                "data",
                "processed",
                "rainfall",
                "chirps_v3_pune_daily_2020_2024_timeseries.csv",
            )
        if raster_dir is None:
            raster_dir = os.path.join(project_root, "data", "processed", "rainfall")

        # Discover raster files for catalog
        raster_catalog = []
        if os.path.exists(raster_dir):
            for fname in os.listdir(raster_dir):
                if fname.endswith(".tif"):
                    raster_catalog.append({
                        "file_name": fname,
                        "path": os.path.relpath(os.path.join(raster_dir, fname), project_root).replace("\\", "/"),
                        "size_bytes": os.path.getsize(os.path.join(raster_dir, fname)),
                    })

        metadata = {
            "satellite_product": "CHIRPS v3.0",
            "spatial_coverage": "Pune / Mula-Mutha Study Boundary [18.25-18.75N, 73.35-74.30E]",
            "raster_catalog": raster_catalog,
        }

        source = self.get_or_create_source(db, metadata_json=metadata)
        log = self.start_log(db, source_id=source.id, file_name=os.path.basename(csv_path))

        if not os.path.exists(csv_path):
            err_msg = f"CHIRPS time series CSV not found: {csv_path}"
            logger.error(err_msg)
            self.finish_log(db, log, status="FAILED", records_read=0, records_inserted=0, records_skipped=0, records_failed=0, error_message=err_msg)
            return {"status": "FAILED", "error": err_msg}

        records_read = 0
        records_inserted = 0
        records_skipped = 0
        records_failed = 0

        try:
            df = pd.read_csv(csv_path)
            records_read = len(df)

            for _, row in df.iterrows():
                try:
                    # Parse date as UTC midnight
                    obs_date = datetime.strptime(str(row["date"]).strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    mean_val = float(row["mean_mm_day"])
                    max_val = float(row["max_mm_day"])
                    min_val = float(row["min_mm_day"])
                    p90_val = float(row["p90_mm_day"])
                    epoch = str(row.get("epoch", "monsoon_peak"))

                    # Check for existing observation
                    stmt = select(RainfallObservation).where(
                        RainfallObservation.source_id == source.id,
                        RainfallObservation.station_name == "CHIRPS_V3_PUNE_BASIN_AGGREGATE",
                        RainfallObservation.observation_time == obs_date,
                        RainfallObservation.measurement_type == "DAILY_ACCUMULATION",
                    )
                    existing = db.execute(stmt).scalar_one_or_none()

                    if existing:
                        existing.rainfall_value = mean_val
                        existing.metadata_json = {
                            "mean_mm_day": mean_val,
                            "max_mm_day": max_val,
                            "min_mm_day": min_val,
                            "p90_mm_day": p90_val,
                            "epoch": epoch,
                            "source_label": str(row.get("data_source", "CHIRPS v3")),
                        }
                        records_skipped += 1
                    else:
                        obs = RainfallObservation(
                            source_id=source.id,
                            station_name="CHIRPS_V3_PUNE_BASIN_AGGREGATE",
                            latitude=18.5204,
                            longitude=73.8567,
                            observation_time=obs_date,
                            rainfall_value=mean_val,
                            rainfall_unit="mm/day",
                            measurement_type="DAILY_ACCUMULATION",
                            quality_flag="VALID",
                            metadata_json={
                                "mean_mm_day": mean_val,
                                "max_mm_day": max_val,
                                "min_mm_day": min_val,
                                "p90_mm_day": p90_val,
                                "epoch": epoch,
                                "source_label": str(row.get("data_source", "CHIRPS v3")),
                            },
                        )
                        db.add(obs)
                        records_inserted += 1

                except Exception as row_err:
                    logger.warning("Error processing row %s: %s", row, row_err)
                    records_failed += 1

            db.commit()

            # Record Data Quality Issue for non-continuous sequence
            self.record_quality_issue(
                db=db,
                source_id=source.id,
                issue_type="TEMPORAL_RESOLUTION_LIMITATION",
                severity="LOW",
                description=(
                    "CHIRPS v3 dataset contains 25 targeted daily observations across 2020-2024 "
                    "monsoon peak epochs rather than a continuous 365-day time series."
                ),
                affected_record_count=records_read,
                metadata_json={"covered_dates": records_read, "max_single_day_mm": 344.0},
            )

            status = "COMPLETED" if records_failed == 0 else "PARTIAL"
            self.finish_log(
                db,
                log,
                status=status,
                records_read=records_read,
                records_inserted=records_inserted,
                records_skipped=records_skipped,
                records_failed=records_failed,
            )
            return {
                "source": self.source_name,
                "status": status,
                "records_read": records_read,
                "records_inserted": records_inserted,
                "records_skipped": records_skipped,
                "records_failed": records_failed,
            }

        except Exception as exc:
            db.rollback()
            err_msg = f"CHIRPS ingestion failed: {exc}"
            logger.exception(err_msg)
            self.finish_log(
                db,
                log,
                status="FAILED",
                records_read=records_read,
                records_inserted=records_inserted,
                records_skipped=records_skipped,
                records_failed=records_failed,
                error_message=err_msg,
            )
            return {"source": self.source_name, "status": "FAILED", "error": err_msg}

