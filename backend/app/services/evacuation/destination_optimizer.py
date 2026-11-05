"""Evacuation Destination Optimizer for FLOOD-X Phase 3.2.

Ranks and recommends emergency shelters and relief centers with strict data integrity:
- Only officially verified shelters (VERIFIED_SHELTER) are recommended as confirmed destinations.
- If no verified shelter is available, returns NO_VERIFIED_SHELTER_AVAILABLE with candidate facilities separated for manual review.
- Never fabricates capacity bonuses for unknown or unverified capacities.
- Hard-excludes transit routes blocked by active municipal road closures.
- Transparently reports scoring rationale, reachability, and capacity status.
"""

import math
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import networkx as nx

from app.services.routing.road_network_service import road_network_service
from app.services.evacuation.flood_exposure_service import flood_exposure_service
from app.services.evacuation.road_closure_service import road_closure_service
from app.services.evacuation.shelter_service import shelter_service
from app.services.evacuation.routing_algorithms import evacuation_routing_engine
from app.services.evacuation.evacuation_constants import (
    PROFILE_BALANCED,
    SHELTER_VERIFIED,
    SHELTER_CANDIDATE,
    SHELTER_UNVERIFIED,
    SHELTER_INACTIVE,
    MAX_ORIGIN_SNAP_DISTANCE_M
)
from app.services.evacuation.evacuation_models import (
    ShelterItem,
    ShelterRecommendationItem,
    ShelterRecommendationResponse
)

logger = logging.getLogger("floodx.evacuation.optimizer")


