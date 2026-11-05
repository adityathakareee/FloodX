"""
Generates the comprehensive Phase 1 Stage 1 Master Dataset Manifest
with SHA-256 checksums, coordinate references, bounding boxes, file sizes,
and provenance for FLOOD-X.
"""
import os
import json
import time
import hashlib
import rasterio
import pyogrio

STUDY_BOUNDS_PROVISIONAL = [73.30, 18.25, 74.25, 18.85]
CENTROID_PUNE = [18.5204, 73.8567]

def sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== Generating FLOOD-X Phase 1 Stage 1 Master Manifest ===")
    
    files = []
    
    # 1. Raw Elevation
    for f in ["Copernicus_DSM_COG_30_N18_00_E073_00_DEM.tif", "Copernicus_DSM_COG_30_N18_00_E074_00_DEM.tif"]:
        rel = f"data/raw/elevation/{f}"
        if os.path.exists(rel):
            files.append({
                "category": "raw_raster",
                "subdomain": "elevation",
                "filename": f,
                "relative_path": rel,
                "size_bytes": os.path.getsize(rel),
                "sha256": sha256(rel),
                "format": "GeoTIFF (Cloud-Optimized)",
                "provider": "European Space Agency (ESA) / AWS Open Data",
                "license": "Copernicus Open Access",
                "crs": "EPSG:4326",
                "resolution": "90m (3 arc-seconds)",
                "surface_type": "Digital Surface Model (DSM)"
            })

    # 2. Raw Weather
    for f, desc in [
        ("open_meteo_forecast_pune.json", "7-Day Hourly Meteorological Forecast & Dual-Layer Soil Moisture"),
        ("open_meteo_historical_202407_pune.json", "July 2024 Severe Monsoon Flood Event Telemetry (July 20-31, 2024)")
    ]:
        rel = f"data/raw/weather/{f}"
        if os.path.exists(rel):
            files.append({
                "category": "raw_telemetry",
                "subdomain": "weather_and_soil",
                "filename": f,
                "relative_path": rel,
                "size_bytes": os.path.getsize(rel),
                "sha256": sha256(rel),
                "format": "JSON",
                "provider": "Open-Meteo",
                "license": "CC BY 4.0 / Open Data",
                "description": desc,
                "spatial_focus": "Pune City (18.5204° N, 73.8567° E)"
            })

    # 3. Raw Rainfall
    for f, desc, obs_date in [
        ("chirps-v3.0.sat.2024.07.25.tif", "CHIRPS v3 Daily Satellite Precipitation (Peak Monsoon Flood Day)", "2024-07-25"),
        ("chirps-v3.0.sat.2026.01.01.tif", "CHIRPS v3 Daily Satellite Precipitation (Dry Season Reference)", "2026-01-01"),
        ("rainfall_tel_hr_cwprs_mh_sample.csv", "CWPRS Khadakwasla 5-Minute Telemetry Rainfall (24-hr Cumulative)", "2024-2025")
    ]:
        rel = f"data/raw/rainfall/{f}"
        if os.path.exists(rel):
            files.append({
                "category": "raw_rainfall",
                "subdomain": "precipitation",
                "filename": f,
                "relative_path": rel,
                "size_bytes": os.path.getsize(rel),
                "sha256": sha256(rel),
                "format": "GeoTIFF" if f.endswith(".tif") else "CSV",
                "provider": "UCSB CHC" if f.endswith(".tif") else "National Water Informatics Centre (NWIC) / CWPRS",
                "license": "Public Domain / GODL India",
                "description": desc,
                "observation_coverage": obs_date
            })

    # 4. Raw River Water Level
    f = "rwl_tel_hr_maharashtra_sw_007_sample.csv"
    rel = f"data/raw/river_levels/{f}"
    if os.path.exists(rel):
        files.append({
            "category": "raw_hydrology",
            "subdomain": "river_levels",
            "filename": f,
            "relative_path": rel,
            "size_bytes": os.path.getsize(rel),
            "sha256": sha256(rel),
            "format": "CSV",
            "provider": "NWIC / Maharashtra Surface Water Department",
            "license": "Government Open Data License - India (GODL)",
            "description": "Hourly River Water Level Telemetry (Station: Ankali Bridge, Sangli; Krishna Basin 007)",
            "geographic_classification": "Regional reference only (Outside pilot basin; 205.3 km south of Pune)"
        })

    # 5. Raw GIS
    for f in ["pune_core_deccan.osm", "pune_sangam_confluence.osm", "pune_upstream_mutha.osm", "osm_raw_layers_pune.gpkg"]:
        rel = f"data/raw/gis/{f}"
        if os.path.exists(rel):
            files.append({
                "category": "raw_gis",
                "subdomain": "infrastructure",
                "filename": f,
                "relative_path": rel,
                "size_bytes": os.path.getsize(rel),
                "sha256": sha256(rel),
                "format": "OSM XML" if f.endswith(".osm") else "GeoPackage",
                "provider": "OpenStreetMap Foundation & Contributors",
                "license": "ODbL 1.0"
            })

    # 6. Processed Rasters
    for f, ptype, units, min_max in [
        ("copernicus_glo90_pune_basin_dem.tif", "Cropped Digital Surface Model (DSM)", "meters", "0.0m - 1396.6m"),
        ("copernicus_glo90_pune_basin_slope.tif", "Topographic Slope Raster", "degrees", "0.00° - 69.93°"),
        ("chirps_v3_pune_basin_cropped.tif", "Cropped Peak Flood Day Precipitation (2024-07-25)", "mm/day", "16.22 - 344.00 mm/day"),
        ("chirps_v3_pune_july2024_flood_sequence.tif", "Multi-Band 2024 Flood Sequence (July 22-26, 2024)", "mm/day", "5 daily bands")
    ]:
        rel = f"data/processed/elevation/{f}" if "copernicus" in f else f"data/processed/rainfall/{f}"
        if os.path.exists(rel):
            with rasterio.open(rel) as src:
                w, h = src.width, src.height
                crs = str(src.crs)
            files.append({
                "category": "processed_raster",
                "subdomain": "elevation" if "copernicus" in f else "rainfall",
                "filename": f,
                "relative_path": rel,
                "size_bytes": os.path.getsize(rel),
                "sha256": sha256(rel),
                "format": "GeoTIFF (LZW Compressed)",
                "product_type": ptype,
                "dimensions": [w, h],
                "crs": crs,
                "bounds_wgs84": STUDY_BOUNDS_PROVISIONAL,
                "unit": units,
                "valid_range": min_max
            })

    # 7. Processed Multi-Year Timeseries CSV
    f_ts = "chirps_v3_pune_daily_2020_2024_timeseries.csv"
    rel_ts = f"data/processed/rainfall/{f_ts}"
    if os.path.exists(rel_ts):
        files.append({
            "category": "processed_tabular",
            "subdomain": "rainfall",
            "filename": f_ts,
            "relative_path": rel_ts,
            "size_bytes": os.path.getsize(rel_ts),
            "sha256": sha256(rel_ts),
            "format": "CSV",
            "product_type": "Multi-Year Daily Monsoon Rainfall Time Series (2020-2024)",
            "unit": "mm/day",
            "observation_epochs": "2020, 2021, 2022, 2023, 2024 peak monsoon flood periods"
        })

    # 8. Processed GIS GeoPackage
    f_gpkg = "osm_features_pune.gpkg"
    rel_gpkg = f"data/processed/gis/{f_gpkg}"
    if os.path.exists(rel_gpkg):
        layers = pyogrio.list_layers(rel_gpkg)
        files.append({
            "category": "processed_vector",
            "subdomain": "gis",
            "filename": f_gpkg,
            "relative_path": rel_gpkg,
            "size_bytes": os.path.getsize(rel_gpkg),
            "sha256": sha256(rel_gpkg),
            "format": "OGC GeoPackage (GPKG)",
            "crs": "EPSG:4326",
            "layers": [l[0] for l in layers],
            "attribution": "© OpenStreetMap contributors (ODbL). Arterial road backbone; civic halls are mapped community facilities, not certified flood shelters."
        })

    manifest = {
        "manifest_version": "1.1.0",
        "project": "FLOOD-X",
        "stage": "Stage 1.1: Data Quality & Geographic Coverage Audit",
        "generated_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pilot_region": {
            "name": "Pune / Mula-Mutha River Basin",
            "centroid_wgs84": CENTROID_PUNE,
            "provisional_catchment_bounds_wgs84": {
                "west": STUDY_BOUNDS_PROVISIONAL[0],
                "south": STUDY_BOUNDS_PROVISIONAL[1],
                "east": STUDY_BOUNDS_PROVISIONAL[2],
                "north": STUDY_BOUNDS_PROVISIONAL[3]
            },
            "boundary_status": "Provisional study boundary covering Western Ghats upper catchments (Khadakwasla, Panshet, Varasgaon, Mulshi) through PMC/PCMC urban core to Bhima confluence."
        },
        "summary": {
            "total_artifacts": len(files),
            "raw_artifacts": len([f for f in files if "raw" in f["category"]]),
            "processed_artifacts": len([f for f in files if "processed" in f["category"]]),
            "crs_standard": "WGS 84 (EPSG:4326)"
        },
        "files": files
    }

    manifest_path = "data/manifests/phase1_manifest.json"
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Master manifest v1.1 written to {manifest_path} ({len(files)} registered artifacts).")

if __name__ == "__main__":
    main()
