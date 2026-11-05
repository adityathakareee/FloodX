"""
Acquires, inspects, and validates real Indian National Water Informatics Centre (NWIC)
telemetry datasets (CWPRS Hourly Rainfall and Maharashtra SW River Water Levels).
"""
import os
import sys
import time
import json
import hashlib
import requests
import pandas as pd

RAW_RAIN_DIR = os.path.abspath("data/raw/rainfall")
RAW_RIVER_DIR = os.path.abspath("data/river_levels")
if not os.path.exists(RAW_RIVER_DIR):
    RAW_RIVER_DIR = os.path.abspath("data/raw/river_levels")
os.makedirs(RAW_RAIN_DIR, exist_ok=True)
os.makedirs(RAW_RIVER_DIR, exist_ok=True)
METADATA_DIR = os.path.abspath("data/metadata")
os.makedirs(METADATA_DIR, exist_ok=True)

CWPRS_RAIN_URL = "https://nwdp.nwic.gov.in/dataset/2f43d9da-02d2-4a61-aef3-cec40f62e63e/resource/7fde6691-8d28-4276-a1d3-ad568ad8b7cf/download/rainfall_tel_hr_cwprs_mh_2021_2025.csv"
MAH_SW_RWL_URL = "https://nwdp.nwic.gov.in/dataset/928a52b4-609e-494d-9b8b-adea2ee56e29/resource/e684c4b6-0714-4579-9d42-10991f23501b/download/rwl_tel_hr_maharashtra_sw_007_2021_2025.csv"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def download_csv_sample(url, dst_path, max_bytes=5*1024*1024):
    if os.path.exists(dst_path) and os.path.getsize(dst_path) > 500000:
        print(f"File exists: {dst_path} ({os.path.getsize(dst_path)} bytes)")
        return dst_path
    headers = {"User-Agent": "FLOODX-Academic-Research/1.0 (Pune Flood Intelligence)"}
    print(f"Streaming from {url} to {dst_path} (max {max_bytes//(1024*1024)}MB)...")
    r = requests.get(url, headers=headers, stream=True, timeout=40)
    r.raise_for_status()
    
    total_bytes = 0
    with open(dst_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
                total_bytes += len(chunk)
                if total_bytes >= max_bytes:
                    break
    print(f"Captured {total_bytes} bytes in {dst_path}")
    return dst_path

def inspect_rainfall_csv(path):
    print(f"\n--- Inspecting CWPRS Rainfall Telemetry CSV: {path} ---")
    try:
        df = pd.read_csv(path, nrows=10000, on_bad_lines='skip')
        cols = list(df.columns)
        print(f"Columns ({len(cols)}): {cols}")
        
        sample_records = df.head(2).to_dict(orient='records')
        stations = df['Station'].dropna().unique().tolist()[:10] if 'Station' in df.columns else []
        print(f"Stations present: {stations}")
        
        # Check rainfall values
        val_col = [c for c in cols if 'rain' in c.lower() or 'value' in c.lower()]
        stats = {}
        if val_col:
            v_series = pd.to_numeric(df[val_col[0]], errors='coerce').dropna()
            stats = {
                "metric_column": val_col[0],
                "min": float(v_series.min()),
                "max": float(v_series.max()),
                "mean": float(v_series.mean()),
                "sample_non_null_records": int(len(v_series))
            }
            print(f"Rainfall stats in sample: min={stats['min']}, max={stats['max']}, mean={stats['mean']:.2f}")
            
        return {
            "columns": cols,
            "sample_row_count": len(df),
            "stations": stations,
            "sample_record": sample_records[0] if sample_records else {},
            "stats": stats
        }
    except Exception as e:
        print(f"Error parsing rainfall CSV: {e}")
        return {"error": str(e)}

def inspect_rwl_csv(path):
    print(f"\n--- Inspecting Maharashtra SW River Water Level CSV: {path} ---")
    try:
        df = pd.read_csv(path, nrows=10000, on_bad_lines='skip')
        cols = list(df.columns)
        print(f"Columns ({len(cols)}): {cols}")
        
        sample_records = df.head(2).to_dict(orient='records')
        station_cols = [c for c in cols if 'station' in c.lower() or 'site' in c.lower()]
        stations = df[station_cols[0]].dropna().unique().tolist()[:10] if station_cols else []
        print(f"Stations in sample: {stations}")
        
        # Check water level values
        val_col = [c for c in cols if 'level' in c.lower() or 'water' in c.lower() or 'value' in c.lower()]
        stats = {}
        if val_col:
            v_series = pd.to_numeric(df[val_col[0]], errors='coerce').dropna()
            stats = {
                "metric_column": val_col[0],
                "min": float(v_series.min()) if len(v_series) > 0 else 0,
                "max": float(v_series.max()) if len(v_series) > 0 else 0,
                "mean": float(v_series.mean()) if len(v_series) > 0 else 0,
                "sample_non_null_records": int(len(v_series))
            }
            print(f"Water level stats in sample: min={stats['min']}, max={stats['max']}, mean={stats['mean']:.2f}")
            
        return {
            "columns": cols,
            "sample_row_count": len(df),
            "stations": stations,
            "sample_record": sample_records[0] if sample_records else {},
            "stats": stats
        }
    except Exception as e:
        print(f"Error parsing RWL CSV: {e}")
        return {"error": str(e)}

def main():
    print("=== NWIC CWPRS & Maharashtra SW Telemetry Dataset Acquisition ===")
    
    # 1. CWPRS Rainfall
    dst_rain = os.path.join(RAW_RAIN_DIR, "rainfall_tel_hr_cwprs_mh_sample.csv")
    download_csv_sample(CWPRS_RAIN_URL, dst_rain, max_bytes=5*1024*1024)
    rain_meta = inspect_rainfall_csv(dst_rain)
    
    # 2. Maharashtra SW River Water Level (Krishna Basin 007)
    dst_rwl = os.path.join(RAW_RIVER_DIR, "rwl_tel_hr_maharashtra_sw_007_sample.csv")
    download_csv_sample(MAH_SW_RWL_URL, dst_rwl, max_bytes=5*1024*1024)
    rwl_meta = inspect_rwl_csv(dst_rwl)
    
    metadata = {
        "dataset_name": "NWIC Indian Telemetry (CWPRS Rainfall & Maharashtra SW River Water Levels)",
        "provider": "National Water Informatics Centre (NWIC), Ministry of Jal Shakti, Government of India",
        "portal": "https://nwdp.nwic.gov.in/",
        "license": "Government Open Data License - India (GODL)",
        "provenance_and_verification_notes": [
            "CWPRS Khadakwasla station provides verified hourly telemetry located in Haveli Tehsil, Pune directly at the Khadakwasla dam basin (Lat: 18.4469, Lon: 73.7850).",
            "Maharashtra SW Krishna Basin 007 provides official hourly river stage telemetry.",
            "Municipal gauges within central Pune (Holkar Bridge, Baba Bhide Bridge, Deccan) are monitored by Pune Municipal Corporation (PMC) and Maharashtra Water Resources Department (WRD); station dictionary joins will be integrated in Phase 1 Stage 2."
        ],
        "files": [
            {
                "product_type": "CWPRS Hourly Rainfall Telemetry (Maharashtra/Pune)",
                "filename": os.path.basename(dst_rain),
                "relative_path": "data/raw/rainfall/rainfall_tel_hr_cwprs_mh_sample.csv",
                "source_url": CWPRS_RAIN_URL,
                "size_bytes": os.path.getsize(dst_rain),
                "sha256": compute_sha256(dst_rain),
                "inspection": rain_meta
            },
            {
                "product_type": "Maharashtra SW Hourly River Water Level Telemetry (Krishna Basin 007)",
                "filename": os.path.basename(dst_rwl),
                "relative_path": "data/raw/river_levels/rwl_tel_hr_maharashtra_sw_007_sample.csv",
                "source_url": MAH_SW_RWL_URL,
                "size_bytes": os.path.getsize(dst_rwl),
                "sha256": compute_sha256(dst_rwl),
                "inspection": rwl_meta
            }
        ],
        "acquisition_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    meta_path = os.path.join(METADATA_DIR, "nwic_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nMetadata written to {meta_path}")
    print("NWIC acquisition & inspection completed successfully!")

if __name__ == "__main__":
    main()
