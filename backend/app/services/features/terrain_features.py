"""Topographical and elevation feature engineering service for Copernicus GLO-90 DSM."""
import os
import logging
from typing import Optional, Dict, Any, List, Tuple
import rasterio
import numpy as np
import pandas as pd
from scipy.ndimage import minimum_filter, uniform_filter

logger = logging.getLogger("floodx.features.terrain")

# Canonical hydrological reference points across Pune / Mula-Mutha river basin
CANONICAL_PUNE_POINTS = [
    {"name": "Sangam (Mula-Mutha Confluence)", "category": "RIVER_CONFLUENCE", "lat": 18.5308, "lon": 73.8643},
    {"name": "Bund Garden Reach", "category": "RIVER_REACH", "lat": 18.5365, "lon": 73.8824},
    {"name": "Yerawada Bridge Reach", "category": "RIVER_REACH", "lat": 18.5492, "lon": 73.8856},
    {"name": "Deccan Gymkhana / Sambhaji Bridge", "category": "RIVER_REACH", "lat": 18.5178, "lon": 73.8441},
    {"name": "Dapodi (Mula-Pavana Confluence)", "category": "RIVER_CONFLUENCE", "lat": 18.5775, "lon": 73.8340},
    {"name": "Aundh Bridge Reach", "category": "RIVER_REACH", "lat": 18.5607, "lon": 73.8078},
    {"name": "Khadakwasla Dam Outfall", "category": "RESERVOIR_OUTLET", "lat": 18.4419, "lon": 73.7661},
    {"name": "Warje Mutha Floodplain", "category": "LOW_LYING_FLOODPLAIN", "lat": 18.4812, "lon": 73.8034},
    {"name": "Sinhagad Road Lowlands (Ekta Nagari)", "category": "LOW_LYING_FLOODPLAIN", "lat": 18.4756, "lon": 73.8242},
    {"name": "Pune Station Core", "category": "URBAN_CORE", "lat": 18.5284, "lon": 73.8739},
    {"name": "Shivajinagar Lowlands", "category": "URBAN_CORE", "lat": 18.5314, "lon": 73.8446},
    {"name": "Kalyani Nagar Riverside", "category": "RIVER_REACH", "lat": 18.5441, "lon": 73.9038},
    {"name": "Mundhwa Bridge Reach", "category": "RIVER_REACH", "lat": 18.5332, "lon": 73.9287},
    {"name": "Hadapsar Industrial Zone", "category": "URBAN_ZONE", "lat": 18.5028, "lon": 73.9272},
    {"name": "Koregaon Park Riverside", "category": "RIVER_REACH", "lat": 18.5385, "lon": 73.8931},
    {"name": "Baner Stream Basin", "category": "STREAM_BASIN", "lat": 18.5590, "lon": 73.7868},
    {"name": "Kothrud Paud Road Corridor", "category": "URBAN_ZONE", "lat": 18.5074, "lon": 73.8077},
    {"name": "Katraj Lake Downstream", "category": "STREAM_BASIN", "lat": 18.4552, "lon": 73.8601},
]


