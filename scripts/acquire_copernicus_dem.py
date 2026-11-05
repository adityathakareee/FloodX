"""
Acquires, validates, mosaics, crops, and derives slope for Copernicus DEM GLO-90
covering the Pune / Mula-Mutha River Basin provisional study area.
"""
import os
import sys
import time
import json
import hashlib
import numpy as np
import requests
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
from shapely.geometry import box, mapping

RAW_DIR = os.path.abspath("data/raw/elevation")
PROCESSED_DIR = os.path.abspath("data/processed/elevation")
METADATA_DIR = os.path.abspath("data/metadata")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

# Provisional study bounds: [west, south, east, north]
STUDY_BOUNDS = [73.30, 18.25, 74.25, 18.85]

TILES = [
    {
        "name": "Copernicus_DSM_COG_30_N18_00_E073_00_DEM.tif",
        "url": "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N18_00_E073_00_DEM/Copernicus_DSM_COG_30_N18_00_E073_00_DEM.tif"
    },
    {
        "name": "Copernicus_DSM_COG_30_N18_00_E074_00_DEM.tif",
        "url": "https://copernicus-dem-90m.s3.amazonaws.com/Copernicus_DSM_COG_30_N18_00_E074_00_DEM/Copernicus_DSM_COG_30_N18_00_E074_00_DEM.tif"
    }
]

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def download_file(url, target_path):
    if os.path.exists(target_path) and os.path.getsize(target_path) > 1000000:
        print(f"File already exists: {target_path} ({os.path.getsize(target_path)} bytes)")
        return
    print(f"Downloading {url} -> {target_path}...")
    headers = {"User-Agent": "FLOODX-Academic-Research/1.0 (Pune Flood Intelligence)"}
    r = requests.get(url, headers=headers, stream=True, timeout=60)
    r.raise_for_status()
    with open(target_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*256):
            if chunk:
                f.write(chunk)
    print(f"Downloaded successfully: {os.path.getsize(target_path)} bytes")

def compute_slope(dem_array, res_x_deg, res_y_deg, center_lat_deg=18.52):
    """
    Computes slope in degrees from a DEM in geographic degrees (EPSG:4326).
    Converts degree spacing to meters using spherical approximation.
    """
    # 1 deg lat ~ 111,139 m; 1 deg lon ~ 111,139 * cos(lat) m
    m_per_deg_lat = 111139.0
    m_per_deg_lon = 111139.0 * np.cos(np.radians(center_lat_deg))
    
    dx = res_x_deg * m_per_deg_lon
    dy = res_y_deg * m_per_deg_lat
    
    # Gradient in y (axis 0) and x (axis 1)
    gy, gx = np.gradient(dem_array, dy, dx)
    
    slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
    slope_deg = np.degrees(slope_rad)
    return slope_deg.astype(np.float32)

