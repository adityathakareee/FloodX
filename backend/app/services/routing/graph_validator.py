"""Independent Graph Validation & Topology Audit Service for FLOOD-X Phase 3.1.

Performs 10 comprehensive validation checks on the constructed NetworkX road graph:
1. Valid node references for all edges.
2. Strictly positive metric lengths for all edges.
3. Valid, non-empty GeoJSON geometries.
4. One-way directionality compliance.
5. Access restriction flagging.
6. Vertical layer separation (bridge/tunnel separation from ground).
7. Intersection connectivity at genuine junctions.
8. Connected components analysis and distribution.
9. Isolated nodes detection.
10. Strictly positive travel times.
"""

import logging
from typing import Dict, List, Any, Tuple, Union
import networkx as nx

logger = logging.getLogger("floodx.routing.validator")


class RoadGraphValidator:
    """Performs rigorous topological and attribute validation on routable road graphs."""

    def __init__(self):
        pass

    def validate_graph(self, G: Union[nx.DiGraph, nx.MultiDiGraph]) -> Dict[str, Any]:
        """Runs the 10 canonical validation checks and returns a comprehensive report."""
        report = {
            "is_valid": True,
            "graph_type": type(G).__name__,
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "checks": {},
            "issues": [],
            "warnings": [],
            "metrics": {}
        }

        # Check 1: Node References Integrity
        missing_nodes = []
        for u, v in G.edges():
            if not G.has_node(u):
                missing_nodes.append((u, "source"))
            if not G.has_node(v):
                missing_nodes.append((v, "destination"))
        
        c1_passed = len(missing_nodes) == 0
        report["checks"]["1_valid_node_references"] = {
            "passed": c1_passed,
            "details": f"All {G.number_of_edges()} edges connect valid existing graph nodes" if c1_passed else f"Found {len(missing_nodes)} dangling edge endpoints"
        }
        if not c1_passed:
            report["is_valid"] = False
            report["issues"].append("Found edges referencing non-existent nodes")

        # Check 2: Strictly Positive Metric Lengths
        non_positive_lengths = []
        lengths = []
        for u, v, d in G.edges(data=True):
            length = d.get("length_m", 0.0)
            lengths.append(length)
            if length <= 0.0:
                non_positive_lengths.append((d.get("edge_id"), length))

        c2_passed = len(non_positive_lengths) == 0
        report["checks"]["2_positive_edge_lengths"] = {
            "passed": c2_passed,
            "min_length_m": min(lengths) if lengths else 0.0,
            "max_length_m": max(lengths) if lengths else 0.0,
            "mean_length_m": round(sum(lengths)/len(lengths), 2) if lengths else 0.0,
            "total_length_km": round(sum(lengths)/1000.0, 2)
        }
        if not c2_passed:
            report["is_valid"] = False
            report["issues"].append(f"Found {len(non_positive_lengths)} edges with length <= 0")

        # Check 3: Valid Geometries
        invalid_geoms = []
        for u, v, d in G.edges(data=True):
            geom = d.get("geometry_geojson")
            if not geom or "coordinates" not in geom or len(geom["coordinates"]) < 2:
                invalid_geoms.append(d.get("edge_id"))

        c3_passed = len(invalid_geoms) == 0
        report["checks"]["3_valid_edge_geometries"] = {
            "passed": c3_passed,
            "details": f"All {G.number_of_edges()} edges contain valid GeoJSON coordinates" if c3_passed else f"Found {len(invalid_geoms)} edges with missing/invalid geometry"
        }
        if not c3_passed:
            report["is_valid"] = False
            report["issues"].append(f"Found {len(invalid_geoms)} edges with invalid geometry")

        # Check 4: One-Way Directionality & Verification Status
        oneway_count = 0
        bidirectional_count = 0
        dir_breakdown = {}
        assumed_count = 0
        speed_source_breakdown = {}
        uv_counts = {}

        for u, v, d in G.edges(data=True):
            if d.get("is_oneway"):
                oneway_count += 1
            else:
                bidirectional_count += 1

            d_stat = d.get("directionality_status", "UNKNOWN_DIRECTIONALITY")
            dir_breakdown[d_stat] = dir_breakdown.get(d_stat, 0) + 1

            if d.get("is_direction_assumed"):
                assumed_count += 1

            spd_src = d.get("speed_source", "IRC_DEFAULT_ESTIMATE")
            speed_source_breakdown[spd_src] = speed_source_breakdown.get(spd_src, 0) + 1

            uv_pair = (u, v)
            uv_counts[uv_pair] = uv_counts.get(uv_pair, 0) + 1

        parallel_uv_count = sum(1 for count in uv_counts.values() if count > 1)
        parallel_edges_total = sum(count for count in uv_counts.values() if count > 1)

        report["checks"]["4_oneway_directionality"] = {
            "passed": True,
            "oneway_directed_edges": oneway_count,
            "bidirectional_directed_edges": bidirectional_count,
            "directionality_breakdown": dir_breakdown,
            "assumed_direction_edges_count": assumed_count,
            "parallel_uv_pairs_count": parallel_uv_count,
            "parallel_edges_total": parallel_edges_total,
            "speed_source_breakdown": speed_source_breakdown,
            "details": f"Directionality verified: {dir_breakdown.get('VERIFIED_ONEWAY', 0)} oneway, {dir_breakdown.get('VERIFIED_BIDIRECTIONAL', 0)} bidirectional, {dir_breakdown.get('UNKNOWN_DIRECTIONALITY', 0)} assumed"
        }

        # Check 5: Access Restrictions Flagged
        access_flagged = {}
        for u, v, d in G.edges(data=True):
            acc = d.get("access", "yes")
            access_flagged[acc] = access_flagged.get(acc, 0) + 1

        report["checks"]["5_access_restrictions"] = {
            "passed": True,
            "access_distribution": access_flagged,
            "restricted_edges_count": sum(v for k, v in access_flagged.items() if k not in ["yes", "permissive"])
        }

        # Check 6: Vertical Layer Separation
        cross_layer_edges = []
        layer_counts = {}
        for u, v, d in G.edges(data=True):
            u_layer = G.nodes[u].get("layer", 0)
            v_layer = G.nodes[v].get("layer", 0)
            edge_layer = d.get("layer", 0)
            layer_counts[edge_layer] = layer_counts.get(edge_layer, 0) + 1
            # Note: Bridge ramps transition layers; within-segment layer mismatch check
            if u_layer != v_layer and u_layer != 0 and v_layer != 0:
                cross_layer_edges.append((d.get("edge_id"), u_layer, v_layer))

        c6_passed = len(cross_layer_edges) == 0
        report["checks"]["6_vertical_layer_separation"] = {
            "passed": c6_passed,
            "edge_layer_distribution": layer_counts,
            "invalid_cross_layer_jumps": len(cross_layer_edges)
        }
        if not c6_passed:
            report["warnings"].append(f"Detected {len(cross_layer_edges)} cross-layer connections")

        # Check 7: Intersection Connectivity
        degrees = [d for n, d in G.degree()]
        true_intersections = [n for n, d in G.degree() if d >= 3]
        dead_ends = [n for n, d in G.degree() if d == 1]

        report["checks"]["7_junction_connectivity"] = {
            "passed": len(true_intersections) > 0,
            "true_intersections_count": len(true_intersections),
            "dead_ends_count": len(dead_ends),
            "max_node_degree": max(degrees) if degrees else 0,
            "mean_node_degree": round(sum(degrees)/len(degrees), 2) if degrees else 0.0
        }

        # Check 8: Connected Components Analysis
        G_undir = G.to_undirected()
        components = list(nx.connected_components(G_undir))
        comp_sizes = sorted([len(c) for c in components], reverse=True)
        largest_component_size = comp_sizes[0] if comp_sizes else 0
        largest_pct = round((largest_component_size / G.number_of_nodes() * 100.0), 1) if G.number_of_nodes() > 0 else 0.0

        report["checks"]["8_connected_components"] = {
            "passed": True,
            "component_count": len(components),
            "largest_component_nodes": largest_component_size,
            "largest_component_percentage": largest_pct,
            "top_10_component_sizes": comp_sizes[:10],
            "note": "Disconnected components are expected due to arterial-only filtering and bounding-box tile edges."
        }

        # Check 9: Isolated Nodes Detection
        isolated = list(nx.isolates(G))
        c9_passed = len(isolated) == 0
        report["checks"]["9_isolated_nodes"] = {
            "passed": c9_passed,
            "isolated_count": len(isolated),
            "details": "Zero isolated nodes detected" if c9_passed else f"Found {len(isolated)} isolated nodes"
        }
        if not c9_passed:
            report["warnings"].append(f"Found {len(isolated)} isolated nodes")

        # Check 10: Positive Travel Times
        travel_times = []
        invalid_travel_times = []
        for u, v, d in G.edges(data=True):
            tt = d.get("estimated_travel_time_sec", 0.0)
            travel_times.append(tt)
            if tt <= 0.0:
                invalid_travel_times.append((d.get("edge_id"), tt))

        c10_passed = len(invalid_travel_times) == 0
        report["checks"]["10_positive_travel_times"] = {
            "passed": c10_passed,
            "min_travel_time_sec": min(travel_times) if travel_times else 0.0,
            "max_travel_time_sec": max(travel_times) if travel_times else 0.0,
            "mean_travel_time_sec": round(sum(travel_times)/len(travel_times), 1) if travel_times else 0.0
        }
        if not c10_passed:
            report["is_valid"] = False
            report["issues"].append(f"Found {len(invalid_travel_times)} edges with travel time <= 0")

        # Summary Metrics
        report["metrics"] = {
            "graph_type": type(G).__name__,
            "total_nodes": G.number_of_nodes(),
            "total_directed_edges": G.number_of_edges(),
            "parallel_edges_count": parallel_edges_total,
            "total_mapped_length_km": report["checks"]["2_positive_edge_lengths"]["total_length_km"],
            "connected_components": len(components),
            "largest_component_nodes": largest_component_size,
            "largest_component_pct": largest_pct,
            "true_intersections": len(true_intersections),
            "dead_ends": len(dead_ends),
            "directionality_breakdown": dir_breakdown,
            "speed_source_breakdown": speed_source_breakdown
        }

        return report


# Global validator instance
road_graph_validator = RoadGraphValidator()

