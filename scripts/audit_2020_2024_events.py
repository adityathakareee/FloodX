"""Audit and validate all historical flood events in 2020-2024 overlapping the weather period."""
import pandas as pd
import json

df = pd.read_csv("data/raw/flood_inventory/India_Flood_Inventory_v3.csv", low_memory=False)
mask = df["Districts"].astype(str).str.contains(r"\bPunc\b|\bPune\b", case=False, na=False)
p_df = df[mask].copy()

# Look at rows with 2020, 2021, 2022, 2023, 2024
rows = []
for idx, r in p_df.iterrows():
    s_date = str(r.get("Start Date", "")).strip()
    e_date = str(r.get("End Date", "")).strip()
    if any(y in s_date for y in ["2020", "2021", "2022", "2023", "2024"]):
        rows.append((idx, r))

print(f"Total candidate rows matching 2020-2024: {len(rows)}")
for idx, r in rows:
    print(f"\n--- Index {idx} ---")
    print(f"Start: {r['Start Date']} | End: {r['End Date']} | Duration: {r.get('Duration(Days)')} days")
    print(f"Cause: {r.get('Main Cause')} | Deaths: {r.get('Human fatality')} | Location: {r.get('Location')}")
    print(f"Districts: {r.get('Districts')}")
    dmg = str(r.get("Extent of damage ", ""))
    print(f"Damage: {dmg[:250] if dmg != 'nan' else 'None'}")