def main():
    print("=== Copernicus DEM GLO-90 Acquisition & Processing ===")
    
    downloaded_files = []
    tile_meta = []
    
    for tile in TILES:
        dst = os.path.join(RAW_DIR, tile["name"])
        download_file(tile["url"], dst)
        downloaded_files.append(dst)
        
        with rasterio.open(dst) as src:
            bounds = src.bounds
            meta = {
                "file": tile["name"],
                "crs": str(src.crs),
                "width": src.width,
                "height": src.height,
                "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top],
                "nodata": src.nodata,
                "dtype": str(src.dtypes[0]),
                "sha256": compute_sha256(dst),
                "size_bytes": os.path.getsize(dst)
            }
            tile_meta.append(meta)
            print(f"Tile {tile['name']}: {src.width}x{src.height}, CRS={src.crs}, bounds={bounds}")

    # Step 2: Mosaic
    print("\nMosaicking tiles...")
    src_files_to_mosaic = [rasterio.open(f) for f in downloaded_files]
    mosaic, out_trans = merge(src_files_to_mosaic)
    
    mosaic_meta = src_files_to_mosaic[0].meta.copy()
    mosaic_meta.update({
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": out_trans,
        "crs": src_files_to_mosaic[0].crs
    })
    
    for s in src_files_to_mosaic:
        s.close()
        
    print(f"Mosaicked dimensions: {mosaic.shape[2]}x{mosaic.shape[1]}")
    
    # Temporary mosaic file for rasterio mask
    temp_mosaic_path = os.path.join(RAW_DIR, "temp_copernicus_mosaic.tif")
    with rasterio.open(temp_mosaic_path, "w", **mosaic_meta) as dst:
        dst.write(mosaic)
        
    # Step 3: Crop to study bounding box
    print(f"\nCropping mosaic to study bounds: {STUDY_BOUNDS}...")
    crop_geom = box(*STUDY_BOUNDS)
    
    with rasterio.open(temp_mosaic_path) as src:
        out_image, out_transform = mask(src, [mapping(crop_geom)], crop=True)
        out_meta = src.meta.copy()
        
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform,
        "compress": "lzw"
    })
    
    processed_dem_path = os.path.join(PROCESSED_DIR, "copernicus_glo90_pune_basin_dem.tif")
    with rasterio.open(processed_dem_path, "w", **out_meta) as dst:
        dst.write(out_image)
        
    if os.path.exists(temp_mosaic_path):
        os.remove(temp_mosaic_path)
        
    # Step 4: Validate cropped DEM
    dem_data = out_image[0]
    valid_mask = dem_data != out_meta.get("nodata", -99999)
    valid_elev = dem_data[valid_mask]
    
    elev_min = float(valid_elev.min())
    elev_max = float(valid_elev.max())
    elev_mean = float(valid_elev.mean())
    elev_std = float(valid_elev.std())
    
    print(f"Cropped DEM saved: {processed_dem_path}")
    print(f"Dimensions: {out_image.shape[2]} x {out_image.shape[1]}")
    print(f"Elevation range: {elev_min:.1f} m to {elev_max:.1f} m (mean: {elev_mean:.1f} m, std: {elev_std:.1f} m)")
    
    # Step 5: Derive Slope
    print("\nDeriving slope raster...")
    res_x = abs(out_transform[0])
    res_y = abs(out_transform[4])
    slope_data = compute_slope(dem_data, res_x, res_y, center_lat_deg=18.52)
    slope_data[~valid_mask] = -9999.0
    
    slope_meta = out_meta.copy()
    slope_meta.update({
        "dtype": "float32",
        "nodata": -9999.0
    })
    
    processed_slope_path = os.path.join(PROCESSED_DIR, "copernicus_glo90_pune_basin_slope.tif")
    with rasterio.open(processed_slope_path, "w", **slope_meta) as dst:
        dst.write(slope_data, 1)
        
    valid_slope = slope_data[slope_data >= 0]
    print(f"Slope raster saved: {processed_slope_path}")
    print(f"Slope range: {float(valid_slope.min()):.2f}° to {float(valid_slope.max()):.2f}° (mean: {float(valid_slope.mean()):.2f}°)")
    
    # Step 6: Write Metadata
    metadata = {
        "dataset_name": "Copernicus DEM GLO-90",
        "provider": "European Space Agency (ESA) / AWS Open Data",
        "access_method": "Direct S3 HTTPS (Public / No Auth Required)",
        "spatial_resolution": "90m (0.00083333 degrees / ~3 arc-seconds)",
        "vertical_datum": "EGM2008 geoid",
        "horizontal_datum": "WGS 84 (EPSG:4326)",
        "study_area": {
            "name": "Pune / Mula-Mutha River Basin Provisional Catchment",
            "bounds_wgs84": STUDY_BOUNDS,
            "centroid": [18.5204, 73.8567]
        },
        "raw_tiles": tile_meta,
        "processed_products": [
            {
                "product_type": "Cropped DEM",
                "filename": "copernicus_glo90_pune_basin_dem.tif",
                "relative_path": "data/processed/elevation/copernicus_glo90_pune_basin_dem.tif",
                "crs": "EPSG:4326",
                "dimensions": [out_image.shape[2], out_image.shape[1]],
                "pixel_size_deg": [res_x, res_y],
                "elevation_unit": "meters",
                "elevation_stats": {
                    "min": elev_min,
                    "max": elev_max,
                    "mean": elev_mean,
                    "std": elev_std
                },
                "sha256": compute_sha256(processed_dem_path),
                "size_bytes": os.path.getsize(processed_dem_path)
            },
            {
                "product_type": "Slope Raster",
                "filename": "copernicus_glo90_pune_basin_slope.tif",
                "relative_path": "data/processed/elevation/copernicus_glo90_pune_basin_slope.tif",
                "crs": "EPSG:4326",
                "dimensions": [out_image.shape[2], out_image.shape[1]],
                "slope_unit": "degrees",
                "slope_stats": {
                    "min": float(valid_slope.min()),
                    "max": float(valid_slope.max()),
                    "mean": float(valid_slope.mean())
                },
                "sha256": compute_sha256(processed_slope_path),
                "size_bytes": os.path.getsize(processed_slope_path)
            }
        ],
        "licensing": "Free and open data access under the Copernicus Programme and ESA terms of use.",
        "acquisition_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    meta_path = os.path.join(METADATA_DIR, "copernicus_dem_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nMetadata written to: {meta_path}")
    print("Copernicus DEM acquisition & processing completed successfully!")

if __name__ == "__main__":
    main()

