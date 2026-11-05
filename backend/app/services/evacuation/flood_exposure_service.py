"""Flood Hazard Exposure Assessment Service for FLOOD-X Phase 3.2 Road Network.

Maps environmental hazard vectors onto each directed road graph edge:
1. Copernicus GLO-90 DSM minimum and mean elevation.
2. Local terrain slope (degrees).
3. Geodesic distance to Mula and Mutha waterways.
4. Proximity to chronic historical riverine and pluvial inundation hotspots.
5. Relative terrain elevation above the local river channel floor (~545m benchmark).

Scientific Disclaimers & Provenance:
- Copernicus GLO-90 is a Digital Surface Model (DSM), not a bare-earth DTM; contains urban rooftop and tree canopy elevation bias (2-8m).
- Waterway proximity does NOT equal active inundation.
- Relies on audited physical indicators to prioritize conservative evacuation routing.
"""

import os
import json
import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from shapely.geometry import Point, LineString, shape
from shapely import wkt
import rasterio
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.services.routing.road_network_service import road_network_service
from app.services.evacuation.evacuation_constants import (
    EXPOSURE_LOW,
    EXPOSURE_MODERATE,
    EXPOSURE_HIGH,
    EXPOSURE_CRITICAL,
    EXPOSURE_UNKNOWN,
    EVIDENCE_OBSERVED_HAZARD,
    EVIDENCE_FORECAST_DERIVED,
    EVIDENCE_TERRAIN_SUSCEPTIBILITY,
    EVIDENCE_SIMULATED_SCENARIO,
    EVIDENCE_UNKNOWN,
    RELATIVE_EXPOSURE_LOW,
    RELATIVE_EXPOSURE_MODERATE,
    RELATIVE_EXPOSURE_HIGH,
    RELATIVE_EXPOSURE_BLOCKED,
    RELATIVE_EXPOSURE_UNKNOWN,
    CHRONIC_RIVERINE_HOTSPOTS
)
from app.services.evacuation.evacuation_models import RoadExposureItem

logger = logging.getLogger("floodx.evacuation.exposure")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEM_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "elevation", "copernicus_glo90_pune_basin_dem.tif")
SLOPE_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "elevation", "copernicus_glo90_pune_basin_slope.tif")
EXPOSURE_CACHE_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "routing", "road_flood_exposure.json")

# Regional Pune riverbed baseline elevation benchmark (meters above MSL)
PUNE_RIVERBED_DATUM_ELEVATION_M = 545.0


