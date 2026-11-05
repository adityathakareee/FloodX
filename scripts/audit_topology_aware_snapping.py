"""Test topology-aware snapping logic and compare against naive 8m snapping."""
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

from typing import Tuple, List, Dict, Any
import math
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import networkx as nx

from app.services.routing.graph_builder import road_graph_builder
from app.services.routing.routing_constants import PROJECTED_METRIC_CRS, GEOGRAPHIC_CRS

records = road_graph_builder.load_road_records()
parsed = road_graph_builder.parse_road_attributes(records)
gdf_wgs = gpd.GeoDataFrame(parsed, geometry="geom", crs=GEOGRAPHIC_CRS)
gdf_utm = gdf_wgs.to_crs(PROJECTED_METRIC_CRS)
split_segments = road_graph_builder.split_roads_at_intersections(gdf_utm)

def get_tangent_vector(line: LineString, at_start: bool) -> Tuple[float, float]:
    coords = list(line.coords)
    if at_start:
        p1, p2 = coords[0], coords[1]
    else:
        p1, p2 = coords[-1], coords[-2]
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    norm = math.hypot(dx, dy)
    if norm == 0:
        return (0.0, 0.0)
    return (dx / norm, dy / norm)

def angle_between_vectors(v1, v2):
    dot = v1[0]*v2[0] + v1[1]*v2[1]
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))

# Let's inspect all endpoint-pair distances under 8.0m on same layer
candidate_snaps = []
all_endpoints = []

for seg_idx, (seg_geom, row) in enumerate(split_segments):
    coords = list(seg_geom.coords)
    if len(coords) < 2:
        continue
    p_start = Point(coords[0])
    p_end = Point(coords[-1])
    v_start = get_tangent_vector(seg_geom, at_start=True)
    v_end = get_tangent_vector(seg_geom, at_start=False)
    
    all_endpoints.append({
        "seg_idx": seg_idx,
        "endpoint_type": "start",
        "pt": p_start,
        "tangent": v_start,
        "layer": row["layer"],
        "row": row
    })
    all_endpoints.append({
        "seg_idx": seg_idx,
        "endpoint_type": "end",
        "pt": p_end,
        "tangent": v_end,
        "layer": row["layer"],
        "row": row
    })

print(f"Total endpoints: {len(all_endpoints)}")

# Evaluate candidate snaps
accepted = 0
rejected_median_parallel = 0
rejected_too_far = 0
flagged_uncertain = 0

rejections = []
uncertain_flags = []

for i in range(len(all_endpoints)):
    ep1 = all_endpoints[i]
    for j in range(i + 1, len(all_endpoints)):
        ep2 = all_endpoints[j]
        if ep1["layer"] != ep2["layer"]:
            continue
        d = ep1["pt"].distance(ep2["pt"])
        if d > 8.0:
            continue
            
        if d <= 0.01:
            accepted += 1
            continue
            
        # Between 0.01m and 8.0m
        v1 = ep1["tangent"]
        v2 = ep2["tangent"]
        angle = angle_between_vectors(v1, v2)
        
        # Parallel / antiparallel detection
        # If angle is close to 0 or 180 degrees
        is_collinear_or_parallel = (angle < 25.0) or (angle > 155.0)
        
        if d > 3.5:
            if is_collinear_or_parallel:
                rejected_median_parallel += 1
                rejections.append({
                    "dist_m": round(d, 2),
                    "angle_deg": round(angle, 1),
                    "reason": "PARALLEL_MEDIAN_SEPARATION",
                    "r1": ep1["row"]["name"],
                    "r2": ep2["row"]["name"],
                    "hw1": ep1["row"]["highway"],
                    "hw2": ep2["row"]["highway"],
                    "layer": ep1["layer"]
                })
            else:
                flagged_uncertain += 1
                uncertain_flags.append({
                    "dist_m": round(d, 2),
                    "angle_deg": round(angle, 1),
                    "reason": "UNCERTAIN_GAP_EXCEEDS_3.5M",
                    "r1": ep1["row"]["name"],
                    "r2": ep2["row"]["name"]
                })
        else: # d <= 3.5m
            # Genuine intersection taper or small gap
            accepted += 1

print(f"Candidate snap audit:")
print(f"  Accepted snaps: {accepted}")
print(f"  Rejected parallel/median snaps: {rejected_median_parallel}")
print(f"  Flagged uncertain snaps: {flagged_uncertain}")

print("\nSample rejected median/parallel connections (prevented false U-turns):")
for r in rejections[:10]:
    print(f"  Dist={r['dist_m']}m Angle={r['angle_deg']}deg: '{r['r1']}' <-> '{r['r2']}' ({r['hw1']}/{r['hw2']}) [{r['reason']}]")
