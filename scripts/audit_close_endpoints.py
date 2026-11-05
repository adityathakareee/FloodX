"""Inspect endpoints with distance between 0.01m and 5.0m."""
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

all_endpoints = []
for idx, (seg_geom, row) in enumerate(split_segments):
    coords = list(seg_geom.coords)
    all_endpoints.append((Point(coords[0]), row["layer"], idx, row["id"], row["name"], row["highway"], row["oneway"], "start"))
    all_endpoints.append((Point(coords[-1]), row["layer"], idx, row["id"], row["name"], row["highway"], row["oneway"], "end"))

for i in range(len(all_endpoints)):
    pt_i, layer_i, seg_i, road_i, name_i, hw_i, oneway_i, end_i = all_endpoints[i]
    for j in range(i + 1, len(all_endpoints)):
        pt_j, layer_j, seg_j, road_j, name_j, hw_j, oneway_j, end_j = all_endpoints[j]
        if layer_i != layer_j:
            continue
        d = pt_i.distance(pt_j)
        if 0.001 < d <= 5.0:
            print(f"Dist={d:.2f}m Layer={layer_i} Segs=({seg_i}, {seg_j}):")
            print(f"   Road 1: id={road_i} '{name_i}' ({hw_i}) oneway={oneway_i} end={end_i}")
            print(f"   Road 2: id={road_j} '{name_j}' ({hw_j}) oneway={oneway_j} end={end_j}")

