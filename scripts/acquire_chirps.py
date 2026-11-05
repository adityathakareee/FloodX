"""
Acquires, validates, and crops CHIRPS v3 daily precipitation data
for the Pune / Mula-Mutha River Basin study area.
"""
import os
import sys
import time
import json
import hashlib
import requests
import rasterio
from rasterio.mask import mask
from shapely.geometry import box, mapping

RAW_DIR = os.path.abspath("data/raw/rainfall")
PROCESSED_DIR = os.path.abspath("data/processed/rainfall")
METADATA_DIR = os.path.abspath("data/metadata")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

STUDY_BOUNDS = [73.30, 18.25, 74.25, 18.85]

CANDIDATE_URLS = [
    # 2026 final satellite product
    ("chirps-v3.0.sat.2026.01.01.tif", "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/sat/2026/chirps-v3.0.sat.2026.01.01.tif", "CHIRPS v3 Final Satellite Daily"),
    # 2024 reanalysis final product during Pune monsoon
    ("chirps-v3.0.rnl.2024.07.25.tif", "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/2024/chirps-v3.0.rnl.2024.07.25.tif", "CHIRPS v3 Final Reanalysis Daily (July 2024 Monsoon Flood)"),
    # 2026 prelim product
    ("chirps-v3.0.prelim.2026.01.01.tif", "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/prelim/sat/2026/chirps-v3.0.prelim.2026.01.01.tif", "CHIRPS v3 Preliminary Daily")
]

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def download_with_retry(url, dst_path, max_retries=3):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FLOODX-Academic-Research/1.0"}
    for attempt in range(max_retries):
        try:
            print(f"Downloading {url} (attempt {attempt+1}/{max_retries})...")
            r = requests.get(url, headers=headers, stream=True, timeout=90)
            if r.status_code == 200:
                with open(dst_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*256):
                        if chunk:
                            f.write(chunk)
                print(f"Download complete: {os.path.getsize(dst_path)} bytes")
                return True
            elif r.status_code == 429:
                print(f"Received 429 Rate Limit. Sleeping 5s before retry...")
                time.sleep(5)
            else:
                print(f"HTTP {r.status_code} received.")
        except Exception as e:
            print(f"Network error: {e}")
            time.sleep(3)
    return False

def main():
    print("=== CHIRPS v3 Acquisition & Processing ===")
    
    selected_file = None
    selected_product = None
    selected_url = None
    
    # Try candidate URLs in order
    for fname, url, prod_desc in CANDIDATE_URLS:
        dst = os.path.join(RAW_DIR, fname)
        if os.path.exists(dst) and os.path.getsize(dst) > 1000000:
            print(f"File exists: {dst} ({os.path.getsize(dst)} bytes)")
            selected_file = dst
            selected_product = prod_desc
            selected_url = url
            break
            
        success = download_with_retry(url, dst)
        if success:
            selected_file = dst
            selected_product = prod_desc
            selected_url = url
            break
            
    if not selected_file or not os.path.exists(selected_file):
        print("ERROR: Failed to download any CHIRPS v3 candidate.")
        sys.exit(1)
        
    print(f"\nInspecting raw CHIRPS raster: {selected_file}")
    with rasterio.open(selected_file) as src:
        raw_width = src.width
        raw_height = src.height
        raw_crs = str(src.crs)
        raw_bounds = [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top]
        raw_nodata = src.nodata
        raw_dtype = str(src.dtypes[0])
        raw_transform = src.transform
        
        print(f"Dimensions: {raw_width} x {raw_height}")
        print(f"CRS: {raw_crs}")
        print(f"Bounds: {raw_bounds}")
        print(f"Resolution: {abs(raw_transform[0]):.5f}° x {abs(raw_transform[4]):.5f}°")
        print(f"NoData: {raw_nodata}, DType: {raw_dtype}")
        
    # Crop to Pune study area
    print(f"\nCropping to study bounds: {STUDY_BOUNDS}...")
    crop_geom = box(*STUDY_BOUNDS)
    
    with rasterio.open(selected_file) as src:
        out_image, out_transform = mask(src, [mapping(crop_geom)], crop=True)
        out_meta = src.meta.copy()
        
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform,
        "compress": "lzw"
    })
    
    processed_chirps_path = os.path.join(PROCESSED_DIR, "chirps_v3_pune_basin_cropped.tif")
    with rasterio.open(processed_chirps_path, "w", **out_meta) as dst:
        dst.write(out_image)
        
    # Compute stats on cropped data
    rain_data = out_image[0]
    valid_mask = (rain_data != out_meta.get("nodata")) & (rain_data >= 0)
    valid_rain = rain_data[valid_mask]
    
    r_min = float(valid_rain.min()) if len(valid_rain) > 0 else 0.0
    r_max = float(valid_rain.max()) if len(valid_rain) > 0 else 0.0
    r_mean = float(valid_rain.mean()) if len(valid_rain) > 0 else 0.0
    
    print(f"Cropped raster saved: {processed_chirps_path}")
    print(f"Cropped dimensions: {out_image.shape[2]} x {out_image.shape[1]} cells")
    print(f"Rainfall stats (mm/day): min={r_min:.2f}, max={r_max:.2f}, mean={r_mean:.2f}")
    
    # Write metadata
    metadata = {
        "dataset_name": "CHIRPS v3 Daily Precipitation",
        "provider": "Climate Hazards Center (CHC), UC Santa Barbara",
        "product_selected": selected_product,
        "source_url": selected_url,
        "spatial_resolution": "0.05 degrees (~5.3 km)",
        "temporal_resolution": "Daily",
        "unit": "mm/day",
        "crs": raw_crs or "EPSG:4326",
        "nodata_value": raw_nodata,
        "study_area": {
            "name": "Pune / Mula-Mutha River Basin Provisional Catchment",
            "bounds_wgs84": STUDY_BOUNDS
        },
        "raw_file": {
            "filename": os.path.basename(selected_file),
            "relative_path": os.path.relpath(selected_file, os.getcwd()).replace("\\", "/"),
            "dimensions": [raw_width, raw_height],
            "sha256": compute_sha256(selected_file),
            "size_bytes": os.path.getsize(selected_file)
        },
        "processed_file": {
            "filename": os.path.basename(processed_chirps_path),
            "relative_path": os.path.relpath(processed_chirps_path, os.getcwd()).replace("\\", "/"),
            "dimensions": [out_image.shape[2], out_image.shape[1]],
            "bounds_wgs84": STUDY_BOUNDS,
            "rainfall_stats_mm_day": {
                "min": r_min,
                "max": r_max,
                "mean": r_mean
            },
            "sha256": compute_sha256(processed_chirps_path),
            "size_bytes": os.path.getsize(processed_chirps_path)
        },
        "citation": "Funk, C. et al. Climate Hazards Center InfraRed Precipitation with Station data (CHIRPS) v3.0, UC Santa Barbara.",
        "acquisition_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    meta_path = os.path.join(METADATA_DIR, "chirps_v3_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata written to {meta_path}")
    print("CHIRPS v3 acquisition & processing completed successfully!")

if __name__ == "__main__":
    main()

