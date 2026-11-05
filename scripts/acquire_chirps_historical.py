"""
Acquires genuine CHIRPS v3 historical daily rainfall data and multi-year time series
for the Pune / Mula-Mutha River Basin study area (2020-2024).
"""
import os
import sys
import time
import json
import hashlib
import rasterio
from rasterio.windows import from_bounds
import pandas as pd
import numpy as np

# Configure GDAL HTTP client for robust fast timeouts
os.environ["GDAL_HTTP_TIMEOUT"] = "15"
os.environ["GDAL_HTTP_MAX_RETRY"] = "2"
os.environ["GDAL_HTTP_RETRY_DELAY"] = "2"
os.environ["GDAL_HTTP_USERAGENT"] = "FLOODX-Academic-Research/1.0 (Pune Flood Intelligence)"

RAW_DIR = os.path.abspath("data/raw/rainfall")
PROCESSED_DIR = os.path.abspath("data/processed/rainfall")
METADATA_DIR = os.path.abspath("data/metadata")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

# Provisional study bounds: [west, south, east, north]
STUDY_BOUNDS = [73.30, 18.25, 74.25, 18.85]
PEAK_EVENT_FILENAME = "chirps-v3.0.sat.2024.07.25.tif"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def crop_peak_raster(raw_path):
    print(f"\nCropping peak flood raster ({raw_path}) to study bounds: {STUDY_BOUNDS}...")
    with rasterio.open(raw_path) as src:
        win = from_bounds(*STUDY_BOUNDS, src.transform)
        # Compute integer slices to avoid deprecation warnings
        col_off = int(np.floor(win.col_off))
        row_off = int(np.floor(win.row_off))
        width = int(np.ceil(win.width))
        height = int(np.ceil(win.height))
        int_win = rasterio.windows.Window(col_off, row_off, width, height)
        
        cropped_data = src.read(1, window=int_win)
        cropped_trans = src.window_transform(int_win)
        meta = src.meta.copy()
        
    meta.update({
        "driver": "GTiff",
        "height": cropped_data.shape[0],
        "width": cropped_data.shape[1],
        "transform": cropped_trans,
        "compress": "lzw"
    })
    
    out_path = os.path.join(PROCESSED_DIR, "chirps_v3_pune_basin_cropped.tif")
    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(cropped_data, 1)
        
    valid = cropped_data[cropped_data >= 0]
    print(f"Saved cropped peak raster: {out_path} ({os.path.getsize(out_path)} bytes)")
    print(f"Dimensions: {cropped_data.shape[1]} x {cropped_data.shape[0]}")
    print(f"Rainfall stats (2024-07-25): min={valid.min():.2f} mm, max={valid.max():.2f} mm, mean={valid.mean():.2f} mm")
    return out_path, float(valid.min()), float(valid.max()), float(valid.mean())

def extract_multi_year_timeseries():
    """
    Extracts daily time series for the Pune study area across representative monsoon
    and flood periods from 2020 through 2024 using GDAL /vsicurl/.
    """
    print("\n--- Extracting Multi-Year Daily Rainfall Time Series (2020-2024) ---")
    
    # 5 Key Monsoon/Flood Epochs across 2020 to 2024 (25 total observations)
    epochs = [
        ("2024", [f"2024.07.{d:02d}" for d in range(22, 27)], "July 2024 Catastrophic Cloudburst & Khadakwasla Dam Spill"),
        ("2023", [f"2023.07.{d:02d}" for d in range(22, 27)], "July 2023 Peak Monsoon Catchment Inflow"),
        ("2022", [f"2022.07.{d:02d}" for d in range(11, 16)], "July 2022 Heavy Catchment Runoff Sequence"),
        ("2021", [f"2021.07.{d:02d}" for d in range(21, 26)], "July 2021 Historic Western Ghats Severe Flood Event"),
        ("2020", [f"2020.08.{d:02d}" for d in range(4, 9)], "August 2020 Peak Western Ghats Spill Event")
    ]
    
    records = []
    grids_2024 = []
    
    for year, dates, epoch_desc in epochs:
        print(f"\nProcessing {year}: {epoch_desc} ({len(dates)} days)...")
        for dt_str in dates:
            iso_date = dt_str.replace(".", "-")
            url = f"/vsicurl/https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/sat/{year}/chirps-v3.0.sat.{dt_str}.tif"
            
            # If it's 2024-07-25, we already have it locally!
            if dt_str == "2024.07.25":
                local_f = os.path.join(RAW_DIR, PEAK_EVENT_FILENAME)
                if os.path.exists(local_f):
                    url = local_f
                    
            try:
                t0 = time.time()
                with rasterio.open(url) as src:
                    win = from_bounds(*STUDY_BOUNDS, src.transform)
                    col_off = int(np.floor(win.col_off))
                    row_off = int(np.floor(win.row_off))
                    width = int(np.ceil(win.width))
                    height = int(np.ceil(win.height))
                    int_win = rasterio.windows.Window(col_off, row_off, width, height)
                    
                    data = src.read(1, window=int_win)
                    valid = data[data >= 0]
                    if len(valid) > 0:
                        rec = {
                            "date": iso_date,
                            "year": int(year),
                            "min_mm_day": round(float(valid.min()), 2),
                            "max_mm_day": round(float(valid.max()), 2),
                            "mean_mm_day": round(float(valid.mean()), 2),
                            "p90_mm_day": round(float(np.percentile(valid, 90)), 2),
                            "epoch": epoch_desc,
                            "data_source": f"CHIRPS v3 Final Sat ({dt_str})",
                            "status": "valid"
                        }
                        records.append(rec)
                        print(f"  {iso_date} ({time.time()-t0:.2f}s): min={rec['min_mm_day']}, mean={rec['mean_mm_day']}, max={rec['max_mm_day']} mm/day")
                        
                        if year == "2024":
                            grids_2024.append((iso_date, data, src.window_transform(int_win), src.meta.copy()))
            except Exception as e:
                print(f"  Error on {iso_date}: {e}")
                records.append({
                    "date": iso_date,
                    "year": int(year),
                    "min_mm_day": None,
                    "max_mm_day": None,
                    "mean_mm_day": None,
                    "p90_mm_day": None,
                    "epoch": epoch_desc,
                    "data_source": f"CHIRPS v3 Final Sat ({dt_str})",
                    "status": f"error: {str(e)[:50]}"
                })
                
    df_ts = pd.DataFrame(records)
    csv_path = os.path.join(PROCESSED_DIR, "chirps_v3_pune_daily_2020_2024_timeseries.csv")
    df_ts.to_csv(csv_path, index=False)
    print(f"\nSaved multi-year daily time series CSV: {csv_path} ({len(df_ts)} records)")
    print("\nSummary by Year (Monsoon Peak Epochs):")
    valid_df = df_ts[df_ts["status"] == "valid"]
    print(valid_df.groupby("year")[["mean_mm_day", "max_mm_day"]].agg(["min", "mean", "max"]))

    # Save multi-band raster for 2024 sequence
    if grids_2024:
        mband_path = os.path.join(PROCESSED_DIR, "chirps_v3_pune_july2024_flood_sequence.tif")
        meta = grids_2024[0][3]
        meta.update({
            "driver": "GTiff",
            "count": len(grids_2024),
            "height": grids_2024[0][1].shape[0],
            "width": grids_2024[0][1].shape[1],
            "transform": grids_2024[0][2],
            "compress": "lzw"
        })
        with rasterio.open(mband_path, "w", **meta) as dst:
            for idx, (dt, grid, _, _) in enumerate(grids_2024, start=1):
                dst.write(grid, idx)
                dst.set_band_description(idx, f"Rainfall_{dt}_mm_day")
        print(f"Saved multi-band 2024 flood sequence: {mband_path} ({len(grids_2024)} bands)")

    return csv_path, len(df_ts)

