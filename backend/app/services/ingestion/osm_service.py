"""Ingestion service for OpenStreetMap infrastructure layers into PostGIS."""
import os
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
import geopandas as gpd
from geoalchemy2.shape import from_shape
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.spatial import SpatialFeature
from app.services.ingestion.base import BaseIngestionService

logger = logging.getLogger("floodx.ingestion.osm")

LAYER_MAPPING = {
    "waterways": "WATERWAY",
    "bridges": "BRIDGE",
    "healthcare_facilities": "HEALTHCARE",
    "education_facilities": "EDUCATION",
    "civic_and_community_facilities": "COMMUNITY_CIVIC",
    "evacuation_road_network": "EVACUATION_ROAD",
}


class OSMIngestionService(BaseIngestionService):
    """Ingests GeoPackage layers into spatial_features table with PostGIS geometries."""

    source_name = "OPENSTREETMAP_PUNE"
    source_type = "GIS_VECTOR"
    provider = "OpenStreetMap Contributors"
    description = (
        "Infrastructure layers (waterways, bridges, hospitals, schools, civic shelters, "
        "and evacuation road corridors) for the Pune / Mula-Mutha river basin."
    )
    data_format = "GeoPackage (GPKG)"
    units = "EPSG:4326 (WGS84)"
    temporal_resolution = "STATIC_LAYER"
    spatial_resolution = "VECTOR"

    def ingest(
        self,
        db: Session,
        gpkg_path: Optional[str] = None,
        batch_size: int = 1000,
    ) -> Dict[str, Any]:
        """Reads each layer from GeoPackage and populates spatial_features."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if gpkg_path is None:
            gpkg_path = os.path.join(
                project_root, "data", "processed", "gis", "osm_features_pune.gpkg"
            )

        metadata = {
            "coordinate_reference_system": "EPSG:4326",
            "layers": list(LAYER_MAPPING.keys()),
            "spatial_domain": "Pune / Mula-Mutha river basin",
        }

        source = self.get_or_create_source(db, metadata_json=metadata)
        log = self.start_log(db, source_id=source.id, file_name=os.path.basename(gpkg_path))

        if not os.path.exists(gpkg_path):
            err_msg = f"OSM GeoPackage not found: {gpkg_path}"
            logger.error(err_msg)
            self.finish_log(db, log, status="FAILED", records_read=0, records_inserted=0, records_skipped=0, records_failed=0, error_message=err_msg)
            return {"status": "FAILED", "error": err_msg}

        total_read = 0
        total_inserted = 0
        total_skipped = 0
        total_failed = 0
        layer_stats: Dict[str, int] = {}

        try:
            available_layers = gpd.list_layers(gpkg_path)["name"].tolist()

            for layer_name, feature_type in LAYER_MAPPING.items():
                if layer_name not in available_layers:
                    logger.warning("Layer %s not found in GPKG", layer_name)
                    continue

                gdf = gpd.read_file(gpkg_path, layer=layer_name)
                # Ensure CRS is EPSG:4326
                if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
                    gdf = gdf.to_crs(epsg=4326)

                layer_read = len(gdf)
                total_read += layer_read
                layer_stats[layer_name] = layer_read

                records_to_insert: List[Dict[str, Any]] = []

                for _, row in gdf.iterrows():
                    try:
                        geom = row.geometry
                        if geom is None or geom.is_empty:
                            continue

                        osm_id = str(row.get("osm_id", "")) if pd.notnull(row.get("osm_id")) else None
                        name = str(row.get("name", "")) if pd.notnull(row.get("name")) else None

                        # Clean properties dict
                        props = {}
                        for col, val in row.items():
                            if col not in ["geometry", "osm_id", "name"] and pd.notnull(val):
                                props[col] = str(val) if not isinstance(val, (int, float, bool)) else val

                        records_to_insert.append({
                            "source_id": source.id,
                            "feature_type": feature_type,
                            "osm_id": osm_id,
                            "name": name,
                            "properties_json": props,
                            "geom": from_shape(geom, srid=4326),
                        })
                    except Exception as feat_err:
                        logger.warning("Error processing feature in %s: %s", layer_name, feat_err)
                        total_failed += 1

                for i in range(0, len(records_to_insert), batch_size):
                    chunk = records_to_insert[i : i + batch_size]
                    stmt = pg_insert(SpatialFeature).values(chunk).on_conflict_do_nothing(
                        index_elements=["source_id", "feature_type", "osm_id"]
                    )
                    res = db.execute(stmt)
                    db.commit()
                    inserted_cnt = res.rowcount if res.rowcount >= 0 else len(chunk)
                    total_inserted += inserted_cnt
                    total_skipped += (len(chunk) - inserted_cnt)

            # Record Data Quality Issues
            self.record_quality_issue(
                db=db,
                source_id=source.id,
                issue_type="ARTERIAL_ROAD_NETWORK_ONLY",
                severity="MEDIUM",
                description=(
                    "Evacuation road network layer is filtered to arterial backbone (trunk, primary, "
                    "secondary, tertiary); local tertiary links and minor access lanes are omitted."
                ),
                affected_record_count=layer_stats.get("evacuation_road_network", 0),
            )

            self.record_quality_issue(
                db=db,
                source_id=source.id,
                issue_type="UNVERIFIED_SHELTER_CERTIFICATION",
                severity="MEDIUM",
                description=(
                    "Civic & community facilities include unverified community halls and sabhagruhas "
                    "not officially designated or certified by Pune Municipal Disaster Management authorities."
                ),
                affected_record_count=layer_stats.get("civic_and_community_facilities", 0),
            )

            status = "COMPLETED" if total_failed == 0 else "PARTIAL"
            self.finish_log(
                db,
                log,
                status=status,
                records_read=total_read,
                records_inserted=total_inserted,
                records_skipped=total_skipped,
                records_failed=total_failed,
                metadata_json={"layer_statistics": layer_stats},
            )

            return {
                "source": self.source_name,
                "status": status,
                "records_read": total_read,
                "records_inserted": total_inserted,
                "records_skipped": total_skipped,
                "records_failed": total_failed,
                "layers": layer_stats,
            }

        except Exception as exc:
            db.rollback()
            err_msg = f"OSM ingestion failed: {exc}"
            logger.exception(err_msg)
            self.finish_log(
                db,
                log,
                status="FAILED",
                records_read=total_read,
                records_inserted=total_inserted,
                records_skipped=total_skipped,
                records_failed=total_failed,
                error_message=err_msg,
            )
            return {"source": self.source_name, "status": "FAILED", "error": err_msg}
