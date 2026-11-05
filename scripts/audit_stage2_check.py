"""Independent verification script for Phase 1 Stage 2 implementation."""
import os
import sys
import pandas as pd
from zoneinfo import ZoneInfo
from sqlalchemy import text

# Ensure backend in python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.database import engine

IST = ZoneInfo("Asia/Kolkata")

print("=================================================================")
print("FLOOD-X STAGE 2.1 INDEPENDENT AUDIT EXECUTION")
print("=================================================================")

# 1. CWPRS Raw vs Ingested around 08:30 IST reset on 2024-07-25
raw_cwprs_file = os.path.join(PROJECT_ROOT, "data", "raw", "rainfall", "rainfall_tel_hr_cwprs_mh_sample.csv")
df_cwprs = pd.read_csv(raw_cwprs_file)
df_cwprs["parsed_dt"] = pd.to_datetime(df_cwprs["Data Acquisition Time"], format="%d-%m-%Y %H:%M")
df_cwprs = df_cwprs.sort_values("parsed_dt").reset_index(drop=True)

# Select rows from 08:10 to 08:45 on 2024-07-25
sample_window = df_cwprs[(df_cwprs["parsed_dt"] >= "2024-07-25 08:10") & (df_cwprs["parsed_dt"] <= "2024-07-25 08:45")]

print("\n--- CWPRS ORIGINAL CSV AROUND 08:30 IST RESET ---")
for _, r in sample_window.iterrows():
    print(f"Time: {r['Data Acquisition Time']} | Cumulative: {r['Telemetry Hourly Rainfall (mm)']} mm")

with engine.connect() as conn:
    print("\n--- DATABASE CORRESPONDING OBSERVATIONS (UTC) ---")
    db_recs = conn.execute(text("""
        SELECT observation_time, measurement_type, rainfall_value, quality_flag
        FROM rainfall_observations
        WHERE station_name LIKE '%CWPRS%'
          AND observation_time >= '2024-07-25 02:40:00+00' 
          AND observation_time <= '2024-07-25 03:15:00+00'
        ORDER BY observation_time, measurement_type;
    """)).fetchall()
    for r in db_recs:
        print(f"UTC: {r[0]} | Type: {r[1]:<17} | Val: {r[2]:>6.2f} mm | Quality: {r[3]}")

    print("\n--- HOURLY AGGREGATIONS AROUND RESET ---")
    hourly_recs = conn.execute(text("""
        SELECT observation_time, rainfall_value, quality_flag, metadata_json
        FROM rainfall_observations
        WHERE station_name LIKE '%CWPRS%'
          AND measurement_type = 'HOURLY_ACCUMULATION'
          AND observation_time IN ('2024-07-25 02:00:00+00', '2024-07-25 03:00:00+00')
        ORDER BY observation_time;
    """)).fetchall()
    for h in hourly_recs:
        print(f"UTC: {h[0]} | Hourly Val: {h[1]} mm | Meta: {h[3]}")

    print("\n--- CWC REGIONAL REFERENCE VERIFICATION ---")
    total_cwc = conn.execute(text("SELECT count(*) FROM river_level_observations WHERE station_name LIKE '%Ankali Bridge%';")).scalar()
    reg_ref_cwc = conn.execute(text("SELECT count(*) FROM river_level_observations WHERE station_name LIKE '%Ankali Bridge%' AND geographic_relevance = 'REGIONAL_REFERENCE_ONLY';")).scalar()
    print(f"Total CWC Ankali Bridge records: {total_cwc}")
    print(f"REGIONAL_REFERENCE_ONLY count: {reg_ref_cwc}")
    assert total_cwc == reg_ref_cwc, "FAIL: Not all CWC records are marked REGIONAL_REFERENCE_ONLY"
    print("Verification: PASS - 100% of Ankali Bridge records are REGIONAL_REFERENCE_ONLY.")

    print("\n--- WEATHER OBSERVED VS FORECAST VERIFICATION ---")
    weather_cats = dict(conn.execute(text("SELECT data_category, count(*) FROM weather_observations GROUP BY data_category;")).fetchall())
    print(f"Weather observations by category: {weather_cats}")
    assert weather_cats.get("OBSERVED", 0) == 288, f"Expected 288 observed, got {weather_cats.get('OBSERVED')}"
    assert weather_cats.get("FORECAST", 0) == 168, f"Expected 168 forecast, got {weather_cats.get('FORECAST')}"
    print("Verification: PASS - Weather observed (reanalysis) and forecast categories strictly distinct.")

    print("\n--- CHIRPS DATES AND SPATIAL VERIFICATION ---")
    chirps_recs = conn.execute(text("""
        SELECT observation_time, rainfall_value, latitude, longitude, metadata_json
        FROM rainfall_observations
        WHERE station_name = 'CHIRPS_V3_PUNE_BASIN_AGGREGATE'
        ORDER BY observation_time;
    """)).fetchall()
    print(f"CHIRPS total records: {len(chirps_recs)}")
    print(f"Date range: {chirps_recs[0][0].date()} to {chirps_recs[-1][0].date()}")
    print(f"Coordinates: lat={chirps_recs[0][2]}, lon={chirps_recs[0][3]}")
    assert len(chirps_recs) == 25, "Expected 25 CHIRPS records"
    print("Verification: PASS - CHIRPS records accurately match 25 monsoon peak days.")

