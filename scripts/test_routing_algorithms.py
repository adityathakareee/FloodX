"""Test Dijkstra and A* pathfinding on MultiDiGraph."""
import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

import heapq
import math
import networkx as nx
from shapely.geometry import Point, LineString

from app.services.routing.road_network_service import road_network_service
from app.services.evacuation.flood_exposure_service import flood_exposure_service
from app.services.evacuation.road_closure_service import road_closure_service
from app.services.evacuation.dynamic_edge_weights import dynamic_weight_calculator
from app.services.evacuation.evacuation_constants import PROFILE_SAFEST, PROFILE_FASTEST, MAX_GRAPH_SPEED_MS

G = road_network_service.get_or_build_graph()
exposures = flood_exposure_service.compute_all_exposures()
blocked_edges = road_closure_service.get_active_blocked_edge_ids()

# Find two connected nodes in Component #1
G_undir = G.to_undirected()
comps = sorted(list(nx.connected_components(G_undir)), key=len, reverse=True)
comp1_nodes = list(comps[0])
print(f"Component 1 node count: {len(comp1_nodes)}")

# Pick two well-separated nodes
origin_node = comp1_nodes[0]
# Find a reachable destination node
dest_candidates = [n for n in comp1_nodes[100:200] if nx.has_path(G, origin_node, n)]
if not dest_candidates:
    dest_candidates = [n for n in comp1_nodes if nx.has_path(G, origin_node, n) and n != origin_node]

dest_node = dest_candidates[0]
print(f"Testing route from Node {origin_node} to Node {dest_node}")

# Heuristic function
dest_lat = G.nodes[dest_node]["latitude"]
dest_lon = G.nodes[dest_node]["longitude"]

def heuristic(n):
    n_lat = G.nodes[n]["latitude"]
    n_lon = G.nodes[n]["longitude"]
    # Approx metric distance
    d_m = math.hypot((n_lon - dest_lon)*105500.0, (n_lat - dest_lat)*110600.0)
    return d_m / MAX_GRAPH_SPEED_MS

# Priority Queue A* on MultiDiGraph
open_set = []
heapq.heappush(open_set, (0.0, origin_node))
came_from = {}  # node -> (prev_node, edge_id, edge_data)
g_score = {origin_node: 0.0}

found = False
while open_set:
    current_f, current = heapq.heappop(open_set)
    if current == dest_node:
        found = True
        break
        
    for neighbor in G.successors(current):
        # MultiDiGraph: find best parallel edge between current and neighbor
        edges_dict = G.get_edge_data(current, neighbor)
        best_edge_cost = float('inf')
        best_edge_id = None
        best_edge_data = None
        
        for k, e_data in edges_dict.items():
            cost = dynamic_weight_calculator.compute_edge_weight(
                e_data, exposures.get(e_data.get("edge_id")), blocked_edges, cost_profile=PROFILE_SAFEST
            )
            if cost < best_edge_cost:
                best_edge_cost = cost
                best_edge_id = e_data.get("edge_id")
                best_edge_data = e_data
                
        tentative_g = g_score[current] + best_edge_cost
        if tentative_g < g_score.get(neighbor, float('inf')):
            came_from[neighbor] = (current, best_edge_id, best_edge_data)
            g_score[neighbor] = tentative_g
            f_score = tentative_g + heuristic(neighbor)
            heapq.heappush(open_set, (f_score, neighbor))

print(f"A* Path Found: {found}")
if found:
    curr = dest_node
    path_edges = []
    while curr in came_from:
        prev, e_id, e_data = came_from[curr]
        path_edges.append(e_data)
        curr = prev
    path_edges.reverse()
    print(f"Path length: {len(path_edges)} edges")
    total_len = sum(e["length_m"] for e in path_edges)
    total_time = sum(e["estimated_travel_time_sec"] for e in path_edges)
    print(f"Total distance: {total_len:.1f} m, Base travel time: {total_time:.1f} sec")
    print("Sample road steps:")
    for e in path_edges[:5]:
        print(f"  - {e['name']} ({e['highway']}) {e['length_m']}m, oneway={e['is_oneway']}")

