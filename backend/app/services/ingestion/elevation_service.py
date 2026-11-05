"""Ingestion and metadata catalog service for Copernicus GLO-90 DEM and slope rasters."""
import os
import logging
from typing import Optional, Dict, Any, List
import rasterio
import numpy as np
from sqlalchemy.orm import Session

from app.services.ingestion.base import BaseIngestionService

logger = logging.getLogger("floodx.ingestion.elevation")


class ElevationCatalogService(BaseIngestionService):
    """Catalogs Copernicus GLO-90 DEM and slope rasters, extracting spatial extent and statistics."""

    source_name = "COPERNICUS_GLO90_DEM"
    source_type = "RASTER_ELEVATION"
    provider = "Copernicus / European Space Agency (ESA)"
    description = (
        "Copernicus GLO-90 Digital Surface Model (DSM) and derived topographical slope raster "
        "cropped to the Pune / Mula-Mutha river basin study area."
    )
    data_format = "GeoTIFF (Cloud-Optimized GeoTIFF)"
    units = "Meters above MSL / Slope degrees"
    temporal_resolution = "STATIC_SURFACE"
    spatial_resolution = "90m (3 arc-seconds)"

    def ingest(
        self,
        db: Session,
        elevation_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Catalogs elevation and slope rasters, updating DataSource metadata."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if elevation_dir is None:
            elevation_dir = os.path.join(project_root, "data", "processed", "elevation")

        raster_catalog: List[Dict[str, Any]] = []
        dem_file = os.path.join(elevation_dir, "copernicus_glo90_pune_basin_dem.tif")
        slope_file = os.path.join(elevation_dir, "copernicus_glo90_pune_basin_slope.tif")

        targets = [
            ("copernicus_glo90_pune_basin_dem.tif", dem_file, "ELEVATION_MASL"),
            ("copernicus_glo90_pune_basin_slope.tif", slope_file, "SLOPE_DEGREES"),
        ]

        for fname, fpath, metric in targets:
            if not os.path.exists(fpath):
                logger.warning("Raster not found: %s", fpath)
                continue

            try:
                with rasterio.open(fpath) as src:
                    arr = src.read(1)
                    nodata = src.nodata
                    valid_mask = (arr != nodata) if nodata is not None else np.ones_like(arr, dtype=bool)
                    valid_vals = arr[valid_mask]

                    min_v = float(valid_vals.min()) if len(valid_vals) > 0 else 0.0
                    max_v = float(valid_vals.max()) if len(valid_vals) > 0 else 0.0
                    mean_v = float(valid_vals.mean()) if len(valid_vals) > 0 else 0.0

                    raster_catalog.append({
                        "file_name": fname,
                        "relative_path": os.path.relpath(fpath, project_root).replace("\\", "/"),
                        "metric": metric,
                        "crs": str(src.crs),
                        "bounds": {
                            "left": src.bounds.left,
                            "bottom": src.bounds.bottom,
                            "right": src.bounds.right,
                            "top": src.bounds.top,
                        },
                        "dimensions": {"width": src.width, "height": src.height},
                        "resolution_deg": [src.res[0], src.res[1]],
                        "statistics": {
                            "min": round(min_v, 2),
                            "max": round(max_v, 2),
                            "mean": round(mean_v, 2),
                        },
                        "size_bytes": os.path.getsize(fpath),
                    })
            except Exception as r_err:
                logger.warning("Error reading raster %s: %s", fname, r_err)

        metadata = {
            "model_type": "Digital Surface Model (DSM)",
            "coverage_area": "Pune / Mula-Mutha River Basin",
            "rasters": raster_catalog,
        }

        source = self.get_or_create_source(db, metadata_json=metadata)
        log = self.start_log(db, source_id=source.id, file_name="elevation_catalog", ingestion_type="RASTER_CATALOG")

        # Record Data Quality Issue for DSM surface bias
        self.record_quality_issue(
            db=db,
            source_id=source.id,
            issue_type="DIGITAL_SURFACE_MODEL_BIAS",
            severity="LOW",
            description=(
                "Copernicus GLO-90 represents a Digital Surface Model (DSM) capturing canopy top "
                "and tall urban building elevations rather than a bare-earth Digital Terrain Model (DTM)."
            ),
            affected_record_count=len(raster_catalog),
            metadata_json={"product": "GLO-90 DSM", "resolution": "90m"},
        )

        self.finish_log(
            db,
            log,
            status="COMPLETED",
            records_read=len(targets),
            records_inserted=len(raster_catalog),
            records_skipped=0,
            records_failed=len(targets) - len(raster_catalog),
            metadata_json={"catalog_count": len(raster_catalog)},
        )

        return {
            "source": self.source_name,
            "status": "COMPLETED",
            "rasters_cataloged": len(raster_catalog),
            "catalog": raster_catalog,
        }

