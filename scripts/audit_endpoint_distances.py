"""Inspect exact coordinate sharing vs snapping in OSM."""
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from app.services.routing.graph_builder import road_graph_builder
from app.services.routing.routing_constants import PROJECTED_METRIC_CRS, GEOGRAPHIC_CRS

records = road_graph_builder.load_road_records()
parsed = road_graph_builder.parse_road_attributes(records)
gdf_wgs = gpd.GeoDataFrame(parsed, geometry="geom", crs=GEOGRAPHIC_CRS)
gdf_utm = gdf_wgs.to_crs(PROJECTED_METRIC_CRS)
split_segments = road_graph_builder.split_roads_at_intersections(gdf_utm)

print(f"Total split segments: {len(split_segments)}")

# Collect all endpoints
all_endpoints = []
for idx, (seg_geom, row) in enumerate(split_segments):
    coords = list(seg_geom.coords)
    all_endpoints.append((Point(coords[0]), row["layer"], idx, row["id"], row["name"], "start", row["oneway"]))
    all_endpoints.append((Point(coords[-1]), row["layer"], idx, row["id"], row["name"], "end", row["oneway"]))

# Count exact coordinate matches (d == 0)
exact_matches = 0
close_matches = 0 # 0 < d <= 1.0m
medium_matches = 0 # 1.0m < d <= 3.0m
loose_matches = 0 # 3.0m < d <= 8.0m

distance_buckets = {
    "0.0m (exact)": 0,
    "0.0m - 1.0m": 0,
    "1.0m - 3.0m": 0,
    "3.0m - 5.0m": 0,
    "5.0m - 8.0m": 0,
    "> 8.0m": 0
}

# For each endpoint, find nearest other endpoint on same layer
nearest_distances = []
for i in range(len(all_endpoints)):
    pt_i, layer_i, seg_i, road_i, name_i, end_i, oneway_i = all_endpoints[i]
    min_d = float('inf')
    best_j = -1
    for j in range(len(all_endpoints)):
        if i == j:
            continue
        pt_j, layer_j, seg_j, road_j, name_j, end_j, oneway_j = all_endpoints[j]
        if layer_i != layer_j:
            continue
        d = pt_i.distance(pt_j)
        if d < min_d:
            min_d = d
            best_j = j
    if best_j != -1:
        nearest_distances.append({
            "d": min_d,
            "layer": layer_i,
            "road1": road_i,
            "name1": name_i,
            "road2": all_endpoints[best_j][3],
            "name2": all_endpoints[best_j][4],
            "oneway1": oneway_i,
            "oneway2": all_endpoints[best_j][6]
        })

df_nd = pd.DataFrame(nearest_distances)
print("Nearest endpoint distance distribution:")
print(f"  Exactly 0.0m (exact vertex match): {(df_nd['d'] < 0.01).sum()}")
print(f"  0.01m to 1.0m: {((df_nd['d'] >= 0.01) & (df_nd['d'] <= 1.0)).sum()}")
print(f"  1.0m to 3.0m: {((df_nd['d'] > 1.0) & (df_nd['d'] <= 3.0)).sum()}")
print(f"  3.0m to 5.0m: {((df_nd['d'] > 3.0) & (df_nd['d'] <= 5.0)).sum()}")
print(f"  5.0m to 8.0m: {((df_nd['d'] > 5.0) & (df_nd['d'] <= 8.0)).sum()}")
print(f"  > 8.0m: {(df_nd['d'] > 8.0).sum()}")

# Let's inspect those in 1.0m to 5.0m and 5.0m to 8.0m
print("\nInspecting 3.0m to 8.0m connections:")
sample_3_to_8 = df_nd[(df_nd['d'] > 3.0) & (df_nd['d'] <= 8.0)]
for idx, r in sample_3_to_8.head(15).iterrows():
    print(f"  d={r['d']:.2f}m: '{r['name1']}' (id={r['road1']}) <-> '{r['name2']}' (id={r['road2']}) (oneway: {r['oneway1']} vs {r['oneway2']})")

