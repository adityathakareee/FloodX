"""
Audit of Copernicus DEM GLO-90 and Derived Slope products.
"""
import os
import rasterio
import numpy as np

TILES = [
    "data/raw/elevation/Copernicus_DSM_COG_30_N18_00_E073_00_DEM.tif",
    "data/raw/elevation/Copernicus_DSM_COG_30_N18_00_E074_00_DEM.tif"
]
DEM_PROCESSED = "data/processed/elevation/copernicus_glo90_pune_basin_dem.tif"
SLOPE_PROCESSED = "data/processed/elevation/copernicus_glo90_pune_basin_slope.tif"

STUDY_BOUNDS = [73.30, 18.25, 74.25, 18.85]

def audit():
    print("=== Copernicus DEM GLO-90 & Slope Audit ===")
    
    # 1. Raw Tiles
    print("\n--- 1. Raw Elevation Tiles ---")
    for t in TILES:
        with rasterio.open(t) as src:
            b = src.bounds
            data = src.read(1)
            valid = data[data != src.nodata] if src.nodata is not None else data
            print(f"Tile: {os.path.basename(t)}")
            print(f"  Dimensions: {src.width} x {src.height}, CRS: {src.crs}, DType: {src.dtypes[0]}")
            print(f"  Bounds: left={b.left:.4f}, bottom={b.bottom:.4f}, right={b.right:.4f}, top={b.top:.4f}")
            print(f"  NoData: {src.nodata}, Resolution: {abs(src.transform[0]):.6f}°, {abs(src.transform[4]):.6f}°")
            print(f"  Valid pixel elevation: min={valid.min():.1f}m, max={valid.max():.1f}m, mean={valid.mean():.1f}m")

    # 2. Processed Cropped DEM
    print("\n--- 2. Processed Cropped DEM ---")
    with rasterio.open(DEM_PROCESSED) as src:
        b = src.bounds
        data = src.read(1)
        valid = data[data != src.nodata] if src.nodata is not None else data
        print(f"File: {os.path.basename(DEM_PROCESSED)}")
        print(f"  Dimensions: {src.width} x {src.height}, CRS: {src.crs}")
        print(f"  Bounds: left={b.left:.4f}, bottom={b.bottom:.4f}, right={b.right:.4f}, top={b.top:.4f}")
        print(f"  Target Study Bounds: {STUDY_BOUNDS}")
        print(f"  NoData: {src.nodata}")
        print(f"  Elevation Stats: min={valid.min():.1f}m, max={valid.max():.1f}m, mean={valid.mean():.1f}m, std={valid.std():.1f}m")

    # 3. Slope Raster
    print("\n--- 3. Topographic Slope Raster ---")
    with rasterio.open(SLOPE_PROCESSED) as src:
        b = src.bounds
        data = src.read(1)
        valid = data[(data != src.nodata) & (data >= 0)] if src.nodata is not None else data
        print(f"File: {os.path.basename(SLOPE_PROCESSED)}")
        print(f"  Dimensions: {src.width} x {src.height}, CRS: {src.crs}")
        print(f"  Bounds: left={b.left:.4f}, bottom={b.bottom:.4f}, right={b.right:.4f}, top={b.top:.4f}")
        print(f"  NoData: {src.nodata}")
        print(f"  Slope Stats (degrees): min={valid.min():.2f}°, max={valid.max():.2f}°, mean={valid.mean():.2f}°, std={valid.std():.2f}°")

    # 4. DSM vs DTM Classification
    print("\n--- 4. Scientific Surface Classification ---")
    print("  Product Name: Copernicus DEM GLO-90 (Digital Surface Model)")
    print("  Type: DSM (represents top of reflective surface, including vegetation canopy, forest, and urban building heights).")
    print("  Caution: Not a bare-earth Digital Terrain Model (DTM). In dense urban Pune and forested Ghat catchments, heights include canopy/structures.")

if __name__ == "__main__":
    audit()

