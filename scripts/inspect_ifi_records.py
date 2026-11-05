"""Inspect downloaded India Flood Inventory (IFI-Impacts) for Pune and Maharashtra records."""
import pandas as pd
import os

csv_path = "data/raw/flood_inventory/India_Flood_Inventory_v3.csv"
df = pd.read_csv(csv_path)

print(f"Total rows in India Flood Inventory v3: {len(df):,}")
print(f"Columns ({len(df.columns)}):", list(df.columns))

# Filter for Maharashtra
mh_df = df[df["State"].astype(str).str.contains("Maharashtra", case=False, na=False)]
print(f"\nTotal Maharashtra flood event records: {len(mh_df):,}")

# Filter for Pune
pune_df = mh_df[mh_df["Districts"].astype(str).str.contains("Pune", case=False, na=False)]
print(f"Total Pune District flood event records: {len(pune_df):,}")

if len(pune_df) > 0:
    print("\nPune Flood Event Records in IFI-Impacts:")
    cols_to_show = [c for c in ["UEI", "Start Date", "End Date", "Duration(Days)", "Main Cause", "Location", "Districts", "Severity", "Human fatality", "Human Displaced", "Extent of damage "] if c in pune_df.columns]
    print(pune_df[cols_to_show].to_string())
else:
    print("Checking unique districts in Maharashtra:")
    print(mh_df["Districts"].unique()[:20])

# Check other files: District_FloodImpact, District_FloodedArea, DFSI
for fn in ["District_FloodImpact.csv", "District_FloodedArea.csv", "DFSI.csv"]:
    fp = os.path.join("data/raw/flood_inventory", fn)
    if os.path.exists(fp):
        d = pd.read_csv(fp)
        print(f"\n--- {fn} (shape: {d.shape}) ---")
        print("Columns:", list(d.columns)[:6])
        pune_rows = d[d.apply(lambda row: row.astype(str).str.contains("Pune", case=False).any(), axis=1)]
        print(f"Pune rows in {fn}: {len(pune_rows)}")
        if len(pune_rows) > 0:
            print(pune_rows.head(2).to_string())
