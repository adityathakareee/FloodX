"""Test Copernicus DEM sampling along road lines."""
import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

import rasterio
from shapely.geometry import shape, LineString
import json

dem_path = "data/processed/elevation/copernicus_glo90_pune_basin_dem.tif"
slope_path = "data/processed/elevation/copernicus_glo90_pune_basin_slope.tif"

print(f"Opening DEM: {dem_path}")
with rasterio.open(dem_path) as dem_src, rasterio.open(slope_path) as slope_src:
    print(f"DEM bounds: {dem_src.bounds}, crs={dem_src.crs}, shape={dem_src.shape}")
    print(f"Slope bounds: {slope_src.bounds}, crs={slope_src.crs}")
    
    # Sample point around Deccan (73.844, 18.518)
    py, px = dem_src.index(73.844, 18.518)
    elev = dem_src.read(1)[py, px]
    slope = slope_src.read(1)[py, px]
    print(f"Sample at Deccan Gymkhana (73.844, 18.518): Elevation = {elev:.1f}m, Slope = {slope:.1f}deg")