class TerrainFeatureService:
    """Computes neighborhood elevation statistics, relative depression indices,

    focal slope roughness, and topographic flood exposure metrics from Copernicus GLO-90 DSM.
    """

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            self.project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../..")
            )
        else:
            self.project_root = project_root

        self.elevation_dir = os.path.join(self.project_root, "data", "processed", "elevation")
        self.output_dir = os.path.join(self.project_root, "data", "features", "terrain")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_terrain_features(
        self,
        focal_window_size: int = 5,
        grid_sample_step_deg: float = 0.015,  # ~1.6 km regular grid
    ) -> Dict[str, Any]:
        """Processes DEM & Slope rasters, computes focal depression metrics, samples representative

        points and regular spatial grid, and saves features to Parquet and CSV.
        """
        logger.info("Generating terrain and elevation features from Copernicus GLO-90 DSM...")

        dem_path = os.path.join(self.elevation_dir, "copernicus_glo90_pune_basin_dem.tif")
        slope_path = os.path.join(self.elevation_dir, "copernicus_glo90_pune_basin_slope.tif")

        if not os.path.exists(dem_path) or not os.path.exists(slope_path):
            raise FileNotFoundError(f"Elevation or slope raster missing in {self.elevation_dir}")

        with rasterio.open(dem_path) as dem_src, rasterio.open(slope_path) as slope_src:
            dem_arr = dem_src.read(1).astype(np.float32)
            slope_arr = slope_src.read(1).astype(np.float32)
            transform = dem_src.transform
            bounds = dem_src.bounds
            dem_nodata = dem_src.nodata
            slope_nodata = slope_src.nodata

            # Mask invalid / nodata
            if dem_nodata is not None:
                dem_arr[dem_arr == dem_nodata] = np.nan
            if slope_nodata is not None:
                slope_arr[slope_arr == slope_nodata] = np.nan

            # 1. Focal neighborhood calculations (5x5 window ~ 450m x 450m)
            logger.info("Computing focal neighborhood filters (size=%d)...", focal_window_size)
            # Minimum elevation in 5x5 window
            z_min_local = minimum_filter(dem_arr, size=focal_window_size, mode="nearest")
            # Local mean elevation
            z_mean_local = uniform_filter(dem_arr, size=focal_window_size, mode="nearest")
            # Relative height / depression index: Z - Z_min_local
            z_rel = dem_arr - z_min_local

            # Local mean slope and slope standard deviation (roughness)
            slope_clean = np.where(np.isnan(slope_arr), 0.0, slope_arr)
            slope_mean_local = uniform_filter(slope_clean, size=focal_window_size, mode="nearest")
            slope_sq_mean = uniform_filter(slope_clean ** 2, size=focal_window_size, mode="nearest")
            slope_std_local = np.sqrt(np.maximum(0.0, slope_sq_mean - slope_mean_local ** 2))

            # Sample collection
            sampled_records: List[Dict[str, Any]] = []

            def extract_pixel_features(lat: float, lon: float, name: str, cat: str) -> Optional[Dict[str, Any]]:
                """Extracts raster values at coordinate."""
                row, col = dem_src.index(lon, lat)
                if not (0 <= row < dem_arr.shape[0] and 0 <= col < dem_arr.shape[1]):
                    return None

                elev = float(dem_arr[row, col])
                z_min = float(z_min_local[row, col])
                rel_h = float(z_rel[row, col])
                slp = float(slope_clean[row, col])
                slp_m = float(slope_mean_local[row, col])
                slp_s = float(slope_std_local[row, col])

                # Topographic depression susceptibility proxy:
                # Flat ground (slope <= 3 deg) and within 5 meters of local lowest depression point
                is_depression = (rel_h <= 5.0) and (slp <= 3.0)

                # Continuous depression severity index in [0, 1]
                h_factor = max(0.0, 1.0 - (rel_h / 10.0))
                s_factor = max(0.0, 1.0 - (slp / 5.0))
                severity_score = round(float(h_factor * s_factor), 3)

                return {
                    "location_name": name,
                    "location_category": cat,
                    "latitude": round(lat, 5),
                    "longitude": round(lon, 5),
                    "elevation_masl": round(elev, 2),
                    "local_min_elevation_masl": round(z_min, 2),
                    "relative_elevation_m": round(rel_h, 2),
                    "slope_deg": round(slp, 2),
                    "local_mean_slope_deg": round(slp_m, 2),
                    "terrain_roughness_std_deg": round(slp_s, 2),
                    "is_topographic_depression": is_depression,
                    "depression_severity_index": severity_score,
                    "dsm_surface_bias_caveat": (
                        "Copernicus GLO-90 is a Digital Surface Model (DSM) reflecting tree canopy "
                        "and building heights rather than bare-earth terrain (DTM)."
                    ),
                }

            # 2. Extract at canonical Pune hydrological points
            for pt in CANONICAL_PUNE_POINTS:
                rec = extract_pixel_features(pt["lat"], pt["lon"], pt["name"], pt["category"])
                if rec:
                    sampled_records.append(rec)

            # 3. Regular spatial sampling grid across Pune metropolitan core:
            # Lat: 18.42 to 18.62, Lon: 73.74 to 73.96
            lat_grid = np.arange(18.42, 18.62, grid_sample_step_deg)
            lon_grid = np.arange(73.74, 73.96, grid_sample_step_deg)

            grid_counter = 1
            for lt in lat_grid:
                for ln in lon_grid:
                    rec = extract_pixel_features(
                        float(lt),
                        float(ln),
                        f"Pune_Grid_Cell_{grid_counter:03d}",
                        "REGULAR_SPATIAL_GRID",
                    )
                    if rec:
                        sampled_records.append(rec)
                        grid_counter += 1

        df = pd.DataFrame(sampled_records)

        # Save to Parquet and CSV
        csv_file = os.path.join(self.output_dir, "terrain_sampled_features.csv")
        parquet_file = os.path.join(self.output_dir, "terrain_sampled_features.parquet")

        df.to_csv(csv_file, index=False)
        df.to_parquet(parquet_file, index=False, engine="pyarrow")

        logger.info(
            "Terrain features generated: %d records -> %s, %s",
            len(df),
            csv_file,
            parquet_file,
        )

        dep_count = int(df["is_topographic_depression"].sum())
        mean_elev = float(df["elevation_masl"].mean())
        mean_rel = float(df["relative_elevation_m"].mean())

        return {
            "feature_set_name": "COPERNICUS_TERRAIN_SAMPLED_FEATURES",
            "category": "TERRAIN",
            "total_records": len(df),
            "file_path_csv": csv_file,
            "file_path_parquet": parquet_file,
            "columns": list(df.columns),
            "temporal_range": "STATIC_SURFACE (Copernicus GLO-90 DSM Epoch)",
            "spatial_domain": "Pune / Mula-Mutha Basin (73.74E - 73.96E, 18.42N - 18.62N)",
            "summary_metrics": {
                "total_sampled_locations": len(df),
                "depression_zones_count": dep_count,
                "depression_fraction": round(dep_count / len(df), 3),
                "mean_elevation_masl": round(mean_elev, 2),
                "mean_relative_height_m": round(mean_rel, 2),
            },
            "quality_notes": (
                "Calculated from Copernicus GLO-90 90m DSM using 5x5 focal window. "
                "Depression zones identified where relative height <= 5m and slope <= 3 deg. "
                "Critical Caveat: Copernicus GLO-90 is a Digital Surface Model (DSM) capturing urban building rooftops "
                "and vegetation canopies rather than bare-earth terrain (DTM). These depression features serve solely "
                "as preliminary geometric susceptibility proxies; they do NOT model hydrodynamic flow routing or physical flood depths."
            ),
        }

