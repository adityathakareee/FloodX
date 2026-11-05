"""Acquire 5-year continuous hourly historical weather for Pune (2020-2024) from Open-Meteo Archive API."""
import os
import sys
import hashlib
import json
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "raw", "historical_weather")
METADATA_DIR = os.path.join(PROJECT_ROOT, "data", "metadata")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

# Query parameters for Pune centroid
LAT = 18.5204
LON = 73.8567
START_DATE = "2020-01-01"
END_DATE = "2024-12-31"

HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
]

api_url = (
    f"https://archive-api.open-meteo.com/v1/archive?"
    f"latitude={LAT}&longitude={LON}&"
    f"start_date={START_DATE}&end_date={END_DATE}&"
    f"hourly={','.join(HOURLY_VARS)}&"
    f"timezone=UTC"
)

output_file = os.path.join(OUTPUT_DIR, f"open_meteo_pune_hourly_2020_2024.json")

print(f"Querying Open-Meteo Historical Archive API for Pune ({LAT}N, {LON}E)...")
print(f"Date range: {START_DATE} to {END_DATE} (5 continuous years, UTC)")
print(f"URL: {api_url}")

req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
with urllib.request.urlopen(req, timeout=90) as resp, open(output_file, "wb") as f:
    while chunk := resp.read(65536):
        f.write(chunk)

file_size = os.path.getsize(output_file)
print(f"[OK] Downloaded {file_size:,} bytes to {output_file}")

# Calculate SHA-256
h = hashlib.sha256()
with open(output_file, "rb") as cf:
    while chunk := cf.read(65536):
        h.update(chunk)
sha256_hash = h.hexdigest()
print(f"SHA-256: {sha256_hash}")

# Verify JSON structure
with open(output_file, "r") as jf:
    data = json.load(jf)
    hourly = data.get("hourly", {})
    t_len = len(hourly.get("time", []))
    print(f"Total hourly timestamps returned: {t_len:,} hours")

# Save metadata
meta = {
    "dataset_name": "OPEN_METEO_HISTORICAL_REANALYSIS_PUNE_2020_2024",
    "provider": "Open-Meteo / ECMWF ERA5 & ERA5-Land Reanalysis",
    "latitude": LAT,
    "longitude": LON,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "timezone": "UTC",
    "variables": HOURLY_VARS,
    "total_hours": t_len,
    "file_path": output_file,
    "file_size_bytes": file_size,
    "sha256": sha256_hash,
    "license": "CC-BY 4.0 (Attribution: Open-Meteo & Copernicus Climate Change Service)",
    "download_timestamp_utc": "2026-11-04T15:25:00Z",
}

meta_path = os.path.join(METADATA_DIR, "open_meteo_historical_2020_2024_metadata.json")
with open(meta_path, "w", encoding="utf-8") as mf:
    json.dump(meta, mf, indent=2)

print(f"Metadata saved to {meta_path}")
print("Historical weather acquisition completed successfully!")