# Duplicate Ingestion / Idempotency Test
print("\n--- DUPLICATE INGESTION IDEMPOTENCY AUDIT ---")
from app.core.database import SessionLocal
from app.services.ingestion.chirps_service import CHIRPSIngestionService
from app.services.ingestion.osm_service import OSMIngestionService

with engine.connect() as conn:
    rain_before = conn.execute(text("SELECT count(*) FROM rainfall_observations WHERE station_name = 'CHIRPS_V3_PUNE_BASIN_AGGREGATE';")).scalar()
    spatial_before = conn.execute(text("SELECT count(*) FROM spatial_features;")).scalar()

db = SessionLocal()
try:
    chirps_res = CHIRPSIngestionService().ingest(db)
    osm_res = OSMIngestionService().ingest(db)
finally:
    db.close()

with engine.connect() as conn:
    rain_after = conn.execute(text("SELECT count(*) FROM rainfall_observations WHERE station_name = 'CHIRPS_V3_PUNE_BASIN_AGGREGATE';")).scalar()
    spatial_after = conn.execute(text("SELECT count(*) FROM spatial_features;")).scalar()

print(f"CHIRPS: Before={rain_before}, Ingested={chirps_res['records_inserted']}, Skipped={chirps_res['records_skipped']}, After={rain_after}")
print(f"OSM:    Before={spatial_before}, Ingested={osm_res['records_inserted']}, Skipped={osm_res['records_skipped']}, After={spatial_after}")
assert rain_before == rain_after, "FAIL: CHIRPS count changed!"
assert spatial_before == spatial_after, "FAIL: Spatial count changed!"
print("Verification: PASS - Duplicate ingestion causes zero duplicate records (100% skipped).")

# Step 3: PostGIS Verification
print("\n--- POSTGIS SPATIAL INTEGRITY AUDIT ---")
import geopandas as gpd

gpkg_path = os.path.join(PROJECT_ROOT, "data", "processed", "gis", "osm_features_pune.gpkg")

