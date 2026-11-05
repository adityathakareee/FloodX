"""Investigate snaps and whether opposite carriageways or parallel medians were falsely snapped."""
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import math
from app.services.routing.graph_builder import road_graph_builder
from app.services.routing.routing_constants import PROJECTED_METRIC_CRS, GEOGRAPHIC_CRS

records = road_graph_builder.load_road_records()
parsed = road_graph_builder.parse_road_attributes(records)
gdf_wgs = gpd.GeoDataFrame(parsed, geometry="geom", crs=GEOGRAPHIC_CRS)
gdf_utm = gdf_wgs.to_crs(PROJECTED_METRIC_CRS)
split_segments = road_graph_builder.split_roads_at_intersections(gdf_utm)

nodes = {}
node_id_counter = 1
snap_tol = 8.0

def get_bearing(line, at_start=True):
    coords = list(line.coords)
    if at_start:
        p1, p2 = coords[0], coords[1]
    else:
        p1, p2 = coords[-2], coords[-1]
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.atan2(dy, dx)

snapped_pairs = []

for seg_idx, (seg_geom, row) in enumerate(split_segments):
    coords = list(seg_geom.coords)
    if len(coords) < 2:
        continue
    
    # Check start
    pt_start = Point(coords[0])
    for nid, ndata in nodes.items():
        if ndata["layer"] == row["layer"]:
            d = pt_start.distance(ndata["point_utm"])
            if 0.001 < d <= snap_tol:
                snapped_pairs.append({
                    "snap_type": "start",
                    "seg_idx": seg_idx,
                    "road_id": row["id"],
                    "osm_id": row["osm_id"],
                    "name": row["name"],
                    "highway": row["highway"],
                    "oneway": row["oneway"],
                    "target_node": nid,
                    "target_road_id": ndata.get("source_road_id"),
                    "target_name": ndata.get("source_name"),
                    "target_oneway": ndata.get("source_oneway"),
                    "distance_m": d,
                    "bearing": get_bearing(seg_geom, at_start=True),
                    "target_bearing": ndata.get("bearing")
                })
                break
    # Add start node if new
    nid_start = len(nodes) + 1
    # Check if matched
    matched = False
    for nid, ndata in nodes.items():
        if ndata["layer"] == row["layer"] and pt_start.distance(ndata["point_utm"]) <= snap_tol:
            matched = True
            break
    if not matched:
        nodes[nid_start] = {
            "point_utm": pt_start,
            "layer": row["layer"],
            "source_road_id": row["id"],
            "source_name": row["name"],
            "source_oneway": row["oneway"],
            "bearing": get_bearing(seg_geom, at_start=True)
        }

print(f"Total non-exact snaps analyzed: {len(snapped_pairs)}")
df = pd.DataFrame(snapped_pairs)

# Check if target_road_id != road_id
different_roads = df[df["road_id"] != df["target_road_id"]]
print(f"Snaps between different road features: {len(different_roads)}")

# Check snaps where both roads are oneway=yes
both_oneway = different_roads[(different_roads["oneway"] == True) & (different_roads["target_oneway"] == True)]
print(f"Snaps where both are oneway=yes: {len(both_oneway)}")

# Check parallel or anti-parallel lines
suspicious_parallel = []
for idx, r in different_roads.iterrows():
    if r["bearing"] is not None and r["target_bearing"] is not None:
        diff_rad = abs(r["bearing"] - r["target_bearing"])
        diff_deg = math.degrees(diff_rad) % 360
        # If angle is near 0 (parallel) or near 180 (opposite parallel)
        if diff_deg < 25 or abs(diff_deg - 180) < 25:
            suspicious_parallel.append({
                "road_id": r["road_id"],
                "target_road_id": r["target_road_id"],
                "name1": r["name"],
                "name2": r["target_name"],
                "dist_m": r["distance_m"],
                "angle_diff_deg": diff_deg,
                "oneway1": r["oneway"],
                "oneway2": r["target_oneway"]
            })

print(f"Potentially parallel snaps (angle diff < 25 deg or ~180 deg): {len(suspicious_parallel)}")
for p in suspicious_parallel[:10]:
    print(f"  Dist={p['dist_m']:.2f}m AngleDiff={p['angle_diff_deg']:.1f}deg: '{p['name1']}' (id={p['road_id']}) <--> '{p['name2']}' (id={p['target_road_id']})")

