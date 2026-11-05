"""Master Evacuation Intelligence Service for FLOOD-X Phase 3.2.

Coordinates:
- Environmental flood exposure mapping.
- Road safety classification.
- Critical bridge and underpass monitoring.
- Municipal road closures.
- Dynamic route planning (A* & Dijkstra with multi-criteria profiles).
- Shelter discovery, verification, and suitability ranking.
- System-wide operational status and statistics aggregation.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from app.services.routing.road_network_service import road_network_service
from app.services.evacuation.flood_exposure_service import flood_exposure_service
from app.services.evacuation.road_safety_service import road_safety_service
from app.services.evacuation.bridge_safety_service import bridge_safety_service
from app.services.evacuation.road_closure_service import road_closure_service
from app.services.evacuation.shelter_service import shelter_service
from app.services.evacuation.routing_algorithms import evacuation_routing_engine
from app.services.evacuation.destination_optimizer import destination_optimizer
from app.services.evacuation.evacuation_constants import (
    ROAD_STATUS_SAFE,
    ROAD_STATUS_CAUTION,
    ROAD_STATUS_HAZARDOUS,
    ROAD_STATUS_IMPASSABLE,
    EXPOSURE_LOW,
    EXPOSURE_MODERATE,
    EXPOSURE_HIGH,
    EXPOSURE_CRITICAL,
    SHELTER_VERIFIED,
    SHELTER_CANDIDATE,
    SHELTER_UNVERIFIED,
    OFFICIAL_EMERGENCY_DISCLAIMER
)
from app.services.evacuation.evacuation_models import (
    EvacuationStatusResponse,
    EvacuationStatisticsResponse,
    RouteRequest,
    RoutePlanResponse,
    ShelterRecommendationResponse
)

logger = logging.getLogger("floodx.evacuation.master")


class EvacuationIntelligenceService:
    """Master facade coordinating all Phase 3.2 flood-aware evacuation operations."""

    def __init__(self):
        pass

    def get_operational_status(self) -> EvacuationStatusResponse:
        """Aggregates high-level subsystem operational readiness and edge counts."""
        now_str = datetime.now(timezone.utc).isoformat()
        G = road_network_service.get_or_build_graph()
        all_safety = road_safety_service.evaluate_all_road_safety()
        closures = road_closure_service.get_active_closures()
        shelters, total_shelters = shelter_service.get_shelters(limit=200)
        infra = bridge_safety_service.get_all_infrastructure()

        safe_cnt = sum(1 for s in all_safety.values() if s.operational_status == ROAD_STATUS_SAFE)
        caution_cnt = sum(1 for s in all_safety.values() if s.operational_status == ROAD_STATUS_CAUTION)
        hazard_cnt = sum(1 for s in all_safety.values() if s.operational_status == ROAD_STATUS_HAZARDOUS)
        impassable_cnt = sum(1 for s in all_safety.values() if s.operational_status == ROAD_STATUS_IMPASSABLE)

        verified_shelters = sum(1 for sh in shelters if sh.verification_status == SHELTER_VERIFIED)
        candidate_shelters = sum(1 for sh in shelters if sh.verification_status in [SHELTER_CANDIDATE, SHELTER_UNVERIFIED])

        submerged_sim = sum(1 for b in infra if b.is_closed)

        return EvacuationStatusResponse(
            status="READY",
            graph_type="MultiDiGraph",
            total_network_edges=G.number_of_edges(),
            total_safe_edges=safe_cnt,
            total_caution_edges=caution_cnt,
            total_hazardous_edges=hazard_cnt,
            total_impassable_edges=impassable_cnt,
            active_road_closures=len(closures),
            total_registered_shelters=total_shelters,
            verified_shelters_count=verified_shelters,
            candidate_shelters_count=candidate_shelters,
            critical_bridges_count=len(infra),
            submerged_bridges_simulated=submerged_sim,
            last_assessment_timestamp_utc=now_str,
            data_quality_disclaimer=OFFICIAL_EMERGENCY_DISCLAIMER
        )

    def get_statistics(self) -> EvacuationStatisticsResponse:
        """Returns detailed statistical distribution across exposure, status, and shelters."""
        exposures = flood_exposure_service.compute_all_exposures()
        all_safety = road_safety_service.evaluate_all_road_safety()
        closures = road_closure_service.get_active_closures()
        shelters, _ = shelter_service.get_shelters(limit=200)
        infra = bridge_safety_service.get_all_infrastructure()

        # Exposure breakdown
        exp_dist = {EXPOSURE_LOW: 0, EXPOSURE_MODERATE: 0, EXPOSURE_HIGH: 0, EXPOSURE_CRITICAL: 0}
        for exp in exposures.values():
            if exp.exposure_tier in exp_dist:
                exp_dist[exp.exposure_tier] += 1

        # Operational status breakdown
        op_dist = {ROAD_STATUS_SAFE: 0, ROAD_STATUS_CAUTION: 0, ROAD_STATUS_HAZARDOUS: 0, ROAD_STATUS_IMPASSABLE: 0}
        for s in all_safety.values():
            if s.operational_status in op_dist:
                op_dist[s.operational_status] += 1

        # Shelter breakdown
        sh_dist = {SHELTER_VERIFIED: 0, SHELTER_CANDIDATE: 0, SHELTER_UNVERIFIED: 0}
        total_ver_cap = 0
        total_ver_occ = 0

        for sh in shelters:
            st = sh.verification_status
            sh_dist[st] = sh_dist.get(st, 0) + 1
            if st == SHELTER_VERIFIED and sh.total_capacity is not None:
                total_ver_cap += sh.total_capacity
                total_ver_occ += (sh.current_occupancy or 0)

        return EvacuationStatisticsResponse(
            exposure_tier_distribution=exp_dist,
            operational_status_distribution=op_dist,
            shelter_status_distribution=sh_dist,
            total_verified_capacity=total_ver_cap if total_ver_cap > 0 else None,
            total_verified_occupancy=total_ver_occ,
            active_closures_count=len(closures),
            infrastructure_monitored_count=len(infra)
        )

    def plan_route(self, request: RouteRequest) -> RoutePlanResponse:
        """Plans evacuation routes using specified profile and pathfinding algorithm."""
        return evacuation_routing_engine.plan_evacuation_routes(request)

    def recommend_shelters(
        self,
        origin_lat: float,
        origin_lon: float,
        cost_profile: str = "BALANCED",
        need_medical: Optional[bool] = None,
        need_wheelchair: Optional[bool] = None,
        max_results: int = 5
    ) -> ShelterRecommendationResponse:
        """Ranks reachable shelters with verified capacity and flood-avoiding paths."""
        return destination_optimizer.recommend_destinations(
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            cost_profile=cost_profile,
            need_medical=need_medical,
            need_wheelchair=need_wheelchair,
            max_results=max_results
        )


# Global singleton instance
evacuation_service = EvacuationIntelligenceService()

