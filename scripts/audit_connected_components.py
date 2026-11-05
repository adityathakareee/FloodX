"""Audit all connected components in detail for Phase 3.1.1."""
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import networkx as nx

from app.services.routing.road_network_service import road_network_service

G = road_network_service.get_or_build_graph()
G_undir = G.to_undirected()
components = sorted(list(nx.connected_components(G_undir)), key=len, reverse=True)

print(f"Total weakly connected components: {len(components)}")

comp_records = []
for idx, comp_nodes in enumerate(components):
    sub = G.subgraph(comp_nodes)
    node_count = len(comp_nodes)
    edge_count = sub.number_of_edges()
    
    # Calculate bounding box
    lons = [G.nodes[n]["longitude"] for n in comp_nodes]
    lats = [G.nodes[n]["latitude"] for n in comp_nodes]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    
    # Road classifications
    hw_counts = {}
    names = set()
    for u, v, d in sub.edges(data=True):
        hw = d.get("highway", "unknown")
        hw_counts[hw] = hw_counts.get(hw, 0) + 1
        name = d.get("name")
        if name and name != "Unnamed Road":
            names.add(name)
            
    dominant_hw = max(hw_counts.items(), key=lambda x: x[1])[0] if hw_counts else "none"
    
    # Determine reason
    # Bbox boundary of entire dataset: [73.8001, 18.4905, 73.9197, 18.5498]
    is_at_boundary = (min_lon <= 73.805 or max_lon >= 73.915 or min_lat <= 18.495 or max_lat >= 18.545)
    
    if idx == 0:
        reason = "PRIMARY_RIVER_CORRIDOR_BACKBONE (Sinhagad Rd / Deccan / Shivaji Nagar)"
        category = "PRIMARY_BACKBONE"
    elif idx == 1:
        reason = "SECONDARY_RIVER_CORRIDOR_BACKBONE (Yerawada / Bund Garden / Nagar Rd)"
        category = "SECONDARY_BACKBONE"
    elif is_at_boundary:
        reason = "DATASET_BOUNDARY_STUB (Road exits geographic bounding box)"
        category = "BOUNDARY_TRUNCATION"
    elif node_count < 5:
        reason = "MISSING_LOCAL_CONNECTORS (Arterial stub isolated by exclusion of residential streets)"
        category = "LOCAL_STREET_GAP"
    else:
        reason = "ISOLATED_ARTERIAL_CLUSTER"
        category = "ARTERIAL_ISLAND"
        
    comp_records.append({
        "component_id": idx + 1,
        "node_count": node_count,
        "edge_count": edge_count,
        "min_lon": round(min_lon, 4),
        "min_lat": round(min_lat, 4),
        "max_lon": round(max_lon, 4),
        "max_lat": round(max_lat, 4),
        "dominant_highway": dominant_hw,
        "highway_counts": hw_counts,
        "sample_roads": list(names)[:3],
        "category": category,
        "reason": reason
    })

df_comp = pd.DataFrame(comp_records)
print("\nComponent Size Distribution:")
print(f"  >= 100 nodes: {len(df_comp[df_comp['node_count'] >= 100])}")
print(f"  20 - 99 nodes: {len(df_comp[(df_comp['node_count'] >= 20) & (df_comp['node_count'] < 100)])}")
print(f"  5 - 19 nodes: {len(df_comp[(df_comp['node_count'] >= 5) & (df_comp['node_count'] < 20)])}")
print(f"  < 5 nodes: {len(df_comp[df_comp['node_count'] < 5])}")

print("\nCategory Breakdown:")
print(df_comp["category"].value_counts())

print("\nTop 5 Components:")
for idx, r in df_comp.head(5).iterrows():
    print(f"  Comp #{r['component_id']}: {r['node_count']} nodes, {r['edge_count']} edges, {r['dominant_highway']}, Roads={r['sample_roads']}")
    print(f"    Extent: [{r['min_lon']}, {r['min_lat']}] to [{r['max_lon']}, {r['max_lat']}]")
    print(f"    Reason: {r['reason']}")

print("\nSmall Components (< 5 nodes) Sample:")
for idx, r in df_comp[df_comp['node_count'] < 5].head(5).iterrows():
    print(f"  Comp #{r['component_id']}: {r['node_count']} nodes, {r['edge_count']} edges, {r['dominant_highway']}, Roads={r['sample_roads']}")
    print(f"    Extent: [{r['min_lon']}, {r['min_lat']}] to [{r['max_lon']}, {r['max_lat']}]")
    print(f"    Reason: {r['reason']}")

