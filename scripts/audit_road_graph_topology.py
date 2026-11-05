"""Detailed audit script for FLOOD-X Phase 3.1.1 Road Graph Topology & Directionality."""
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

import json
import re
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Point, LineString
import networkx as nx
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.services.routing.graph_builder import road_graph_builder
from app.services.routing.routing_constants import PROJECTED_METRIC_CRS, GEOGRAPHIC_CRS

engine = create_engine(settings.DATABASE_URL)

print("=== 1. RAW ONEWAY AND ACCESS TAG AUDIT ===")
with engine.connect() as conn:
    q = text("""
        SELECT id, osm_id, name, properties_json,
               ST_AsText(geom) as wkt,
               ST_Length(geom::geography) as length_m
        FROM spatial_features
        WHERE feature_type = 'EVACUATION_ROAD'
    """)
    rows = conn.execute(q).mappings().all()

oneway_tags = {}
access_tags = {}
has_oneway_minus_one = []
oneway_values = {}

for r in rows:
    p = r.get("properties_json") or {}
    ot = p.get("other_tags") or ""
    
    # Check oneway in other_tags
    om = re.search(r'"oneway"=>"([^"]+)"', ot)
    if om:
        val = om.group(1)
        oneway_values[val] = oneway_values.get(val, 0) + 1
        if val == "-1":
            has_oneway_minus_one.append(r["id"])
    else:
        oneway_values["[UNSPECIFIED]"] = oneway_values.get("[UNSPECIFIED]", 0) + 1
        
    # Check access
    am = re.search(r'"access"=>"([^"]+)"', ot)
    if am:
        aval = am.group(1)
        access_tags[aval] = access_tags.get(aval, 0) + 1
    else:
        access_tags["[UNSPECIFIED]"] = access_tags.get("[UNSPECIFIED]", 0) + 1

print(f"Total features: {len(rows)}")
print("Oneway tag distribution:", oneway_values)
print("Features with oneway=-1:", has_oneway_minus_one)
print("Access tag distribution:", access_tags)

print("\n=== 2. PARALLEL EDGES / MULTIDIGRAPH INVESTIGATION ===")
# Let's inspect the split segments and check if any (u, v) pairs are generated more than once
parsed = road_graph_builder.parse_road_attributes([dict(r) for r in rows])
gdf_wgs = gpd.GeoDataFrame(parsed, geometry="geom", crs=GEOGRAPHIC_CRS)
gdf_utm = gdf_wgs.to_crs(PROJECTED_METRIC_CRS)
split_segments = road_graph_builder.split_roads_at_intersections(gdf_utm)

print(f"Total split segments: {len(split_segments)}")

# Let's reproduce the node snapping from builder
nodes = {}
node_id_counter = 1
snap_tol = 8.0

def get_or_create_node(pt, layer):
    global node_id_counter
    for nid, ndata in nodes.items():
        if ndata["layer"] == layer:
            if pt.distance(ndata["point_utm"]) <= snap_tol:
                return nid
    nid = node_id_counter
    node_id_counter += 1
    nodes[nid] = {
        "point_utm": pt,
        "coords_utm": (pt.x, pt.y),
        "layer": layer
    }
    return nid

edge_pairs = []
edge_pair_details = {}

for seg_geom, row in split_segments:
    coords = list(seg_geom.coords)
    if len(coords) < 2:
        continue
    u = get_or_create_node(Point(coords[0]), row["layer"])
    v = get_or_create_node(Point(coords[-1]), row["layer"])
    if u == v:
        continue
    
    # Forward edge
    pair = (u, v)
    edge_pairs.append(pair)
    if pair not in edge_pair_details:
        edge_pair_details[pair] = []
    edge_pair_details[pair].append({
        "feature_id": row["id"],
        "osm_id": row["osm_id"],
        "name": row["name"],
        "highway": row["highway"],
        "length_m": seg_geom.length,
        "is_oneway": row["oneway"],
        "direction": "forward"
    })
    
    if not row["oneway"]:
        rev_pair = (v, u)
        edge_pairs.append(rev_pair)
        if rev_pair not in edge_pair_details:
            edge_pair_details[rev_pair] = []
        edge_pair_details[rev_pair].append({
            "feature_id": row["id"],
            "osm_id": row["osm_id"],
            "name": row["name"],
            "highway": row["highway"],
            "length_m": seg_geom.length,
            "is_oneway": row["oneway"],
            "direction": "reverse"
        })

print(f"Total directed edge attempts: {len(edge_pairs)}")
unique_pairs = set(edge_pairs)
print(f"Unique (u, v) pairs: {len(unique_pairs)}")
duplicates = {p: details for p, details in edge_pair_details.items() if len(details) > 1}
print(f"Number of (u, v) pairs with MULTIPLE edges (parallel edges): {len(duplicates)}")

if duplicates:
    print("\nSample parallel edges being overwritten in DiGraph:")
    for p, details in list(duplicates.items())[:5]:
        print(f"  Pair {p}: {len(details)} edges")
        for d in details:
            print(f"    - feat={d['feature_id']} osm={d['osm_id']} name='{d['name']}' hw={d['highway']} len={d['length_m']:.1f}m dir={d['direction']}")

print("\n=== 3. SNAPPING DISTANCE & FALSE CONNECTION AUDIT ===")
# Inspect all snaps where distance > 0 and <= snap_tol
snap_events = []
for nid, ndata in nodes.items():
    # check how many endpoints snapped to this node
    pass

# Let's count how many distinct endpoints snapped to existing nodes at what distances
nodes_audit = {}
snap_distances = []
for seg_geom, row in split_segments:
    coords = list(seg_geom.coords)
    if len(coords) < 2:
        continue
    for pt in [Point(coords[0]), Point(coords[-1])]:
        # find if it matched an existing node
        matched = False
        for nid, ndata in nodes_audit.items():
            if ndata["layer"] == row["layer"]:
                d = pt.distance(ndata["point_utm"])
                if d <= snap_tol:
                    matched = True
                    if d > 0.001:
                        snap_distances.append({
                            "distance_m": d,
                            "layer": row["layer"],
                            "road_id": row["id"],
                            "road_name": row["name"],
                            "highway": row["highway"]
                        })
                    break
        if not matched:
            nodes_audit[len(nodes_audit) + 1] = {
                "point_utm": pt,
                "layer": row["layer"]
            }

print(f"Total non-zero endpoint snaps within {snap_tol}m: {len(snap_distances)}")
if snap_distances:
    df_snaps = pd.DataFrame(snap_distances)
    print("Snap distance quantiles:")
    print(df_snaps["distance_m"].describe())
    print("\nLargest snaps (> 5m):")
    large_snaps = df_snaps[df_snaps["distance_m"] > 5.0]
    print(f"Count of snaps > 5.0m: {len(large_snaps)}")
    for idx, row in large_snaps.head(10).iterrows():
        print(f"  Dist={row['distance_m']:.2f}m Layer={row['layer']} Road={row['road_id']} ('{row['road_name']}', {row['highway']})")
