"""
Deep audit of Maharashtra SW River Water Level Telemetry dataset.
"""
import os
import pandas as pd
import numpy as np

CSV_PATH = "data/raw/river_levels/rwl_tel_hr_maharashtra_sw_007_sample.csv"

# Pune Centroid: 18.5204 N, 73.8567 E
PUNE_LAT, PUNE_LON = 18.5204, 73.8567

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def audit():
    print(f"=== Maharashtra SW River Water Level Audit: {CSV_PATH} ===")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    print(f"Total rows in sample file: {len(df)}")
    print(f"Columns ({len(df.columns)}): {list(df.columns)}")
    
    # 1. Stations and geographic attributes
    print("\n--- 1. Station & Hydrological Location ---")
    stations = df['Station'].unique().tolist()
    print(f"Stations in file: {stations}")
    
    for st in stations:
        st_df = df[df['Station'] == st]
        print(f"\nStation: '{st}' (rows: {len(st_df)})")
        for col in ['Agency', 'State', 'District', 'Tehsil', 'Village', 'River', 'Basin', 'Tributary', 'Latitude', 'Longitude', 'RL_of_zeroGauge', 'MeanSeaLevel']:
            if col in df.columns:
                vals = st_df[col].dropna().unique().tolist()
                print(f"  {col}: {vals[:3]}")
                
        # Calculate distance to Pune centroid
        lats = st_df['Latitude'].dropna().unique()
        lons = st_df['Longitude'].dropna().unique()
        if len(lats) > 0 and len(lons) > 0 and pd.notnull(lats[0]) and pd.notnull(lons[0]):
            lat = float(lats[0])
            lon = float(lons[0])
            dist = haversine_km(PUNE_LAT, PUNE_LON, lat, lon)
            print(f"  Coordinates: {lat:.5f}° N, {lon:.5f}° E")
            print(f"  Geographic distance from Pune City centroid: {dist:.1f} km")
            if dist < 50:
                print("  Classification: Within pilot basin")
            elif dist < 120:
                print("  Classification: Upstream/Downstream hydrologically relevant")
            elif dist < 300:
                print("  Classification: Regional reference only (Outside pilot basin)")
            else:
                print("  Classification: Not relevant (Distant basin)")
        else:
            print("  Classification: Location unverified (Missing lat/lon)")

    # 2. Measurement Column & Units
    print("\n--- 2. Measurement Analysis ---")
    level_col = 'River Water Level Telemetry Hourly (meter)'
    df['water_level'] = pd.to_numeric(df[level_col], errors='coerce')
    print(f"Level column: {level_col}")
    print(f"Valid readings: {df['water_level'].notnull().sum()}")
    print(f"Null readings: {df['water_level'].isnull().sum()}")
    print(f"Unique level values: {df['water_level'].nunique()}")
    print(f"Summary stats:\n{df['water_level'].describe()}")
    
    # 3. Temporal Range
    ts_col = 'Data Acquisition Time'
    print(f"\n--- 3. Temporal Coverage ---")
    print(f"Sample raw timestamps: {df[ts_col].head(5).tolist()}")
    df['parsed_time'] = pd.to_datetime(df[ts_col], format='%d-%m-%Y %H:%M', errors='coerce')
    print(f"Parsed times: {df['parsed_time'].dropna().min()} to {df['parsed_time'].dropna().max()}")
    print(f"Duplicates: {df.duplicated(subset=[ts_col, 'Station']).sum()}")

if __name__ == "__main__":
    audit()

