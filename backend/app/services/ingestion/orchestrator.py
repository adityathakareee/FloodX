"""Master Ingestion Orchestrator for FLOOD-X multi-source environmental pipelines."""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.models.data_source import DataSource
from app.models.observation import (
    RainfallObservation,
    WeatherObservation,
    RiverLevelObservation,
)
from app.models.spatial import SpatialFeature
from app.models.ingestion import DataIngestionLog, DataQualityIssue

from app.services.ingestion.chirps_service import CHIRPSIngestionService
from app.services.ingestion.cwprs_service import CWPRSIngestionService
from app.services.ingestion.open_meteo_service import OpenMeteoIngestionService
from app.services.ingestion.cwc_service import CWCIngestionService
from app.services.ingestion.osm_service import OSMIngestionService
from app.services.ingestion.elevation_service import ElevationCatalogService

logger = logging.getLogger("floodx.ingestion.orchestrator")


class IngestionOrchestrator:
    """Coordinates multi-source data ingestion, cataloging, and status monitoring."""

    def __init__(self):
        self.chirps_service = CHIRPSIngestionService()
        self.cwprs_service = CWPRSIngestionService()
        self.open_meteo_service = OpenMeteoIngestionService()
        self.cwc_service = CWCIngestionService()
        self.osm_service = OSMIngestionService()
        self.elevation_service = ElevationCatalogService()

    def run_source(self, db: Session, source_key: str, **kwargs) -> Dict[str, Any]:
        """Runs an individual data source ingestion pipeline."""
        key = source_key.lower().strip()
        if key in ["chirps", "chirps_v3", "chirps_v3_rainfall"]:
            return self.chirps_service.ingest(db, **kwargs)
        elif key in ["cwprs", "cwprs_khadakwasla"]:
            return self.cwprs_service.ingest(db, **kwargs)
        elif key in ["open_meteo", "openmeteo", "weather"]:
            return self.open_meteo_service.ingest(db, **kwargs)
        elif key in ["cwc", "cwc_telemetry", "river_levels"]:
            return self.cwc_service.ingest(db, **kwargs)
        elif key in ["osm", "openstreetmap", "gis"]:
            return self.osm_service.ingest(db, **kwargs)
        elif key in ["elevation", "dem", "copernicus"]:
            return self.elevation_service.ingest(db, **kwargs)
        else:
            raise ValueError(f"Unknown data source key: {source_key}")

    def run_all(self, db: Session, fast_mode: bool = False) -> Dict[str, Any]:
        """Executes full end-to-end ingestion pipeline for all environmental and spatial sources."""
        logger.info("Starting FLOOD-X full ingestion pipeline (fast_mode=%s)", fast_mode)
        results = {}

        # 1. Elevation raster cataloging
        try:
            results["elevation"] = self.elevation_service.ingest(db)
        except Exception as e:
            results["elevation"] = {"status": "FAILED", "error": str(e)}

        # 2. CHIRPS rainfall
        try:
            results["chirps"] = self.chirps_service.ingest(db)
        except Exception as e:
            results["chirps"] = {"status": "FAILED", "error": str(e)}

        # 3. CWPRS ground rainfall telemetry (optionally capped in fast_mode)
        try:
            max_r = 1000 if fast_mode else None
            results["cwprs"] = self.cwprs_service.ingest(db, max_rows=max_r)
        except Exception as e:
            results["cwprs"] = {"status": "FAILED", "error": str(e)}

        # 4. Open-Meteo weather
        try:
            results["open_meteo"] = self.open_meteo_service.ingest(db)
        except Exception as e:
            results["open_meteo"] = {"status": "FAILED", "error": str(e)}

        # 5. CWC river levels (optionally capped in fast_mode)
        try:
            max_r = 1000 if fast_mode else None
            results["cwc"] = self.cwc_service.ingest(db, max_rows=max_r)
        except Exception as e:
            results["cwc"] = {"status": "FAILED", "error": str(e)}

        # 6. OSM GIS vector features
        try:
            results["osm"] = self.osm_service.ingest(db)
        except Exception as e:
            results["osm"] = {"status": "FAILED", "error": str(e)}

        return {
            "pipeline": "FLOOD-X Phase 1 Stage 2 Ingestion Pipeline",
            "results": results,
            "overview": self.get_overview(db),
        }

    def get_overview(self, db: Session) -> Dict[str, Any]:
        """Generates statistical overview of all ingested tables, sources, and data quality issues."""
        sources_count = db.execute(select(func.count(DataSource.id))).scalar() or 0
        rainfall_count = db.execute(select(func.count(RainfallObservation.id))).scalar() or 0
        weather_count = db.execute(select(func.count(WeatherObservation.id))).scalar() or 0
        river_level_count = db.execute(select(func.count(RiverLevelObservation.id))).scalar() or 0
        spatial_count = db.execute(select(func.count(SpatialFeature.id))).scalar() or 0
        issues_count = db.execute(select(func.count(DataQualityIssue.id))).scalar() or 0
        logs_count = db.execute(select(func.count(DataIngestionLog.id))).scalar() or 0

        # Feature type breakdown
        spatial_breakdown = dict(
            db.execute(
                select(SpatialFeature.feature_type, func.count(SpatialFeature.id)).group_by(
                    SpatialFeature.feature_type
                )
            ).all()
        )

        # Measurement type breakdown for rainfall
        rainfall_breakdown = dict(
            db.execute(
                select(RainfallObservation.measurement_type, func.count(RainfallObservation.id)).group_by(
                    RainfallObservation.measurement_type
                )
            ).all()
        )

        # Weather category breakdown
        weather_breakdown = dict(
            db.execute(
                select(WeatherObservation.data_category, func.count(WeatherObservation.id)).group_by(
                    WeatherObservation.data_category
                )
            ).all()
        )

        # River level relevance breakdown
        river_breakdown = dict(
            db.execute(
                select(RiverLevelObservation.geographic_relevance, func.count(RiverLevelObservation.id)).group_by(
                    RiverLevelObservation.geographic_relevance
                )
            ).all()
        )

        # Recent logs
        recent_logs = (
            db.execute(
                select(DataIngestionLog)
                .order_by(desc(DataIngestionLog.started_at))
                .limit(5)
            )
            .scalars()
            .all()
        )

        # Active quality issues
        quality_issues = (
            db.execute(
                select(DataQualityIssue)
                .order_by(desc(DataQualityIssue.detected_at))
            )
            .scalars()
            .all()
        )

        return {
            "counts": {
                "data_sources": sources_count,
                "rainfall_observations": rainfall_count,
                "weather_observations": weather_count,
                "river_level_observations": river_level_count,
                "spatial_features": spatial_count,
                "data_quality_issues": issues_count,
                "ingestion_logs": logs_count,
            },
            "breakdowns": {
                "spatial_features": spatial_breakdown,
                "rainfall_observations": rainfall_breakdown,
                "weather_observations": weather_breakdown,
                "river_level_observations": river_breakdown,
            },
            "recent_logs": [
                {
                    "id": l.id,
                    "source_id": l.source_id,
                    "file_name": l.file_name,
                    "status": l.status,
                    "records_read": l.records_read,
                    "records_inserted": l.records_inserted,
                    "started_at": l.started_at.isoformat() if l.started_at else None,
                    "completed_at": l.completed_at.isoformat() if l.completed_at else None,
                }
                for l in recent_logs
            ],
            "quality_issues": [
                {
                    "id": q.id,
                    "source_id": q.source_id,
                    "issue_type": q.issue_type,
                    "severity": q.severity,
                    "description": q.description,
                    "affected_records": q.affected_record_count,
                }
                for q in quality_issues
            ],
        }

