"""Feature engineering pipeline orchestrator, cataloger, and manifest generator."""
import os
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.feature import FeatureDataset
from app.services.features.rainfall_features import RainfallFeatureService
from app.services.features.weather_features import WeatherFeatureService
from app.services.features.terrain_features import TerrainFeatureService
from app.services.features.geospatial_features import GeospatialFeatureService
from app.services.features.temporal_alignment import TemporalAlignmentService

logger = logging.getLogger("floodx.features.orchestrator")


def calculate_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class FeatureEngineeringOrchestrator:
    """Coordinates execution of all hydrological feature engineering pipelines,

    catalogs feature datasets into PostgreSQL, and writes the authoritative feature manifest.
    """

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            self.project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../..")
            )
        else:
            self.project_root = project_root

        self.metadata_dir = os.path.join(self.project_root, "data", "features", "metadata")
        os.makedirs(self.metadata_dir, exist_ok=True)

    def run_all(self, db: Session) -> Dict[str, Any]:
        """Runs the entire hydrological feature engineering suite."""
        logger.info("Starting Phase 1 Stage 3 Hydrological Feature Engineering Suite...")
        start_time = datetime.now(timezone.utc)

        results: List[Dict[str, Any]] = []

        rainfall_svc = RainfallFeatureService(self.project_root)
        weather_svc = WeatherFeatureService(self.project_root)
        terrain_svc = TerrainFeatureService(self.project_root)
        geo_svc = GeospatialFeatureService(self.project_root)
        temporal_svc = TemporalAlignmentService(self.project_root)

        # 1. CWPRS Rainfall Features
        try:
            cwprs_meta = rainfall_svc.generate_cwprs_features(db)
            self._catalog_dataset(db, cwprs_meta)
            results.append(cwprs_meta)
        except Exception as e:
            logger.error("Error generating CWPRS features: %s", e, exc_info=True)
            results.append({"feature_set_name": "CWPRS_RAINFALL_ROLLING_FEATURES", "error": str(e)})

        # 2. CHIRPS Daily Spatial Features
        try:
            chirps_meta = rainfall_svc.generate_chirps_features()
            self._catalog_dataset(db, chirps_meta)
            results.append(chirps_meta)
        except Exception as e:
            logger.error("Error generating CHIRPS features: %s", e, exc_info=True)
            results.append({"feature_set_name": "CHIRPS_DAILY_SPATIAL_FEATURES", "error": str(e)})

        # 3. Open-Meteo Weather Features
        try:
            weather_meta = weather_svc.generate_weather_features(db)
            self._catalog_dataset(db, weather_meta)
            results.append(weather_meta)
        except Exception as e:
            logger.error("Error generating Weather features: %s", e, exc_info=True)
            results.append({"feature_set_name": "OPEN_METEO_WEATHER_FEATURES", "error": str(e)})

        # 4. Copernicus GLO-90 Terrain Features
        try:
            terrain_meta = terrain_svc.generate_terrain_features()
            self._catalog_dataset(db, terrain_meta)
            results.append(terrain_meta)
        except Exception as e:
            logger.error("Error generating Terrain features: %s", e, exc_info=True)
            results.append({"feature_set_name": "COPERNICUS_TERRAIN_SAMPLED_FEATURES", "error": str(e)})

        # 5. PostGIS Infrastructure Proximity Features
        try:
            geo_meta = geo_svc.generate_geospatial_features(db)
            self._catalog_dataset(db, geo_meta)
            results.append(geo_meta)
        except Exception as e:
            logger.error("Error generating Geospatial features: %s", e, exc_info=True)
            results.append({"feature_set_name": "POSTGIS_INFRASTRUCTURE_PROXIMITY_FEATURES", "error": str(e)})

        # 6. Master Time-Aligned July 2024 Flood Sequence Features
        try:
            aligned_meta = temporal_svc.generate_aligned_features(db)
            self._catalog_dataset(db, aligned_meta)
            results.append(aligned_meta)
        except Exception as e:
            logger.error("Error generating Master Aligned features: %s", e, exc_info=True)
            results.append({"feature_set_name": "MULA_MUTHA_JULY2024_ALIGNED_FEATURES", "error": str(e)})

        # 7. Generate Master Feature Manifest
        manifest = self.generate_manifest(results)

        duration_sec = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(
            "Feature Engineering Suite completed in %.2f seconds (%d feature sets cataloged)",
            duration_sec,
            len([r for r in results if "error" not in r]),
        )

        return {
            "status": "COMPLETED",
            "duration_seconds": round(duration_sec, 2),
            "total_datasets": len(results),
            "datasets": results,
            "manifest_file": manifest.get("manifest_path"),
        }

    def _catalog_dataset(self, db: Session, meta: Dict[str, Any]) -> None:
        """Upserts metadata into feature_datasets table."""
        name = meta["feature_set_name"]
        stmt = select(FeatureDataset).where(FeatureDataset.feature_set_name == name)
        record = db.execute(stmt).scalar_one_or_none()

        csv_path = meta.get("file_path_csv")
        parquet_path = meta.get("file_path_parquet")

        # Compute provenance hashes
        csv_hash = calculate_sha256(csv_path) if csv_path and os.path.exists(csv_path) else None
        parquet_hash = calculate_sha256(parquet_path) if parquet_path and os.path.exists(parquet_path) else None

        provenance = {
            "csv_sha256": csv_hash,
            "parquet_sha256": parquet_hash,
            "csv_bytes": os.path.getsize(csv_path) if csv_path and os.path.exists(csv_path) else 0,
            "parquet_bytes": os.path.getsize(parquet_path) if parquet_path and os.path.exists(parquet_path) else 0,
            "summary_metrics": meta.get("summary_metrics", {}),
        }

        if record is None:
            record = FeatureDataset(
                feature_set_name=name,
                category=meta["category"],
                file_path_csv=csv_path,
                file_path_parquet=parquet_path,
                total_records=meta["total_records"],
                columns_json=meta.get("columns", []),
                temporal_range=meta.get("temporal_range"),
                spatial_domain=meta.get("spatial_domain"),
                quality_notes=meta.get("quality_notes"),
                provenance_manifest=provenance,
            )
            db.add(record)
        else:
            record.category = meta["category"]
            record.file_path_csv = csv_path
            record.file_path_parquet = parquet_path
            record.total_records = meta["total_records"]
            record.columns_json = meta.get("columns", [])
            record.temporal_range = meta.get("temporal_range")
            record.spatial_domain = meta.get("spatial_domain")
            record.quality_notes = meta.get("quality_notes")
            record.provenance_manifest = provenance

        db.commit()
        db.refresh(record)
        meta["provenance"] = provenance

    def generate_manifest(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Writes data/features/metadata/feature_manifest.json with full metadata & hashes."""
        manifest_path = os.path.join(self.metadata_dir, "feature_manifest.json")

        payload = {
            "manifest_version": "1.0.0",
            "phase": "PHASE_1",
            "stage": "STAGE_3_HYDROLOGICAL_FEATURE_ENGINEERING",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "region": "Pune / Mula-Mutha River Basin, Maharashtra, India",
            "total_datasets": len(datasets),
            "datasets": datasets,
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        logger.info("Saved master feature manifest: %s", manifest_path)
        payload["manifest_path"] = manifest_path
        return payload