with engine.connect() as conn:
    # 1. Check ST_IsValid on all 1,307 geometries
    invalid_count = conn.execute(text("SELECT count(*) FROM spatial_features WHERE NOT ST_IsValid(geom);")).scalar()
    print(f"Invalid geometries count: {invalid_count}")
    assert invalid_count == 0, f"Found {invalid_count} invalid geometries!"

    # 2. Check ST_SRID on all 1,307 geometries
    non_4326 = conn.execute(text("SELECT count(*) FROM spatial_features WHERE ST_SRID(geom) != 4326;")).scalar()
    print(f"Non-4326 SRID count: {non_4326}")
    assert non_4326 == 0, f"Found {non_4326} non-4326 geometries!"

    # 3. Geometry types breakdown
    geom_types = dict(conn.execute(text("SELECT ST_GeometryType(geom), count(*) FROM spatial_features GROUP BY ST_GeometryType(geom);")).fetchall())
    print(f"PostGIS Geometry Types: {geom_types}")

    # 4. Spatial bounding box of all features
    extent = conn.execute(text("""
        SELECT ST_XMin(ST_Extent(geom)), ST_YMin(ST_Extent(geom)), 
               ST_XMax(ST_Extent(geom)), ST_YMax(ST_Extent(geom))
        FROM spatial_features;
    """)).fetchone()
    print(f"PostGIS Total Spatial Extent (WGS84): West={extent[0]:.4f}, South={extent[1]:.4f}, East={extent[2]:.4f}, North={extent[3]:.4f}")

    # 5. Spatial query test: Find bridges crossing or intersecting waterways
    bridge_waterway_proximity = conn.execute(text("""
        SELECT b.name as bridge_name, w.name as waterway_name, ST_Distance(b.geom, w.geom) as dist_deg
        FROM spatial_features b
        JOIN spatial_features w ON w.feature_type = 'WATERWAY'
        WHERE b.feature_type = 'BRIDGE' AND b.name IS NOT NULL AND w.name IS NOT NULL
        ORDER BY ST_Distance(b.geom, w.geom) ASC
        LIMIT 5;
    """)).fetchall()
    print("\nSample Proximity Query (Bridges near Rivers):")
    for b in bridge_waterway_proximity:
        print(f" - Bridge: {b[0]} | Waterway: {b[1]} | Dist: {b[2]:.6f} deg")

    # 6. Verify feature counts against GeoPackage layers
    layer_map = {
        "waterways": "WATERWAY",
        "bridges": "BRIDGE",
        "healthcare_facilities": "HEALTHCARE",
        "education_facilities": "EDUCATION",
        "civic_and_community_facilities": "COMMUNITY_CIVIC",
        "evacuation_road_network": "EVACUATION_ROAD",
    }
    print("\nLayer by Layer Count Verification (GPKG vs DB):")
    for lyr_name, feat_type in layer_map.items():
        gdf = gpd.read_file(gpkg_path, layer=lyr_name)
        gpkg_cnt = len(gdf)
        db_cnt = conn.execute(text(f"SELECT count(*) FROM spatial_features WHERE feature_type = '{feat_type}';")).scalar()
        print(f" - {lyr_name:<30} GPKG: {gpkg_cnt:>4} | DB: {db_cnt:>4} | Match: {gpkg_cnt == db_cnt}")
        assert gpkg_cnt == db_cnt, f"Count mismatch for {lyr_name}: {gpkg_cnt} vs {db_cnt}"

    # 7. Check preservation of OSM attributes and osm_id
    sample_feat = conn.execute(text("""
        SELECT feature_type, osm_id, name, properties_json 
        FROM spatial_features 
        WHERE osm_id IS NOT NULL AND properties_json IS NOT NULL 
        LIMIT 3;
    """)).fetchall()
    print("\nSample OSM Preserved Attributes:")
    for sf in sample_feat:
        print(f" - Type: {sf[0]} | OSM ID: {sf[1]} | Name: {sf[2]} | Properties: {list(sf[3].keys())[:4]}")
    print("Verification: PASS - All geometries valid, SRID 4326, layer counts match GPKG, OSM attributes preserved.")

# Step 4: Comprehensive API Endpoints Audit
print("\n--- COMPREHENSIVE REST API AUDIT ---")
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

endpoints_to_test = [
    # Route, query params, expected status, check fn
    ("/api/v1/ingestion/overview", {}, 200, lambda d: d["counts"]["data_sources"] >= 6),
    ("/api/v1/ingestion/sources", {}, 200, lambda d: len(d) >= 6),
    ("/api/v1/ingestion/sources?source_type=GROUND_TELEMETRY", {}, 200, lambda d: len(d) == 1 and d[0]["source_name"] == "CWPRS_KHADAKWASLA"),
    ("/api/v1/ingestion/sources?source_type=NONEXISTENT", {}, 200, lambda d: len(d) == 0),
    ("/api/v1/ingestion/logs?limit=5", {}, 200, lambda d: len(d) <= 5 and len(d) > 0),
    ("/api/v1/environment/rainfall?limit=5", {}, 200, lambda d: d["total"] > 50000 and len(d["items"]) == 5),
    ("/api/v1/environment/rainfall?measurement_type=5MIN_CUMULATIVE&limit=5", {}, 200, lambda d: d["total"] == 24211),
    ("/api/v1/environment/rainfall?measurement_type=DAILY_ACCUMULATION", {}, 200, lambda d: d["total"] == 25),
    ("/api/v1/environment/rainfall?station_name=NON_EXISTENT_STATION", {}, 200, lambda d: d["total"] == 0 and len(d["items"]) == 0),
    ("/api/v1/environment/rainfall/summary", {}, 200, lambda d: d["cwprs_24h_cumulative_peak_mm"] == 145.6),
    ("/api/v1/environment/weather?limit=5", {}, 200, lambda d: d["total"] == 456),
    ("/api/v1/environment/weather?data_category=OBSERVED", {}, 200, lambda d: d["total"] == 288),
    ("/api/v1/environment/weather?data_category=FORECAST", {}, 200, lambda d: d["total"] == 168),
    ("/api/v1/environment/river-levels?limit=5", {}, 200, lambda d: d["total"] == 32655),
    ("/api/v1/environment/river-levels?geographic_relevance=REGIONAL_REFERENCE_ONLY&limit=5", {}, 200, lambda d: d["total"] == 32655),
    ("/api/v1/environment/river-levels?geographic_relevance=WITHIN_PILOT_BASIN", {}, 200, lambda d: d["total"] == 0),
    ("/api/v1/gis/summary", {}, 200, lambda d: d["total_features"] == 1307),
    ("/api/v1/gis/features?limit=5", {}, 200, lambda d: d["total"] == 1307 and len(d["items"]) == 5),
    ("/api/v1/gis/features?feature_type=WATERWAY", {}, 200, lambda d: d["total"] == 21),
    ("/api/v1/gis/features?feature_type=BRIDGE", {}, 200, lambda d: d["total"] == 158),
    ("/api/v1/gis/features?feature_type=COMMUNITY_CIVIC", {}, 200, lambda d: d["total"] == 7),
    ("/api/v1/data-quality/summary", {}, 200, lambda d: d["total_issues"] >= 8),
    ("/api/v1/data-quality/issues?severity=HIGH", {}, 200, lambda d: len(d) >= 1 and d[0]["issue_type"] == "GEOGRAPHIC_DISPLACEMENT"),
    ("/api/v1/data-quality/issues?severity=UNKNOWN_SEV", {}, 200, lambda d: len(d) == 0),
]