def main():
    print("=== Acquiring Genuine CHIRPS v3 Historical Multi-Year Rainfall (2020-2024) ===")
    
    raw_peak = os.path.join(RAW_DIR, PEAK_EVENT_FILENAME)
    if not os.path.exists(raw_peak) or os.path.getsize(raw_peak) < 1000000:
        print(f"ERROR: {raw_peak} missing or incomplete.")
        sys.exit(1)
        
    crop_path, r_min, r_max, r_mean = crop_peak_raster(raw_peak)
    csv_ts_path, ts_count = extract_multi_year_timeseries()
    
    # Metadata update
    metadata = {
        "dataset_name": "CHIRPS v3 Historical Daily Precipitation & Multi-Year Time Series",
        "provider": "Climate Hazards Center (CHC), University of California Santa Barbara (UCSB)",
        "license": "Public Domain / Open Data Attribution",
        "citation": "Funk, C. et al. Climate Hazards Center InfraRed Precipitation with Station data (CHIRPS) v3.0, UC Santa Barbara.",
        "spatial_resolution": "0.05 degrees (~5.3 km)",
        "temporal_resolution": "Daily",
        "unit": "mm/day",
        "crs": "EPSG:4326",
        "study_area": {
            "name": "Pune / Mula-Mutha River Basin Provisional Catchment",
            "bounds_wgs84": STUDY_BOUNDS
        },
        "artifacts": {
            "raw_peak_event": {
                "filename": PEAK_EVENT_FILENAME,
                "relative_path": f"data/raw/rainfall/{PEAK_EVENT_FILENAME}",
                "observation_date": "2024-07-25",
                "sha256": compute_sha256(raw_peak),
                "size_bytes": os.path.getsize(raw_peak),
                "notes": "Global raw daily Cloud-Optimized GeoTIFF for peak monsoon flood day in Pune."
            },
            "processed_peak_raster": {
                "filename": os.path.basename(crop_path),
                "relative_path": "data/processed/rainfall/chirps_v3_pune_basin_cropped.tif",
                "observation_date": "2024-07-25",
                "dimensions": [19, 12],
                "rainfall_stats_mm_day": {
                    "min": r_min,
                    "max": r_max,
                    "mean": r_mean
                },
                "sha256": compute_sha256(crop_path),
                "size_bytes": os.path.getsize(crop_path)
            },
            "multi_year_timeseries_csv": {
                "filename": os.path.basename(csv_ts_path),
                "relative_path": "data/processed/rainfall/chirps_v3_pune_daily_2020_2024_timeseries.csv",
                "temporal_coverage": "2020 - 2024 (Monsoon peak flood epochs)",
                "total_observations": ts_count,
                "sha256": compute_sha256(csv_ts_path),
                "size_bytes": os.path.getsize(csv_ts_path)
            }
        },
        "acquisition_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    meta_path = os.path.join(METADATA_DIR, "chirps_v3_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nMetadata written to: {meta_path}")
    print("CHIRPS v3 historical multi-year acquisition completed successfully!")

if __name__ == "__main__":
    main()
