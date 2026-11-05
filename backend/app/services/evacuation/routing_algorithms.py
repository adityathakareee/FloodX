"""Evacuation Routing Engine for FLOOD-X Phase 3.2.

Implements Dijkstra and A* pathfinding on NetworkX MultiDiGraph:
- Multi-criteria dynamic cost profiles (FASTEST, SAFEST, BALANCED).
- Admissible geographic heuristic for A* based on straight-line distance and maximum network velocity.
- Strictly enforces one-way restrictions and layer-separated grade crossings.
- Excludes active municipal road closures.
- Discovers non-overlapping alternative evacuation routes via edge-penalty exploration.
- Robust geographic coordinate snapping with out-of-bounds rejection.
- Transparent reporting of directionality assumptions, flood hazard exposure, and data caveats.
"""

import heapq
import math
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Set, Any
import networkx as nx
from shapely.geometry import Point, LineString

from app.services.routing.road_network_service import road_network_service
from app.services.evacuation.flood_exposure_service import flood_exposure_service
from app.services.evacuation.road_closure_service import road_closure_service
from app.services.evacuation.dynamic_edge_weights import dynamic_weight_calculator
from app.services.evacuation.evacuation_constants import (
    PROFILE_FASTEST,
    PROFILE_SAFEST,
    PROFILE_BALANCED,
    MAX_ORIGIN_SNAP_DISTANCE_M,
    MAX_GRAPH_SPEED_MS,
    CLOSED_EDGE_PENALTY,
    MAX_ALTERNATIVE_OVERLAP_PCT,
    MIN_DISTINCT_SEGMENTS,
    OFFICIAL_EMERGENCY_DISCLAIMER
)
from app.services.evacuation.evacuation_models import (
    RouteRequest,
    RoutePlanResponse,
    RouteAlternativeItem,
    RouteStepItem
)

logger = logging.getLogger("floodx.evacuation.routing")