class DestinationOptimizer:
    """Evaluates and ranks candidate shelters for an evacuating citizen or ward."""

    def __init__(self):
        pass

    def recommend_destinations(
        self,
        origin_lat: float,
        origin_lon: float,
        cost_profile: str = PROFILE_BALANCED,
        need_medical: Optional[bool] = None,
        need_wheelchair: Optional[bool] = None,
        max_results: int = 5
    ) -> ShelterRecommendationResponse:
        """Finds and ranks the safest, most suitable evacuation destinations."""
        now_str = datetime.now(timezone.utc).isoformat()
        warnings: List[str] = []

        # 1. Snap origin coordinate
        orig_node, orig_dist = evacuation_routing_engine.snap_coordinate_to_node(origin_lat, origin_lon)
        if orig_node is None:
            return ShelterRecommendationResponse(
                status="OUT_OF_BOUNDS",
                origin_lat=origin_lat,
                origin_lon=origin_lon,
                total_evaluated=0,
                recommendations=[],
                candidate_facilities_for_review=[],
                warnings=[f"Origin coordinate ({origin_lat:.4f}, {origin_lon:.4f}) is {orig_dist:.1f}m from nearest road, exceeding {MAX_ORIGIN_SNAP_DISTANCE_M}m threshold."],
                generated_at_utc=now_str
            )

        # 2. Retrieve candidate shelters from database
        all_shelters, total_count = shelter_service.get_shelters(limit=100)
        eligible_shelters: List[ShelterItem] = []

        for s in all_shelters:
            if s.verification_status == SHELTER_INACTIVE:
                continue
            # If total_capacity is verified and available is explicitly 0, skip as full
            if s.total_capacity is not None and s.available_capacity is not None and s.available_capacity <= 0:
                continue
            if need_medical and not s.has_medical_support:
                continue
            if need_wheelchair and not s.is_wheelchair_accessible:
                continue
            eligible_shelters.append(s)

        if not eligible_shelters:
            return ShelterRecommendationResponse(
                status="NO_VERIFIED_SHELTER_AVAILABLE",
                origin_lat=origin_lat,
                origin_lon=origin_lon,
                total_evaluated=0,
                recommendations=[],
                candidate_facilities_for_review=[],
                warnings=["No eligible shelters matched the requested criteria or available capacity."],
                generated_at_utc=now_str
            )

        G = road_network_service.get_or_build_graph()
        exposures = flood_exposure_service.compute_all_exposures()
        blocked_edges = road_closure_service.get_active_blocked_edge_ids()

        # Find connected component of origin
        orig_component = None
        for comp in nx.weakly_connected_components(G):
            if orig_node in comp:
                orig_component = comp
                break

        verified_items: List[ShelterRecommendationItem] = []
        candidate_items: List[ShelterRecommendationItem] = []

        for s in eligible_shelters:
            s_node, s_dist = evacuation_routing_engine.snap_coordinate_to_node(s.latitude, s.longitude)
            if s_node is None or orig_component is None or s_node not in orig_component:
                # Euclidean fallback for unreachable
                dx = (s.longitude - origin_lon) * 105500.0
                dy = (s.latitude - origin_lat) * 110600.0
                euc_dist = round(math.hypot(dx, dy), 1)

                rec_item = ShelterRecommendationItem(
                    shelter=s,
                    distance_to_origin_m=euc_dist,
                    estimated_travel_time_sec=0.0,
                    safest_route_hazard_tier="UNREACHABLE",
                    is_reachable=False,
                    suitability_score=0.0,
                    ranking_rationale="Shelter is in a disconnected road network component; road access severed by river or boundary.",
                    capacity_status="Capacity unverified" if s.total_capacity is None else f"{s.available_capacity or 0} remaining"
                )
                if s.verification_status == SHELTER_VERIFIED:
                    verified_items.append(rec_item)
                else:
                    candidate_items.append(rec_item)
                continue

            # Compute actual path using A* with hard closure avoidance
            path_edges = evacuation_routing_engine._compute_path(
                G=G,
                origin_node=orig_node,
                dest_node=s_node,
                cost_profile=cost_profile,
                algorithm="A_STAR",
                exposures=exposures,
                blocked_edges=blocked_edges,
                avoid_closed=True
            )

            if path_edges is None:
                # Reachable in component, but currently path blocked by closures
                dx = (s.longitude - origin_lon) * 105500.0
                dy = (s.latitude - origin_lat) * 110600.0
                euc_dist = round(math.hypot(dx, dy), 1)

                rec_item = ShelterRecommendationItem(
                    shelter=s,
                    distance_to_origin_m=euc_dist,
                    estimated_travel_time_sec=0.0,
                    safest_route_hazard_tier="BLOCKED",
                    is_reachable=False,
                    suitability_score=0.0,
                    ranking_rationale="Transit route blocked by active municipal road closures or confirmed impassable bridges.",
                    capacity_status="Capacity unverified" if s.total_capacity is None else f"{s.available_capacity or 0} remaining"
                )
                if s.verification_status == SHELTER_VERIFIED:
                    verified_items.append(rec_item)
                else:
                    candidate_items.append(rec_item)
                continue

            # Route summary metrics
            total_dist_m = sum(float(e.get("length_m", 10.0)) for e in path_edges)
            total_time_s = sum(float(e.get("free_flow_travel_time_sec", 1.0)) for e in path_edges)

            # Analyze exposure along route
            hazard_counts = {"CRITICAL_EXPOSURE": 0, "HIGH_EXPOSURE": 0, "MODERATE_EXPOSURE": 0, "LOW_EXPOSURE": 0}
            for e in path_edges:
                eid = e.get("edge_id", "")
                exp = exposures.get(eid)
                tier = exp.exposure_tier if exp else "UNKNOWN_EXPOSURE"
                if tier in hazard_counts:
                    hazard_counts[tier] += 1

            worst_tier = "LOW_EXPOSURE"
            if hazard_counts["CRITICAL_EXPOSURE"] > 0:
                worst_tier = "CRITICAL_EXPOSURE"
            elif hazard_counts["HIGH_EXPOSURE"] > 0:
                worst_tier = "HIGH_EXPOSURE"
            elif hazard_counts["MODERATE_EXPOSURE"] > 0:
                worst_tier = "MODERATE_EXPOSURE"

            # Compute Multi-factor Suitability Score (0 - 100)
            # Base verification score: 60 for verified, 40 for candidate, 20 for unverified
            if s.verification_status == SHELTER_VERIFIED:
                base_score = 60.0
            elif s.verification_status == SHELTER_CANDIDATE:
                base_score = 40.0
            else:
                base_score = 20.0

            # Travel time penalty (up to -25 points for 30 min travel)
            travel_mins = total_time_s / 60.0
            time_pen = min(25.0, travel_mins * 0.8)

            # Hazard penalty
            hazard_pen = (hazard_counts["CRITICAL_EXPOSURE"] * 10.0) + (hazard_counts["HIGH_EXPOSURE"] * 4.0)
            hazard_pen = min(30.0, hazard_pen)

            # Capacity bonus: ONLY if verified and documented available capacity > 50
            # Strict rule: NEVER give capacity bonus for unknown capacity!
            cap_bonus = 0.0
            if s.verification_status == SHELTER_VERIFIED and s.available_capacity is not None and s.available_capacity > 50:
                cap_bonus = 10.0

            # Amenity bonus: ONLY if verified
            amenity_bonus = 0.0
            if s.verification_status == SHELTER_VERIFIED:
                if s.has_medical_support:
                    amenity_bonus += 5.0
                if s.is_wheelchair_accessible:
                    amenity_bonus += 5.0

            final_score = max(5.0, min(100.0, base_score - time_pen - hazard_pen + cap_bonus + amenity_bonus))

            # Capacity label (strictly never invent numbers)
            if s.total_capacity is not None and s.available_capacity is not None:
                cap_label = f"Confirmed Capacity: {s.available_capacity}/{s.total_capacity} available"
            elif s.total_capacity is not None:
                cap_label = f"Documented Total Capacity: {s.total_capacity} (Occupancy unverified)"
            else:
                cap_label = "Capacity unverified by municipal authorities"

            # Rationale text
            rationale_parts = []
            if s.verification_status == SHELTER_VERIFIED:
                rationale_parts.append(f"Official municipal shelter (Doc: {s.evidence_document or 'Verified Record'})")
            else:
                rationale_parts.append(f"{s.verification_status.replace('_', ' ').title()} (Requires Field Verification)")

            rationale_parts.append(f"reachable in {travel_mins:.1f} mins ({total_dist_m/1000.0:.2f} km)")

            if worst_tier in ["CRITICAL_EXPOSURE", "HIGH_EXPOSURE"]:
                rationale_parts.append(f"crosses {hazard_counts['CRITICAL_EXPOSURE'] + hazard_counts['HIGH_EXPOSURE']} flood-exposed segments")
            else:
                rationale_parts.append("routes along elevated low-hazard arterials")

            rationale = "; ".join(rationale_parts) + "."

            rec_item = ShelterRecommendationItem(
                shelter=s,
                distance_to_origin_m=round(total_dist_m, 1),
                estimated_travel_time_sec=round(total_time_s, 1),
                safest_route_hazard_tier=worst_tier,
                is_reachable=True,
                suitability_score=round(final_score, 1),
                ranking_rationale=rationale,
                capacity_status=cap_label
            )

            if s.verification_status == SHELTER_VERIFIED:
                verified_items.append(rec_item)
            else:
                candidate_items.append(rec_item)

        # Sort verified items descending by suitability
        def sort_key(item: ShelterRecommendationItem):
            return (
                1 if item.is_reachable else 0,
                item.suitability_score,
                -item.estimated_travel_time_sec
            )

        verified_items.sort(key=sort_key, reverse=True)
        candidate_items.sort(key=sort_key, reverse=True)

        top_verified = verified_items[:max_results]
        top_candidates = candidate_items[:max_results]

        if not top_verified:
            resp_status = "NO_VERIFIED_SHELTER_AVAILABLE"
            warnings.append(
                "No officially gazetted municipal shelters are currently registered and verified in the database. "
                "Candidate facilities are provided for emergency authority reconnaissance only. "
                "Do not direct citizens to unverified facilities without prior field inspection."
            )
        else:
            resp_status = "SUCCESS"

        return ShelterRecommendationResponse(
            status=resp_status,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            total_evaluated=len(verified_items) + len(candidate_items),
            recommendations=top_verified,
            candidate_facilities_for_review=top_candidates,
            warnings=warnings,
            generated_at_utc=now_str
        )


# Global singleton instance
destination_optimizer = DestinationOptimizer()
