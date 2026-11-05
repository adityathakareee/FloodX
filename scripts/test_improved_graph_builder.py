"""Prototype of improved graph builder with MultiDiGraph and topology-aware snapping."""
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

import re
import math
import logging
from typing import Dict, List, Tuple, Any, Optional
import networkx as nx
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from shapely.ops import split, unary_union
from shapely import wkt
import pyproj

from app.services.routing.routing_constants import (
    GEOGRAPHIC_CRS,
    PROJECTED_METRIC_CRS,
    DEFAULT_SPEED_LIMITS_KMH
)
from app.services.routing.graph_builder import RoadGraphBuilder

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

def vector_angle_deg(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
    dot = v1[0]*v2[0] + v1[1]*v2[1]
    dot = max(-1.0, min(1.0, dot))
    return math.degrees(math.acos(dot))

# Let's test the builder
builder = RoadGraphBuilder()
raw_records = builder.load_road_records()

parsed = []
for r in raw_records:
    p = r.get("properties_json") or {}
    ot = p.get("other_tags") or ""

    layer = 0
    lm = re.search(r'"layer"=>"([^"]+)"', ot)
    if lm:
        try:
            layer = int(lm.group(1))
        except ValueError:
            layer = 0

    is_bridge = '"bridge"=>"yes"' in ot or layer > 0
    is_tunnel = '"tunnel"=>"yes"' in ot or layer < 0

    # Oneway tag parsing
    oneway_raw = None
    om = re.search(r'"oneway"=>"([^"]+)"', ot)
    if om:
        oneway_raw = om.group(1).lower()

    if oneway_raw in ["yes", "1"]:
        oneway_mode = "FORWARD"
        dir_status = "VERIFIED_ONEWAY"
        is_dir_assumed = False
    elif oneway_raw in ["-1", "reverse"]:
        oneway_mode = "REVERSE"
        dir_status = "VERIFIED_ONEWAY"
        is_dir_assumed = False
    elif oneway_raw in ["no", "0"]:
        oneway_mode = "BIDIRECTIONAL"
        dir_status = "VERIFIED_BIDIRECTIONAL"
        is_dir_assumed = False
    elif p.get("highway") in ["motorway", "motorway_link"]:
        oneway_mode = "FORWARD"
        dir_status = "VERIFIED_ONEWAY"
        is_dir_assumed = False
    else:
        oneway_mode = "PROVISIONAL_BIDIRECTIONAL"
        dir_status = "UNKNOWN_DIRECTIONALITY"
        is_dir_assumed = True

    # Maxspeed
    maxspeed = None
    speed_source = "IRC_DEFAULT_ESTIMATE"
    mm = re.search(r'"maxspeed"=>"([^"]+)"', ot)
    if mm:
        try:
            digits = re.findall(r'\d+', mm.group(1))
            if digits:
                maxspeed = float(digits[0])
                speed_source = "OSM_TAGGED"
        except (IndexError, ValueError):
            maxspeed = None

    surface = "asphalt"
    sm = re.search(r'"surface"=>"([^"]+)"', ot)
    if sm:
        surface = sm.group(1).lower()

    access = "yes"
    am = re.search(r'"access"=>"([^"]+)"', ot)
    if am:
        access = am.group(1).lower()

    geom = wkt.loads(r["wkt"])

    parsed.append({
        "id": r["id"],
        "osm_id": r["osm_id"],
        "name": r["name"] or "Unnamed Road",
        "highway": p.get("highway", "unclassified"),
        "layer": layer,
        "is_bridge": is_bridge,
        "is_tunnel": is_tunnel,
        "oneway_mode": oneway_mode,
        "directionality_status": dir_status,
        "is_direction_assumed": is_dir_assumed,
        "maxspeed": maxspeed,
        "speed_source": speed_source,
        "surface": surface,
        "access": access,
        "geom": geom
    })

gdf_wgs = gpd.GeoDataFrame(parsed, geometry="geom", crs=GEOGRAPHIC_CRS)
gdf_utm = gdf_wgs.to_crs(PROJECTED_METRIC_CRS)
split_segments = builder.split_roads_at_intersections(gdf_utm)

print(f"Total split segments: {len(split_segments)}")

# Topology-Aware Snapping Engine
# We want nodes keyed by (x, y, layer), but if a new endpoint arrives:
# 1. Look for existing nodes on same layer.
# 2. If dist <= 0.01m: snap immediately.
# 3. If 0.01m < dist <= 3.5m: snap (junction taper / curb radius).
# 4. If 3.5m < dist <= 8.0m:
#    Compute angle with tangent of existing road at that node.
#    If parallel/collinear (< 25 deg or > 155 deg): REJECT snap (median separation).
#    If intersecting angle: REJECT forced snap (flag as uncertain), create separate node.

nodes = {}
node_id_counter = 1
snap_stats = {
    "accepted_exact": 0,
    "accepted_curb_taper": 0,
    "rejected_parallel_median": 0,
    "rejected_uncertain_gap": 0
}

def get_or_create_node_safe(pt: Point, layer: int, tangent: Tuple[float, float], seg_name: str, hw: str) -> int:
    global node_id_counter
    # Find nearest existing node on same layer
    best_nid = None
    best_dist = float('inf')
    
    for nid, ndata in nodes.items():
        if ndata["layer"] == layer:
            d = pt.distance(ndata["point_utm"])
            if d < best_dist:
                best_dist = d
                best_nid = nid
                
    if best_nid is not None:
        if best_dist <= 0.01:
            snap_stats["accepted_exact"] += 1
            return best_nid
        elif best_dist <= 3.5:
            # Check if this endpoint is parallel to an existing endpoint at that node
            # If opposite carriageway running parallel even at 2-3m, we should check angle
            # But 0.01m-3.5m is typically legitimate turn curb taper
            node_tangents = nodes[best_nid].get("tangents", [])
            is_parallel_median = False
            for t_ex in node_tangents:
                ang = vector_angle_deg(tangent, t_ex)
                if (ang < 20.0 or ang > 160.0) and best_dist > 1.5:
                    is_parallel_median = True
                    break
            if not is_parallel_median:
                snap_stats["accepted_curb_taper"] += 1
                nodes[best_nid]["tangents"].append(tangent)
                return best_nid
            else:
                snap_stats["rejected_parallel_median"] += 1
        elif best_dist <= 8.0:
            # Over 3.5m: check collinearity
            node_tangents = nodes[best_nid].get("tangents", [])
            is_parallel = False
            for t_ex in node_tangents:
                ang = vector_angle_deg(tangent, t_ex)
                if ang < 25.0 or ang > 155.0:
                    is_parallel = True
                    break
            if is_parallel:
                snap_stats["rejected_parallel_median"] += 1
            else:
                snap_stats["rejected_uncertain_gap"] += 1

    # Create new node
    nid = node_id_counter
    node_id_counter += 1
    nodes[nid] = {
        "point_utm": pt,
        "coords_utm": (pt.x, pt.y),
        "layer": layer,
        "tangents": [tangent]
    }
    return nid

# Build MultiDiGraph
G = nx.MultiDiGraph()
edge_idx = 1

for seg_geom, row in split_segments:
    coords_utm = list(seg_geom.coords)
    if len(coords_utm) < 2:
        continue

    v_start = get_tangent_vector(seg_geom, at_start=True)
    v_end = get_tangent_vector(seg_geom, at_start=False)

    u = get_or_create_node_safe(Point(coords_utm[0]), row["layer"], v_start, row["name"], row["highway"])
    v = get_or_create_node_safe(Point(coords_utm[-1]), row["layer"], v_end, row["name"], row["highway"])

    if u == v:
        continue

    length_m = round(float(seg_geom.length), 2)
    if length_m < 0.5:
        continue

    raw_speed = row.get("maxspeed")
    if raw_speed is not None and not pd.isna(raw_speed) and float(raw_speed) > 0:
        speed_kmh = float(raw_speed)
        speed_is_default = False
        speed_source = "OSM_TAGGED"
    else:
        speed_kmh = float(DEFAULT_SPEED_LIMITS_KMH.get(row.get("highway"), DEFAULT_SPEED_LIMITS_KMH["default"]))
        speed_is_default = True
        speed_source = "IRC_DEFAULT_ESTIMATE"

    speed_ms = (speed_kmh * 1000.0) / 3600.0
    travel_time_sec = round(float(length_m / speed_ms), 1)

    coords_wgs = [builder.utm_to_wgs.transform(x, y) for x, y in coords_utm]
    geom_wgs = LineString(coords_wgs)

    base_edge_data = {
        "source_feature_id": int(row["id"]),
        "osm_id": str(row["osm_id"]),
        "name": str(row["name"]),
        "highway": str(row["highway"]),
        "length_m": length_m,
        "estimated_travel_time_sec": travel_time_sec,
        "speed_limit_kmh": round(speed_kmh, 1),
        "speed_is_default": speed_is_default,
        "speed_source": speed_source,
        "surface": str(row.get("surface", "asphalt")),
        "is_bridge": bool(row.get("is_bridge", False)),
        "is_tunnel": bool(row.get("is_tunnel", False)),
        "layer": int(row.get("layer", 0)),
        "access": str(row.get("access", "yes")),
        "directionality_status": row["directionality_status"],
        "is_direction_assumed": row["is_direction_assumed"]
    }

    oneway_mode = row["oneway_mode"]

    if oneway_mode == "FORWARD":
        e_id = f"edge_{edge_idx}"
        edge_idx += 1
        d = dict(base_edge_data)
        d.update({
            "edge_id": e_id,
            "source_node": u,
            "destination_node": v,
            "is_oneway": True,
            "geometry_geojson": geom_wgs.__geo_interface__
        })
        G.add_edge(u, v, key=e_id, **d)

    elif oneway_mode == "REVERSE":
        # oneway = -1
        e_id = f"edge_{edge_idx}"
        edge_idx += 1
        d = dict(base_edge_data)
        rev_coords_wgs = list(reversed(coords_wgs))
        d.update({
            "edge_id": e_id,
            "source_node": v,
            "destination_node": u,
            "is_oneway": True,
            "geometry_geojson": LineString(rev_coords_wgs).__geo_interface__
        })
        G.add_edge(v, u, key=e_id, **d)

    else:
        # BIDIRECTIONAL or PROVISIONAL_BIDIRECTIONAL
        e_id_fwd = f"edge_{edge_idx}"
        edge_idx += 1
        d_fwd = dict(base_edge_data)
        d_fwd.update({
            "edge_id": e_id_fwd,
            "source_node": u,
            "destination_node": v,
            "is_oneway": False,
            "geometry_geojson": geom_wgs.__geo_interface__
        })
        G.add_edge(u, v, key=e_id_fwd, **d_fwd)

        e_id_rev = f"edge_{edge_idx}"
        edge_idx += 1
        d_rev = dict(base_edge_data)
        rev_coords_wgs = list(reversed(coords_wgs))
        d_rev.update({
            "edge_id": e_id_rev,
            "source_node": v,
            "destination_node": u,
            "is_oneway": False,
            "geometry_geojson": LineString(rev_coords_wgs).__geo_interface__
        })
        G.add_edge(v, u, key=e_id_rev, **d_rev)

print(f"\nConstructed MultiDiGraph:")
print(f"  Nodes: {G.number_of_nodes()}")
print(f"  Edges: {G.number_of_edges()}")
print(f"Snap Statistics: {snap_stats}")

# Check connected components in undirected view
G_undir = G.to_undirected()
comps = sorted(list(nx.connected_components(G_undir)), key=len, reverse=True)
print(f"  Connected components: {len(comps)}")
print(f"  Largest component: {len(comps[0])} nodes ({len(comps[0])/G.number_of_nodes()*100:.1f}%)")
print(f"  Second largest: {len(comps[1])} nodes ({len(comps[1])/G.number_of_nodes()*100:.1f}%)")

