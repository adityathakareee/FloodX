"""
Acquires and validates real current, forecast, and historical environmental/weather data
from Open-Meteo for the Pune / Mula-Mutha River Basin study area.
"""
import os
import json
import time
import hashlib
import requests

RAW_DIR = os.path.abspath("data/raw/weather")
METADATA_DIR = os.path.abspath("data/metadata")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

PUNE_COORDS = {"latitude": 18.5204, "longitude": 73.8567}

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def acquire_forecast():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": PUNE_COORDS["latitude"],
        "longitude": PUNE_COORDS["longitude"],
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "precipitation_probability",
            "rain",
            "weather_code",
            "pressure_msl",
            "wind_speed_10m",
            "wind_direction_10m",
            "soil_temperature_0_to_7cm",
            "soil_moisture_0_to_7cm",
            "soil_moisture_7_to_28cm"
        ],
        "daily": [
            "precipitation_sum",
            "precipitation_hours",
            "precipitation_probability_max",
            "temperature_2m_max",
            "temperature_2m_min"
        ],
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "weather_code",
            "wind_speed_10m",
            "wind_direction_10m"
        ],
        "timezone": "Asia/Kolkata"
    }
    
    headers = {"User-Agent": "FLOODX-Academic-Research/1.0 (Pune Flood Intelligence)"}
    print(f"Fetching forecast from {url}...")
    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    data = r.json()
    
    out_path = os.path.join(RAW_DIR, "open_meteo_forecast_pune.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Forecast saved to {out_path} ({os.path.getsize(out_path)} bytes)")
    return out_path, data

def acquire_historical():
    url = "https://archive-api.open-meteo.com/v1/archive"
    # Severe July 2024 monsoon flood week in Pune
    params = {
        "latitude": PUNE_COORDS["latitude"],
        "longitude": PUNE_COORDS["longitude"],
        "start_date": "2024-07-20",
        "end_date": "2024-07-31",
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "pressure_msl",
            "wind_speed_10m",
            "wind_direction_10m",
            "soil_moisture_0_to_7cm",
            "soil_moisture_7_to_28cm"
        ],
        "daily": [
            "precipitation_sum",
            "precipitation_hours",
            "temperature_2m_max",
            "temperature_2m_min"
        ],
        "timezone": "Asia/Kolkata"
    }
    
    headers = {"User-Agent": "FLOODX-Academic-Research/1.0 (Pune Flood Intelligence)"}
    print(f"Fetching historical archive from {url}...")
    r = requests.get(url, params=params, headers=headers, timeout=25)
    r.raise_for_status()
    data = r.json()
    
    out_path = os.path.join(RAW_DIR, "open_meteo_historical_202407_pune.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Historical weather saved to {out_path} ({os.path.getsize(out_path)} bytes)")
    return out_path, data

def validate_weather(data, label):
    hourly = data.get("hourly", {})
    timestamps = hourly.get("time", [])
    precip = hourly.get("precipitation", [])
    soil_m = hourly.get("soil_moisture_0_to_7cm", [])
    
    non_null_precip = [p for p in precip if p is not None]
    non_null_soil = [s for s in soil_m if s is not None]
    
    precip_max = max(non_null_precip) if non_null_precip else 0.0
    soil_mean = sum(non_null_soil) / len(non_null_soil) if non_null_soil else 0.0
    
    print(f"[{label}] Timesteps: {len(timestamps)}, "
          f"Precipitation Max: {precip_max} mm/hr, "
          f"Soil Moisture 0-7cm Mean: {soil_mean:.3f} m³/m³")
    
    return {
        "timesteps_count": len(timestamps),
        "start_time": timestamps[0] if timestamps else None,
        "end_time": timestamps[-1] if timestamps else None,
        "precipitation_max_mm_per_hr": precip_max,
        "soil_moisture_mean_m3_per_m3": soil_mean,
        "variables_present": list(hourly.keys())
    }

def main():
    print("=== Open-Meteo Weather Data Acquisition ===")
    fc_path, fc_data = acquire_forecast()
    hist_path, hist_data = acquire_historical()
    
    fc_val = validate_weather(fc_data, "Forecast")
    hist_val = validate_weather(hist_data, "Historical (July 2024 Flood Event)")
    
    metadata = {
        "dataset_name": "Open-Meteo Weather & Environmental Telemetry",
        "provider": "Open-Meteo (open-meteo.com)",
        "license": "Non-commercial free API / Open Data Attribution (CC BY 4.0)",
        "coordinates": PUNE_COORDS,
        "elevation_m": fc_data.get("elevation"),
        "timezone": fc_data.get("timezone"),
        "utc_offset_seconds": fc_data.get("utc_offset_seconds"),
        "files": [
            {
                "product_type": "7-Day Hourly Forecast & Current Conditions",
                "filename": "open_meteo_forecast_pune.json",
                "relative_path": "data/raw/weather/open_meteo_forecast_pune.json",
                "sha256": compute_sha256(fc_path),
                "size_bytes": os.path.getsize(fc_path),
                "validation": fc_val
            },
            {
                "product_type": "Historical Hourly Monsoon Archive (July 2024 Flood Event)",
                "filename": "open_meteo_historical_202407_pune.json",
                "relative_path": "data/raw/weather/open_meteo_historical_202407_pune.json",
                "sha256": compute_sha256(hist_path),
                "size_bytes": os.path.getsize(hist_path),
                "validation": hist_val
            }
        ],
        "acquisition_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    meta_path = os.path.join(METADATA_DIR, "open_meteo_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata written to {meta_path}")
    print("Open-Meteo acquisition completed successfully!")

if __name__ == "__main__":
    main()