print("Executing API test matrix (24 endpoints & filter permutations)...")
for path, params, exp_status, check_fn in endpoints_to_test:
    res = client.get(path, params=params if params else None)
    assert res.status_code == exp_status, f"FAIL: {path} returned {res.status_code}, expected {exp_status}"
    data = res.json()
    assert check_fn(data), f"FAIL: {path} validation assertion failed! Data: {data}"
    print(f" - [PASS] GET {path}")

# Test Ingestion Trigger and Error Handling
print("\nTesting Ingestion Trigger API & Failure Handling:")
run_bad = client.post("/api/v1/ingestion/run", json={"source": "invalid_source_xyz"})
print(f" - Bad source status: {run_bad.status_code} | Error: {run_bad.json()['error']['message']}")
assert run_bad.status_code == 500, f"Expected 500 on invalid source, got {run_bad.status_code}"

run_good = client.post("/api/v1/ingestion/run", json={"source": "elevation"})
print(f" - Valid source status: {run_good.status_code} | Message: {run_good.json()['message']}")
assert run_good.status_code == 200, f"Expected 200 on valid source, got {run_good.status_code}"
print("Verification: PASS - All 26 API verification tests succeeded.")

# Step 5: Raw File SHA-256 Hash Verification against Stage 1.1 Manifest
print("\n--- RAW DATASETS SHA-256 HASH INTEGRITY AUDIT ---")
import json
import hashlib

manifest_file = os.path.join(PROJECT_ROOT, "data", "manifests", "phase1_manifest.json")
with open(manifest_file, "r") as f:
    manifest = json.load(f)

raw_files = [item for item in manifest.get("files", []) if item.get("category", "").startswith("raw_")]
print(f"Total raw files tracked in manifest: {len(raw_files)}")

mismatches = []
for item in raw_files:
    fpath = os.path.join(PROJECT_ROOT, item["relative_path"])
    exp_hash = item["sha256"]
    fname = item["filename"]
    if not os.path.exists(fpath):
        print(f" - {fname:<45}: MISSING [FAIL]")
        mismatches.append((fname, "MISSING", exp_hash))
        continue

    hasher = hashlib.sha256()
    with open(fpath, "rb") as bf:
        while chunk := bf.read(65536):
            hasher.update(chunk)
    curr_hash = hasher.hexdigest()

    match = (curr_hash.lower() == exp_hash.lower())
    status = "MATCH [PASS]" if match else "MISMATCH [FAIL]"
    print(f" - {fname:<45}: {status}")
    if not match:
        mismatches.append((fname, curr_hash, exp_hash))

print(f"Total Raw File Mismatches: {len(mismatches)}")
assert len(mismatches) == 0, f"Raw files were modified! {mismatches}"
print("Verification: PASS - All raw dataset files are byte-for-byte unmodified.")