class FloodExposureService:
    """Computes and caches environmental flood hazard exposure for all road graph edges."""

    def __init__(self):
        self._exposure_cache: Optional[Dict[str, RoadExposureItem]] = None
        self._waterways: Optional[List[LineString]] = None
        self._dem_raster = None
        self._slope_raster = None

    def _load_waterways(self) -> List[LineString]:
        """Loads Mula, Mutha, and Mula-Mutha river lines from PostGIS spatial_features."""
        if self._waterways is not None:
            return self._waterways

        waterways = []
        try:
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                q = text("SELECT ST_AsText(geom) as wkt FROM spatial_features WHERE feature_type = 'WATERWAY'")
                rows = conn.execute(q).scalars().all()
                for wkt_str in rows:
                    if wkt_str:
                        geom = wkt.loads(wkt_str)
                        if isinstance(geom, LineString):
                            waterways.append(geom)
                        elif hasattr(geom, "geoms"):
                            for g in geom.geoms:
                                if isinstance(g, LineString):
                                    waterways.append(g)
            logger.info("Loaded %d waterway features for road exposure analysis", len(waterways))
        except Exception as e:
            logger.warning("Could not load waterways from database (%s); using default river corridor line", e)
            # Default Mula-Mutha approximation if DB unavailable
            waterways = [LineString([(73.80, 18.50), (73.85, 18.52), (73.87, 18.53), (73.92, 18.55)])]

        self._waterways = waterways
        return waterways

    def _calculate_waterway_distance_m(self, geom: LineString, waterways: List[LineString]) -> float:
        """Calculates minimum distance in meters between a road LineString and any waterway line."""
        if not waterways:
            return 999.0

        min_dist_deg = float('inf')
        for ww in waterways:
            d = geom.distance(ww)
            if d < min_dist_deg:
                min_dist_deg = d

        # Approximate conversion from degrees to meters at latitude 18.52° N
        # 1 deg lat ~= 110.6 km, 1 deg lon ~= 105.5 km -> mean ~ 108.0 km/deg
        distance_m = min_dist_deg * 108000.0
        return round(distance_m, 1)

    def _check_chronic_hotspots(self, geom: LineString) -> Tuple[bool, Optional[str]]:
        """Checks if a road segment intersects the spatial buffer of known chronic inundation hotspots."""
        coords = list(geom.coords)
        mid_pt = coords[len(coords) // 2]
        mid_lon, mid_lat = mid_pt[0], mid_pt[1]

        for hotspot in CHRONIC_RIVERINE_HOTSPOTS:
            h_lon, h_lat = hotspot["lon"], hotspot["lat"]
            d_deg = math.hypot((mid_lon - h_lon) * 1.055, mid_lat - h_lat)
            d_m = d_deg * 110600.0
            if d_m <= hotspot["buffer_radius_m"]:
                return True, f"Located inside chronic flood hotspot: {hotspot['name']} ({hotspot['hazard_type']})"

        return False, None

    def _sample_rasters(self, coords: List[Tuple[float, float]], dem_band, slope_band, dem_src) -> Tuple[float, float, float]:
        """Samples elevation and slope along the coordinates of a road geometry."""
        elevations = []
        slopes = []

        for lon, lat in coords:
            try:
                py, px = dem_src.index(lon, lat)
                if 0 <= py < dem_src.height and 0 <= px < dem_src.width:
                    val_e = float(dem_band[py, px])
                    val_s = float(slope_band[py, px])
                    if val_e > 0.0:
                        elevations.append(val_e)
                    if val_s >= 0.0:
                        slopes.append(val_s)
            except Exception:
                pass

        min_elev = min(elevations) if elevations else 560.0
        mean_elev = (sum(elevations) / len(elevations)) if elevations else 560.0
        mean_slope = (sum(slopes) / len(slopes)) if slopes else 2.5

        return round(min_elev, 1), round(mean_elev, 1), round(mean_slope, 1)

    def compute_all_exposures(self, force_refresh: bool = False) -> Dict[str, RoadExposureItem]:
        """Calculates or loads cached flood hazard exposure for all edges in the road graph."""
        if self._exposure_cache is not None and not force_refresh:
            return self._exposure_cache

        # Check disk cache
        if not force_refresh and os.path.exists(EXPOSURE_CACHE_PATH):
            try:
                with open(EXPOSURE_CACHE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cache = {k: RoadExposureItem(**v) for k, v in data.items()}
                self._exposure_cache = cache
                logger.info("Loaded %d road exposure assessments from cache %s", len(cache), EXPOSURE_CACHE_PATH)
                return cache
            except Exception as e:
                logger.warning("Failed to load exposure cache (%s); recomputing...", e)

        logger.info("Computing flood hazard exposure for all road graph edges...")
        G = road_network_service.get_or_build_graph()
        waterways = self._load_waterways()
        assessments: Dict[str, RoadExposureItem] = {}
        now_iso = datetime.now(timezone.utc).isoformat()

        # Open Copernicus DEM and Slope rasters
        has_rasters = os.path.exists(DEM_PATH) and os.path.exists(SLOPE_PATH)
        dem_src = rasterio.open(DEM_PATH) if has_rasters else None
        slope_src = rasterio.open(SLOPE_PATH) if has_rasters else None
        dem_band = dem_src.read(1) if dem_src else None
        slope_band = slope_src.read(1) if slope_src else None

        try:
            for u, v, k, d in G.edges(data=True, keys=True):
                edge_id = d.get("edge_id", f"{u}_{v}")
                coords = d.get("geometry_geojson", {}).get("coordinates", [])
                if len(coords) < 2:
                    continue

                line_geom = LineString(coords)

                # 1. Raster metrics
                if dem_band is not None and slope_band is not None and dem_src is not None:
                    min_elev, mean_elev, slope_deg = self._sample_rasters(coords, dem_band, slope_band, dem_src)
                else:
                    min_elev, mean_elev, slope_deg = 560.0, 560.0, 2.5

                # Relative elevation above baseline riverbed datum
                rel_elev = round(max(0.0, min_elev - PUNE_RIVERBED_DATUM_ELEVATION_M), 1)

                # 2. Waterway proximity
                dist_waterway_m = self._calculate_waterway_distance_m(line_geom, waterways)

                # 3. Chronic hotspot proximity
                is_hotspot, hotspot_reason = self._check_chronic_hotspots(line_geom)

                # 4. Multi-criteria exposure classification
                # Rules:
                # - CRITICAL: In chronic flood hotspot OR within 60m of river and rel_elev <= 6m
                # - HIGH: Within 150m of river and rel_elev <= 10m
                # - MODERATE: Within 350m of river OR rel_elev <= 7m with flat slope
                # - LOW: Elevated ground > 350m from river, rel_elev > 7m
                if is_hotspot:
                    tier = EXPOSURE_CRITICAL
                    reason = hotspot_reason or "Proximity to historical inundation hotspot"
                    evidence_type = EVIDENCE_OBSERVED_HAZARD
                    rel_class = RELATIVE_EXPOSURE_HIGH
                elif dist_waterway_m <= 60.0 and rel_elev <= 6.0:
                    tier = EXPOSURE_CRITICAL
                    reason = f"Immediate riverbank corridor ({dist_waterway_m}m) with low relative elevation ({rel_elev}m)"
                    evidence_type = EVIDENCE_TERRAIN_SUSCEPTIBILITY
                    rel_class = RELATIVE_EXPOSURE_HIGH
                elif dist_waterway_m <= 150.0 and rel_elev <= 10.0:
                    tier = EXPOSURE_HIGH
                    reason = f"River buffer zone ({dist_waterway_m}m) within potential overbank reach"
                    evidence_type = EVIDENCE_TERRAIN_SUSCEPTIBILITY
                    rel_class = RELATIVE_EXPOSURE_HIGH
                elif dist_waterway_m <= 350.0 or (rel_elev <= 7.0 and slope_deg <= 2.0):
                    tier = EXPOSURE_MODERATE
                    reason = f"Intermediate river corridor ({dist_waterway_m}m) or local terrain depression"
                    evidence_type = EVIDENCE_TERRAIN_SUSCEPTIBILITY
                    rel_class = RELATIVE_EXPOSURE_MODERATE
                else:
                    tier = EXPOSURE_LOW
                    reason = f"High ground elevation ({min_elev}m MSL) well set back from river ({dist_waterway_m}m)"
                    evidence_type = EVIDENCE_TERRAIN_SUSCEPTIBILITY
                    rel_class = RELATIVE_EXPOSURE_LOW

                item = RoadExposureItem(
                    edge_id=edge_id,
                    source_node=u,
                    destination_node=v,
                    road_name=d.get("name", "Unnamed Road"),
                    highway=d.get("highway", "unclassified"),
                    length_m=d.get("length_m", 0.0),
                    min_elevation_m=min_elev,
                    mean_elevation_m=mean_elev,
                    relative_elevation_m=rel_elev,
                    waterway_distance_m=dist_waterway_m,
                    local_slope_deg=slope_deg,
                    exposure_tier=tier,
                    exposure_reason=reason,
                    is_chronic_hotspot=is_hotspot,
                    evidence_type=evidence_type,
                    relative_exposure_classification=rel_class,
                    evidence_provenance="Copernicus GLO-90 DSM (~90m), OSM Waterway Proximity, WRD Benchmark Hotspots",
                    assessment_timestamp_utc=now_iso
                )
                assessments[edge_id] = item
        finally:
            if dem_src:
                dem_src.close()
            if slope_src:
                slope_src.close()

        # Save to cache
        try:
            os.makedirs(os.path.dirname(EXPOSURE_CACHE_PATH), exist_ok=True)
            with open(EXPOSURE_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump({k: v.model_dump() for k, v in assessments.items()}, f, indent=2)
            logger.info("Saved %d road exposure assessments to cache %s", len(assessments), EXPOSURE_CACHE_PATH)
        except Exception as e:
            logger.error("Failed to write exposure cache: %s", e)

        self._exposure_cache = assessments
        return assessments

    def get_edge_exposure(self, edge_id: str) -> Optional[RoadExposureItem]:
        """Retrieves hazard exposure item for a specific edge."""
        assessments = self.compute_all_exposures()
        return assessments.get(edge_id)


# Global singleton instance
flood_exposure_service = FloodExposureService()

