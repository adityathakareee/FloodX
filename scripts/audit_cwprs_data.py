"""
Deep audit of CWPRS Khadakwasla rainfall telemetry dataset.
"""
import os
import pandas as pd
import numpy as np

CSV_PATH = "data/raw/rainfall/rainfall_tel_hr_cwprs_mh_sample.csv"

def audit():
    print(f"=== CWPRS Khadakwasla Telemetry Audit: {CSV_PATH} ===")
    df = pd.read_csv(CSV_PATH, low_memory=False)
    print(f"Total rows in sample file: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # 1. Station info
    print("\n--- 1. Station Metadata ---")
    for col in ['Station', 'Agency', 'State', 'District', 'Tehsil', 'Village', 'Latitude', 'Longitude']:
        if col in df.columns:
            u_vals = df[col].unique().tolist()
            print(f"  {col}: {u_vals[:5]} (unique: {len(u_vals)})")

    # 2. Timestamps & Temporal Coverage
    print("\n--- 2. Temporal Analysis ---")
    ts_col = 'Data Acquisition Time'
    print(f"Timestamp column: {ts_col}")
    print(f"Sample raw timestamps: {df[ts_col].head(5).tolist()}")
    
    # Try parsing timestamps (format looks like 'DD-MM-YYYY HH:MM')
    df['parsed_time'] = pd.to_datetime(df[ts_col], format='%d-%m-%Y %H:%M', errors='coerce')
    null_ts = df['parsed_time'].isnull().sum()
    print(f"Null / Unparseable timestamps: {null_ts}")
    
    valid_times = df['parsed_time'].dropna()
    print(f"Temporal Range: {valid_times.min()} to {valid_times.max()}")
    
    # Check time step differences
    df_sorted = df.sort_values('parsed_time').copy()
    df_sorted['time_diff_min'] = df_sorted['parsed_time'].diff().dt.total_seconds() / 60.0
    print(f"Time intervals (diff in minutes) value counts (top 10):")
    print(df_sorted['time_diff_min'].value_counts().head(10))
    
    # Duplicate timestamps
    dups = df.duplicated(subset=[ts_col]).sum()
    print(f"Duplicate timestamp rows: {dups}")
    if dups > 0:
        print("Sample duplicated timestamps:", df[df.duplicated(subset=[ts_col], keep=False)][ts_col].head(4).tolist())

    # 3. Measurement Column & Statistics
    print("\n--- 3. Rainfall Measurements & Extreme Outliers ---")
    rain_col = 'Telemetry Hourly Rainfall (mm)'
    df['rain_val'] = pd.to_numeric(df[rain_col], errors='coerce')
    
    total_records = len(df)
    null_rain = df['rain_val'].isnull().sum()
    neg_rain = (df['rain_val'] < 0).sum()
    zero_rain = (df['rain_val'] == 0).sum()
    pos_rain = (df['rain_val'] > 0).sum()
    
    print(f"Total rows: {total_records}")
    print(f"Null rainfall: {null_rain}")
    print(f"Negative rainfall (< 0): {neg_rain}")
    print(f"Zero rainfall (== 0): {zero_rain}")
    print(f"Positive rainfall (> 0): {pos_rain}")
    
    valid_rain = df['rain_val'].dropna()
    print(f"\nRainfall Summary Statistics (mm):")
    print(valid_rain.describe())
    
    # Extreme values analysis
    print("\nTop 10 highest rainfall records:")
    top10 = df.sort_values('rain_val', ascending=False).head(10)
    for idx, row in top10.iterrows():
        print(f"  SlNo: {row.get('SlNo')}, Time: {row.get(ts_col)}, Value: {row.get('rain_val')} mm")

    # Sequence around the max value (145.6 mm)
    max_idx = df['rain_val'].idxmax()
    print(f"\nContext around peak record ({df.loc[max_idx, 'rain_val']} mm at {df.loc[max_idx, ts_col]}):")
    context_indices = range(max(0, max_idx - 5), min(len(df), max_idx + 6))
    for i in context_indices:
        r = df.loc[i]
        print(f"  [{i}] Time: {r.get(ts_col)}, Rain: {r.get(rain_col)} mm")

if __name__ == "__main__":
    audit()

