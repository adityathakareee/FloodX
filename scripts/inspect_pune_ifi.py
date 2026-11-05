"""Analyze Pune flood events from IFI-Impacts."""
import pandas as pd

df = pd.read_csv("data/raw/flood_inventory/India_Flood_Inventory_v3.csv")
pune = df[
    df["State"].astype(str).str.contains("Maharashtra", case=False, na=False)
    & df["Districts"].astype(str).str.contains("Pune", case=False, na=False)
].copy()

pune["Start_DT"] = pd.to_datetime(pune["Start Date"], format="%d-%m-%Y %H:%M", errors="coerce")
pune_recent = pune[pune["Start_DT"] >= "2000-01-01"].sort_values("Start_DT")

print(f"Total Pune flood event entries since 2000: {len(pune_recent)}")
print("-" * 100)
for _, r in pune_recent.iterrows():
    s_dt = r["Start Date"]
    e_dt = r["End Date"]
    dur = r["Duration(Days)"]
    cause = r["Main Cause"]
    fatal = r["Human fatality"]
    disp = r["Human Displaced"]
    dam = str(r["Extent of damage "])[:60] if pd.notna(r["Extent of damage "]) else "None"
    print(f"[{s_dt} to {e_dt}] ({dur}d) Cause: {cause} | Deaths: {fatal} | Displaced: {disp} | Damage: {dam}")