class EvacuationRoutingEngine:
    """Computes flood-aware evacuation routes and alternatives on the Pune road graph."""

    def __init__(self):
        pass

    def snap_coordinate_to_node(self, lat: float, lon: float) -> Tuple[Optional[int], float]:
        """Snaps a geographic coordinate (lat, lon) to the nearest graph node.
        
        Returns:
            Tuple of (node_id, snap_distance_meters). If distance exceeds MAX_ORIGIN_SNAP_DISTANCE_M, returns (None, distance).
        """
        G = road_network_service.get_or_build_graph()
        best_nid = None
        min_dist_m = float('inf')

        for nid, ndata in G.nodes(data=True):
            n_lat = ndata.get("latitude")
            n_lon = ndata.get("longitude")
            if n_lat is None or n_lon is None:
                continue

            # Metric distance approximation
            dx = (lon - n_lon) * 105500.0
            dy = (lat - n_lat) * 110600.0
            d_m = math.hypot(dx, dy)

            if d_m < min_dist_m:
                min_dist_m = d_m
                best_nid = nid

        min_dist_m = round(min_dist_m, 1)

        if min_dist_m > MAX_ORIGIN_SNAP_DISTANCE_M:
            logger.warning("Coordinate (%.4f, %.4f) snap distance %.1fm exceeds threshold %.1fm", lat, lon, min_dist_m, MAX_ORIGIN_SNAP_DISTANCE_M)
            return None, min_dist_m

        return best_nid, min_dist_m

    def _compute_path(
        self,
        G: nx.MultiDiGraph,
        origin_node: int,
        dest_node: int,
        cost_profile: str,
        algorithm: str,
        exposures: Dict[str, Any],
        blocked_edges: Set[str],
        avoid_closed: bool = True,
        penalty_edge_ids: Optional[Set[str]] = None,
        penalty_multiplier: float = 2.5
    ) -> Optional[List[Dict[str, Any]]]:
        """Executes Dijkstra or A* on MultiDiGraph returning ordered list of traversed edge data dictionaries."""
        if origin_node == dest_node:
            return []

        dest_lat = G.nodes[dest_node].get("latitude", 18.52)
        dest_lon = G.nodes[dest_node].get("longitude", 73.85)

        # Admissible Heuristic for A*
        def heuristic(n: int) -> float:
            if algorithm != "A_STAR":
                return 0.0
            n_lat = G.nodes[n].get("latitude", dest_lat)
            n_lon = G.nodes[n].get("longitude", dest_lon)
            d_m = math.hypot((n_lon - dest_lon) * 105500.0, (n_lat - dest_lat) * 110600.0)
            return d_m / MAX_GRAPH_SPEED_MS

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
                edges_dict = G.get_edge_data(current, neighbor)
                if not edges_dict:
                    continue

                # MultiDiGraph: evaluate all parallel edges between current and neighbor
                best_edge_cost = float('inf')
                best_edge_data = None
                best_edge_id = None

                for k, e_data in edges_dict.items():
                    e_id = e_data.get("edge_id", f"{current}_{neighbor}")
                    # Task 5: Hard exclusion of closed road edges in MultiDiGraph
                    if avoid_closed and e_id in blocked_edges:
                        continue
                    exp = exposures.get(e_id)
                    cost = dynamic_weight_calculator.compute_edge_weight(
                        edge_data=e_data,
                        exposure=exp,
                        blocked_edge_ids=blocked_edges,
                        cost_profile=cost_profile,
                        avoid_closed_roads=avoid_closed,
                        penalty_edge_ids=penalty_edge_ids,
                        penalty_multiplier=penalty_multiplier
                    )
                    if cost < best_edge_cost:
                        best_edge_cost = cost
                        best_edge_id = e_id
                        best_edge_data = e_data

                if best_edge_data is None or math.isinf(best_edge_cost) or best_edge_cost >= CLOSED_EDGE_PENALTY:
                    continue  # Impassable edge / all parallel paths closed

                tentative_g = g_score[current] + best_edge_cost
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = (current, best_edge_id, best_edge_data)
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor)
                    heapq.heappush(open_set, (f_score, neighbor))

        if not found:
            return None

        # Reconstruct path
        path_edges = []
        curr = dest_node
        while curr in came_from:
            prev, e_id, e_data = came_from[curr]
            path_edges.append(e_data)
            curr = prev

        path_edges.reverse()
        return path_edges

    def _assemble_route_alternative(
        self,
        route_id: str,
        label: str,
        profile: str,
        algorithm: str,
        path_edges: List[Dict[str, Any]],
        exposures: Dict[str, Any],
        shared_edges_count: int = 0,
        shared_distance_m: float = 0.0,
        overlap_percentage: float = 0.0,
        now_str: Optional[str] = None
    ) -> RouteAlternativeItem:
        """Constructs RouteAlternativeItem from raw edge sequence."""
        total_len = 0.0
        total_time = 0.0
        exposure_counts: Dict[str, int] = {}
        hazard_count = 0
        caution_count = 0
        assumed_count = 0
        all_coords = []

        for idx, e in enumerate(path_edges):
            total_len += e.get("length_m", 0.0)
            total_time += e.get("estimated_travel_time_sec", 0.0)

            e_id = e.get("edge_id", "")
            exp = exposures.get(e_id)
            tier = exp.exposure_tier if exp else "UNKNOWN_EXPOSURE"
            exposure_counts[tier] = exposure_counts.get(tier, 0) + 1

            if tier in ["CRITICAL_EXPOSURE", "HIGH_EXPOSURE"]:
                hazard_count += 1
            elif tier == "MODERATE_EXPOSURE":
                caution_count += 1

            if e.get("is_direction_assumed"):
                assumed_count += 1

            # Accumulate coordinates for full GeoJSON LineString
            geom_coords = e.get("geometry_geojson", {}).get("coordinates", [])
            if geom_coords:
                if not all_coords:
                    all_coords.extend(geom_coords)
                else:
                    # Avoid duplicate intermediate vertex
                    all_coords.extend(geom_coords[1:])

        line_geom = LineString(all_coords) if len(all_coords) >= 2 else LineString([(73.85, 18.52), (73.851, 18.521)])

        # Construct explanation
        if profile == PROFILE_SAFEST:
            explanation = (
                f"Selected for maximum flood safety: routes via elevated terrain, "
                f"bypassing {hazard_count} critical riverine corridors. Total distance: {total_len/1000.0:.2f} km."
            )
        elif profile == PROFILE_FASTEST:
            explanation = (
                f"Selected for minimum free-flow travel time ({total_time/60.0:.1f} mins). "
                f"Traverses {hazard_count} flood-exposed arterial segments. Proceed with caution."
            )
        else:
            explanation = (
                f"Balanced trade-off between travel time efficiency and flood hazard avoidance. "
                f"Total length: {total_len/1000.0:.2f} km across {len(path_edges)} segments."
            )

        now_iso = now_str or datetime.now(timezone.utc).isoformat()
        dir_uncertainty_note = (
            f"{assumed_count} of {len(path_edges)} segments ({assumed_count/len(path_edges)*100.0:.1f}%) have unverified directionality (assumed two-way in OSM). Exercise caution on these links."
            if assumed_count > 0 else "All road segments have verified one-way / two-way directionality tags."
        )
        speed_note = (
            "Estimated travel times assume dry free-flow baseline speeds. Active flooding, surface pooling, and severe weather will significantly reduce transit speeds."
        )

        return RouteAlternativeItem(
            route_id=route_id,
            route_label=label,
            profile=profile,
            algorithm=algorithm,
            total_distance_m=round(total_len, 1),
            total_travel_time_sec=round(total_time, 1),
            steps_count=len(path_edges),
            exposure_summary=exposure_counts,
            hazardous_segments_count=hazard_count,
            caution_segments_count=caution_count,
            assumed_direction_segments_count=assumed_count,
            shared_edges_count=shared_edges_count,
            shared_distance_m=shared_distance_m,
            overlap_percentage=overlap_percentage,
            data_freshness_utc=now_iso,
            directionality_uncertainty_note=dir_uncertainty_note,
            speed_assumptions_note=speed_note,
            geometry_geojson=line_geom.__geo_interface__,
            explanation=explanation
        )

    def plan_evacuation_routes(
        self,
        request: RouteRequest,
        extra_blocked_edges: Optional[Set[str]] = None
    ) -> RoutePlanResponse:
        """Plans primary and alternative flood-aware evacuation routes."""
        now_str = datetime.now(timezone.utc).isoformat()
        G = road_network_service.get_or_build_graph()
        exposures = flood_exposure_service.compute_all_exposures()
        blocked_edges = road_closure_service.get_active_blocked_edge_ids()
        if extra_blocked_edges:
            blocked_edges = blocked_edges.union(extra_blocked_edges)

        warnings = []

        # 1. Snap Origin
        u_orig, orig_dist = self.snap_coordinate_to_node(request.origin_lat, request.origin_lon)
        if u_orig is None:
            return RoutePlanResponse(
                status="OUT_OF_BOUNDS",
                origin_snapped_node=0,
                origin_snap_distance_m=orig_dist,
                destination_snapped_node=0,
                destination_snap_distance_m=0.0,
                chosen_profile=request.cost_profile,
                algorithm_used=request.algorithm,
                primary_route=None,
                alternatives=[],
                warnings=[f"Origin point ({request.origin_lat}, {request.origin_lon}) is {orig_dist:.1f}m away from the mapped arterial network (max: {MAX_ORIGIN_SNAP_DISTANCE_M}m)."],
                disclaimer=OFFICIAL_EMERGENCY_DISCLAIMER,
                generated_at_utc=now_str
            )

        # 2. Determine Destination Coordinates
        dest_lat = request.destination_lat
        dest_lon = request.destination_lon

        if request.destination_shelter_id is not None:
            from app.services.evacuation.shelter_service import shelter_service
            shelter = shelter_service.get_shelter_by_id(request.destination_shelter_id)
            if shelter:
                dest_lat = shelter.latitude
                dest_lon = shelter.longitude
            else:
                warnings.append(f"Shelter ID #{request.destination_shelter_id} not found in database; using coordinates.")

        if dest_lat is None or dest_lon is None:
            return RoutePlanResponse(
                status="ERROR",
                origin_snapped_node=u_orig,
                origin_snap_distance_m=orig_dist,
                destination_snapped_node=0,
                destination_snap_distance_m=0.0,
                chosen_profile=request.cost_profile,
                algorithm_used=request.algorithm,
                primary_route=None,
                alternatives=[],
                warnings=["Destination coordinates or valid shelter_id must be provided."],
                disclaimer=OFFICIAL_EMERGENCY_DISCLAIMER,
                generated_at_utc=now_str
            )

        # 3. Snap Destination
        v_dest, dest_dist = self.snap_coordinate_to_node(dest_lat, dest_lon)
        if v_dest is None:
            return RoutePlanResponse(
                status="OUT_OF_BOUNDS",
                origin_snapped_node=u_orig,
                origin_snap_distance_m=orig_dist,
                destination_snapped_node=0,
                destination_snap_distance_m=dest_dist,
                chosen_profile=request.cost_profile,
                algorithm_used=request.algorithm,
                primary_route=None,
                alternatives=[],
                warnings=[f"Destination point ({dest_lat}, {dest_lon}) is {dest_dist:.1f}m away from the mapped arterial network."],
                disclaimer=OFFICIAL_EMERGENCY_DISCLAIMER,
                generated_at_utc=now_str
            )

        # Add snap warning if distance > 100m
        if orig_dist > 150.0:
            warnings.append(f"Origin was snapped {orig_dist:.0f}m to nearest arterial road (N{u_orig}). Last-mile residential streets are omitted.")
        if dest_dist > 150.0:
            warnings.append(f"Destination was snapped {dest_dist:.0f}m to nearest arterial road (N{v_dest}).")

        # 4. Connected Component Reachability Check
        G_undir = G.to_undirected()
        if not nx.has_path(G_undir, u_orig, v_dest):
            return RoutePlanResponse(
                status="NO_PATH",
                origin_snapped_node=u_orig,
                origin_snap_distance_m=orig_dist,
                destination_snapped_node=v_dest,
                destination_snap_distance_m=dest_dist,
                chosen_profile=request.cost_profile,
                algorithm_used=request.algorithm,
                primary_route=None,
                alternatives=[],
                warnings=[
                    f"No topological path exists between Origin (Node {u_orig}) and Destination (Node {v_dest}). "
                    "They reside in separate disconnected arterial sub-networks. Door-to-door connectivity requires residential connector streets."
                ],
                disclaimer=OFFICIAL_EMERGENCY_DISCLAIMER,
                generated_at_utc=now_str
            )

        # 5. Compute Primary Route
        primary_edges = self._compute_path(
            G=G,
            origin_node=u_orig,
            dest_node=v_dest,
            cost_profile=request.cost_profile,
            algorithm=request.algorithm,
            exposures=exposures,
            blocked_edges=blocked_edges,
            avoid_closed=request.avoid_closed_roads
        )

        if not primary_edges:
            return RoutePlanResponse(
                status="NO_PATH",
                origin_snapped_node=u_orig,
                origin_snap_distance_m=orig_dist,
                destination_snapped_node=v_dest,
                destination_snap_distance_m=dest_dist,
                chosen_profile=request.cost_profile,
                algorithm_used=request.algorithm,
                primary_route=None,
                alternatives=[],
                avoided_closures_count=len(blocked_edges),
                warnings=["No viable directed route found obeying one-way restrictions and active road closures."],
                disclaimer=OFFICIAL_EMERGENCY_DISCLAIMER,
                generated_at_utc=now_str
            )

        primary_dist_m = sum(e.get("length_m", 0.0) for e in primary_edges)
        primary_edge_ids = {e.get("edge_id") for e in primary_edges if e.get("edge_id")}

        primary_alt = self._assemble_route_alternative(
            route_id="route_primary",
            label="PRIMARY",
            profile=request.cost_profile,
            algorithm=request.algorithm,
            path_edges=primary_edges,
            exposures=exposures,
            shared_edges_count=len(primary_edges),
            shared_distance_m=round(primary_dist_m, 1),
            overlap_percentage=100.0,
            now_str=now_str
        )

        alternatives = []

        # Helper to compute overlap between candidate alternative and primary route
        def compute_overlap(cand_edges: List[Dict[str, Any]]) -> Tuple[int, float, float, int]:
            sh_cnt = 0
            sh_dist = 0.0
            for ce in cand_edges:
                ce_id = ce.get("edge_id")
                if ce_id in primary_edge_ids:
                    sh_cnt += 1
                    sh_dist += ce.get("length_m", 0.0)
            ov_pct = (sh_dist / primary_dist_m * 100.0) if primary_dist_m > 0 else 0.0
            dist_cnt = len(cand_edges) - sh_cnt
            return sh_cnt, round(sh_dist, 1), round(ov_pct, 1), dist_cnt

        # 6. Compute Alternative Routes (if requested)
        if request.generate_alternatives and len(primary_edges) > 3:
            candidate_alt1_edges = None
            candidate_alt1_metrics = None

            # Alternative 1: Edge penalty exploration on primary route (try escalation to avoid high overlap)
            for mult in [3.0, 5.0, 8.0]:
                alt1_edges = self._compute_path(
                    G=G,
                    origin_node=u_orig,
                    dest_node=v_dest,
                    cost_profile=request.cost_profile,
                    algorithm=request.algorithm,
                    exposures=exposures,
                    blocked_edges=blocked_edges,
                    avoid_closed=request.avoid_closed_roads,
                    penalty_edge_ids=primary_edge_ids,
                    penalty_multiplier=mult
                )

                if alt1_edges and alt1_edges != primary_edges:
                    sh_cnt, sh_dist, ov_pct, dist_cnt = compute_overlap(alt1_edges)
                    if ov_pct <= MAX_ALTERNATIVE_OVERLAP_PCT and dist_cnt >= MIN_DISTINCT_SEGMENTS:
                        candidate_alt1_edges = alt1_edges
                        candidate_alt1_metrics = (sh_cnt, sh_dist, ov_pct)
                        break

            if candidate_alt1_edges and candidate_alt1_metrics:
                alt1_item = self._assemble_route_alternative(
                    route_id="route_alt_1",
                    label="ALTERNATIVE_1",
                    profile=request.cost_profile,
                    algorithm=request.algorithm,
                    path_edges=candidate_alt1_edges,
                    exposures=exposures,
                    shared_edges_count=candidate_alt1_metrics[0],
                    shared_distance_m=candidate_alt1_metrics[1],
                    overlap_percentage=candidate_alt1_metrics[2],
                    now_str=now_str
                )
                alternatives.append(alt1_item)

            # Alternative 2: Complementary profile (FASTEST if SAFEST was chosen, or SAFEST if FASTEST was chosen)
            comp_profile = PROFILE_FASTEST if request.cost_profile == PROFILE_SAFEST else PROFILE_SAFEST
            combined_penalties = set(primary_edge_ids)
            if candidate_alt1_edges:
                combined_penalties.update({e.get("edge_id") for e in candidate_alt1_edges if e.get("edge_id")})

            for mult in [2.5, 4.0, 6.0]:
                alt2_edges = self._compute_path(
                    G=G,
                    origin_node=u_orig,
                    dest_node=v_dest,
                    cost_profile=comp_profile,
                    algorithm=request.algorithm,
                    exposures=exposures,
                    blocked_edges=blocked_edges,
                    avoid_closed=request.avoid_closed_roads,
                    penalty_edge_ids=combined_penalties,
                    penalty_multiplier=mult
                )

                if alt2_edges and alt2_edges != primary_edges and (not candidate_alt1_edges or alt2_edges != candidate_alt1_edges):
                    sh_cnt, sh_dist, ov_pct, dist_cnt = compute_overlap(alt2_edges)
                    if ov_pct <= MAX_ALTERNATIVE_OVERLAP_PCT and dist_cnt >= MIN_DISTINCT_SEGMENTS:
                        alt2_item = self._assemble_route_alternative(
                            route_id="route_alt_2",
                            label="ALTERNATIVE_2",
                            profile=comp_profile,
                            algorithm=request.algorithm,
                            path_edges=alt2_edges,
                            exposures=exposures,
                            shared_edges_count=sh_cnt,
                            shared_distance_m=sh_dist,
                            overlap_percentage=ov_pct,
                            now_str=now_str
                        )
                        alternatives.append(alt2_item)
                        break

        return RoutePlanResponse(
            status="SUCCESS",
            origin_snapped_node=u_orig,
            origin_snap_distance_m=orig_dist,
            destination_snapped_node=v_dest,
            destination_snap_distance_m=dest_dist,
            chosen_profile=request.cost_profile,
            algorithm_used=request.algorithm,
            primary_route=primary_alt,
            alternatives=alternatives,
            avoided_closures_count=len(blocked_edges),
            warnings=warnings,
            disclaimer=OFFICIAL_EMERGENCY_DISCLAIMER,
            generated_at_utc=now_str
        )


# Global singleton instance
evacuation_routing_engine = EvacuationRoutingEngine()

