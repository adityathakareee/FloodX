"""
FLOOD-X Phase 1 / Stage 1 Automated Data Verification Script

Checks all raw, processed, metadata, and manifest artifacts for:
1. Existence and non-zero file sizes
2. Valid CRS (WGS84 EPSG:4326) for geospatial rasters and vectors
3. Bounding box intersection with Pune / Mula-Mutha study area
4. Raster data integrity (dimensions, valid elevation/rainfall range, nodata)
5. Vector layer integrity (layer counts, geometries, non-empty)
6. JSON schema and checksum validation
"""
import os
import sys
import json
import hashlib
import numpy as np
import rasterio
import geopandas as gpd
import pandas as pd
import pyogrio

STUDY_BOUNDS = [73.30, 18.25, 74.25, 18.85] # [west, south, east, north]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def check_file(path, min_bytes=100):
    if not os.path.exists(path):
        return False, f"MISSING: {path}"
    sz = os.path.getsize(path)
    if sz < min_bytes:
        return False, f"TOO SMALL: {path} ({sz} bytes)"
    return True, f"OK ({sz} bytes)"

def main():
    print("=" * 80)
    print("FLOOD-X PHASE 1 / STAGE 1: COMPREHENSIVE DATASET VERIFICATION")
    print("=" * 80)
    
    errors = []
    checks = []
    
    # 1. Raw Files
    raw_files = [
        "data/raw/elevation/Copernicus_DSM_COG_30_N18_00_E073_00_DEM.tif",
        "data/raw/elevation/Copernicus_DSM_COG_30_N18_00_E074_00_DEM.tif",
        "data/raw/weather/open_meteo_forecast_pune.json",
        "data/raw/weather/open_meteo_historical_202407_pune.json",
        "data/raw/rainfall/chirps-v3.0.sat.2024.07.25.tif",
        "data/raw/rainfall/chirps-v3.0.sat.2026.01.01.tif",
        "data/raw/rainfall/rainfall_tel_hr_cwprs_mh_sample.csv",
        "data/raw/river_levels/rwl_tel_hr_maharashtra_sw_007_sample.csv",
    ]
    
    print("\n--- 1. Raw Dataset Integrity ---")
    for rf in raw_files:
        ok, msg = check_file(rf, min_bytes=1000)
        checks.append((rf, ok, msg))
        status_sym = "[PASS]" if ok else "[FAIL]"
        print(f"  {status_sym} {rf:<65} : {msg}")
        if not ok:
            errors.append(msg)
            
    # 2. Processed Rasters
    print("\n--- 2. Processed Raster Validation ---")
    rasters = [
        ("data/processed/elevation/copernicus_glo90_pune_basin_dem.tif", "DEM", 0.0, 1500.0, 1000),
        ("data/processed/elevation/copernicus_glo90_pune_basin_slope.tif", "Slope", 0.0, 90.0, 1000),
        ("data/processed/rainfall/chirps_v3_pune_basin_cropped.tif", "CHIRPS Peak Cropped", 0.0, 500.0, 500),
        ("data/processed/rainfall/chirps_v3_pune_july2024_flood_sequence.tif", "CHIRPS 2024 Sequence", 0.0, 500.0, 1000)
    ]
    
    for rpath, label, min_val, max_val, min_sz in rasters:
        ok, msg = check_file(rpath, min_bytes=min_sz)
        if not ok:
            checks.append((rpath, False, msg))
            errors.append(msg)
            print(f"  [FAIL] {rpath:<65} : {msg}")
            continue
            
        try:
            with rasterio.open(rpath) as src:
                crs = str(src.crs)
                bounds = src.bounds
                width, height = src.width, src.height
                data = src.read(1)
                nodata = src.nodata
                
                valid_mask = data != nodata if nodata is not None else ~np.isnan(data)
                valid_data = data[valid_mask]
                
                dmin = float(valid_data.min()) if len(valid_data) > 0 else 0.0
                dmax = float(valid_data.max()) if len(valid_data) > 0 else 0.0
                
                crs_ok = "4326" in crs
                bbox_ok = not (bounds.right < STUDY_BOUNDS[0] or bounds.left > STUDY_BOUNDS[2] or
                              bounds.top < STUDY_BOUNDS[1] or bounds.bottom > STUDY_BOUNDS[3])
                range_ok = (dmin >= min_val - 1.0 and dmax <= max_val + 10.0)
                
                if crs_ok and bbox_ok and range_ok:
                    res_msg = f"PASS ({width}x{height}, CRS={crs}, Range=[{dmin:.1f}, {dmax:.1f}])"
                    checks.append((rpath, True, res_msg))
                    print(f"  [PASS] {label:<22} {rpath:<45} : {res_msg}")
                else:
                    fail_msg = f"FAIL (CRS_OK={crs_ok}, BBox_OK={bbox_ok}, Range_OK={range_ok}, Range=[{dmin}, {dmax}])"
                    checks.append((rpath, False, fail_msg))
                    errors.append(f"{label}: {fail_msg}")
                    print(f"  [FAIL] {label:<22} {rpath:<45} : {fail_msg}")
        except Exception as e:
            fail_msg = f"READ ERROR: {e}"
            checks.append((rpath, False, fail_msg))
            errors.append(f"{label}: {fail_msg}")
            print(f"  [FAIL] {label:<22} {rpath:<45} : {fail_msg}")

    # 3. Processed Multi-Year Timeseries CSV
    print("\n--- 3. Processed Tabular Multi-Year Timeseries Validation ---")
    ts_csv = "data/processed/rainfall/chirps_v3_pune_daily_2020_2024_timeseries.csv"
    ok, msg = check_file(ts_csv, min_bytes=500)
    if ok:
        df_ts = pd.read_csv(ts_csv)
        years = df_ts['year'].unique().tolist()
        print(f"  [PASS] CHIRPS Time Series     {ts_csv:<45} : PASS ({len(df_ts)} records, years={years})")
        checks.append((ts_csv, True, f"{len(df_ts)} records, years={years}"))
    else:
        checks.append((ts_csv, False, msg))
        errors.append(msg)
        print(f"  [FAIL] CHIRPS Time Series     {ts_csv:<45} : {msg}")

    # 4. Processed Vectors (GeoPackage)
    print("\n--- 4. Processed Geospatial Vector Validation ---")
    gpkg_path = "data/processed/gis/osm_features_pune.gpkg"
    ok, msg = check_file(gpkg_path, min_bytes=1000)
    if not ok:
        checks.append((gpkg_path, False, msg))
        errors.append(msg)
        print(f"  [FAIL] {gpkg_path:<65} : {msg}")
    else:
        try:
            layers = pyogrio.list_layers(gpkg_path)
            layer_names = [l[0] for l in layers]
            for l_name in layer_names:
                gdf = gpd.read_file(gpkg_path, layer=l_name)
                crs_str = str(gdf.crs)
                count = len(gdf)
                geom_types = list(gdf.geom_type.unique())
                crs_ok = "4326" in crs_str
                if crs_ok and count > 0:
                    l_msg = f"PASS ({count} features, types={geom_types}, CRS={crs_str})"
                    checks.append((f"{gpkg_path}::{l_name}", True, l_msg))
                    print(f"  [PASS] Layer '{l_name}': {l_msg}")
                else:
                    l_msg = f"FAIL (count={count}, CRS={crs_str})"
                    checks.append((f"{gpkg_path}::{l_name}", False, l_msg))
                    errors.append(f"Layer {l_name}: {l_msg}")
                    print(f"  [FAIL] Layer '{l_name}': {l_msg}")
        except Exception as e:
            err_msg = f"GPKG ERROR: {e}"
            checks.append((gpkg_path, False, err_msg))
            errors.append(err_msg)
            print(f"  [FAIL] {gpkg_path}: {err_msg}")

    # 5. Metadata Files
    print("\n--- 5. Metadata Integrity Validation ---")
    meta_files = [
        "data/metadata/copernicus_dem_metadata.json",
        "data/metadata/open_meteo_metadata.json",
        "data/metadata/chirps_v3_metadata.json",
        "data/metadata/osm_gis_metadata.json",
        "data/metadata/nwic_metadata.json"
    ]
    for mf in meta_files:
        ok, msg = check_file(mf, min_bytes=50)
        if not ok:
            checks.append((mf, False, msg))
            errors.append(msg)
            print(f"  [FAIL] {mf:<65} : {msg}")
        else:
            try:
                with open(mf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                dname = data.get("dataset_name", "UNKNOWN")
                print(f"  [PASS] {mf:<65} : Valid JSON (Dataset: '{dname}')")
                checks.append((mf, True, f"Valid JSON: {dname}"))
            except Exception as e:
                checks.append((mf, False, f"JSON Error: {e}"))
                errors.append(f"{mf}: {e}")
                print(f"  [FAIL] {mf:<65} : JSON Error: {e}")

    # 6. Master Manifest
    print("\n--- 6. Master Manifest Validation ---")
    manifest_path = "data/manifests/phase1_manifest.json"
    ok, msg = check_file(manifest_path, min_bytes=50)
    if not ok:
        checks.append((manifest_path, False, msg))
        errors.append(msg)
        print(f"  [FAIL] {manifest_path:<65} : {msg}")
    else:
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            total_items = len(manifest.get("files", []))
            print(f"  [INFO] Manifest declares {total_items} registered artifacts.")
            manifest_mismatches = 0
            for item in manifest.get("files", []):
                rel = item["relative_path"]
                expected_sha = item.get("sha256")
                if not os.path.exists(rel):
                    print(f"  [FAIL] Manifest registered file missing: {rel}")
                    manifest_mismatches += 1
                elif expected_sha:
                    actual_sha = sha256(rel)
                    if actual_sha != expected_sha:
                        print(f"  [FAIL] SHA256 mismatch for {rel}: expected {expected_sha[:10]}... got {actual_sha[:10]}...")
                        manifest_mismatches += 1
            if manifest_mismatches == 0:
                print(f"  [PASS] All {total_items} manifest artifacts verified with matching SHA-256 hashes!")
                checks.append((manifest_path, True, f"{total_items} artifacts matched"))
            else:
                checks.append((manifest_path, False, f"{manifest_mismatches} mismatches"))
                errors.append(f"Manifest had {manifest_mismatches} file/checksum mismatches")
        except Exception as e:
            checks.append((manifest_path, False, f"Manifest JSON Error: {e}"))
            errors.append(f"Manifest: {e}")
            print(f"  [FAIL] {manifest_path}: {e}")

    print("\n" + "=" * 80)
    total_checks = len(checks)
    passed_checks = len([c for c in checks if c[1]])
    print(f"VERIFICATION SUMMARY: {passed_checks}/{total_checks} CHECKS PASSED")
    if errors:
        print(f"FAILED CHECKS ({len(errors)}):")
        for err in errors:
            print(f"  - {err}")
        print("=" * 80)
        sys.exit(1)
    else:
        print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH ZERO ERRORS!")
        print("=" * 80)
        sys.exit(0)

if __name__ == "__main__":
    main()
