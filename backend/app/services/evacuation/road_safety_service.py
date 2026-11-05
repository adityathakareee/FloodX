"""Road Safety Assessment Service for FLOOD-X Phase 3.2.

Synthesizes environmental flood hazard exposure, active municipal road closures,
infrastructure status (bridges/underpasses), and directionality verification
into an actionable operational safety classification for every road graph edge.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from app.services.routing.road_network_service import road_network_service
from app.services.evacuation.flood_exposure_service import flood_exposure_service
from app.services.evacuation.road_closure_service import road_closure_service
from app.services.evacuation.evacuation_constants import (
    EXPOSURE_LOW,
    EXPOSURE_MODERATE,
    EXPOSURE_HIGH,
    EXPOSURE_CRITICAL,
    EXPOSURE_UNKNOWN,
    ROAD_STATUS_SAFE,
    ROAD_STATUS_CAUTION,
    ROAD_STATUS_HAZARDOUS,
    ROAD_STATUS_IMPASSABLE,
    EVIDENCE_OBSERVED_HAZARD,
    EVIDENCE_FORECAST_DERIVED,
    EVIDENCE_TERRAIN_SUSCEPTIBILITY,
    EVIDENCE_SIMULATED_SCENARIO,
    EVIDENCE_UNKNOWN,
    RELATIVE_EXPOSURE_LOW,
    RELATIVE_EXPOSURE_MODERATE,
    RELATIVE_EXPOSURE_HIGH,
    RELATIVE_EXPOSURE_BLOCKED,
    RELATIVE_EXPOSURE_UNKNOWN,
    HAZARD_COST_MULTIPLIER,
    CAUTION_PENALTY_SEC
)
from app.services.evacuation.evacuation_models import RoadSafetyItem

logger = logging.getLogger("floodx.evacuation.safety")


class RoadSafetyService:
    """Computes integrated operational road safety statuses for all graph edges."""

    def __init__(self):
        pass

    def evaluate_all_road_safety(self) -> Dict[str, RoadSafetyItem]:
        """Evaluates and returns safety classification for all edges in the road graph."""
        G = road_network_service.get_or_build_graph()
        exposures = flood_exposure_service.compute_all_exposures()
        active_closures = road_closure_service.get_active_closures()
        closure_map = {c.edge_id: c for c in active_closures if c.is_active}

        safety_items: Dict[str, RoadSafetyItem] = {}

        for u, v, k, d in G.edges(data=True, keys=True):
            edge_id = d.get("edge_id", f"{u}_{v}")
            exp = exposures.get(edge_id)

            tier = exp.exposure_tier if exp else EXPOSURE_UNKNOWN
            is_blocked = edge_id in closure_map
            closure = closure_map.get(edge_id)

            is_dir_assumed = d.get("is_direction_assumed", False)
            dir_status = d.get("directionality_status", "UNKNOWN_DIRECTIONALITY")
            is_bridge = d.get("is_bridge", False)
            is_tunnel = d.get("is_tunnel", False)

            # Determine operational status and qualified exposure classification
            if is_blocked:
                status = ROAD_STATUS_IMPASSABLE
                rel_class = RELATIVE_EXPOSURE_BLOCKED
                evidence_type = EVIDENCE_OBSERVED_HAZARD
                summary = f"CONFIRMED BLOCKED: {closure.reason} (Authority: {closure.reporting_authority or 'Municipal'}). Non-traversable."
                penalty = 1000000.0
            elif tier == EXPOSURE_CRITICAL:
                status = ROAD_STATUS_HAZARDOUS
                rel_class = RELATIVE_EXPOSURE_HIGH
                evidence_type = exp.evidence_type if exp else EVIDENCE_TERRAIN_SUSCEPTIBILITY
                summary = f"HIGH RELATIVE EXPOSURE: Critical riverine/hotspot exposure ({exp.exposure_reason if exp else 'River corridor'}). Screening heuristic."
                penalty = d.get("estimated_travel_time_sec", 10.0) * (HAZARD_COST_MULTIPLIER[EXPOSURE_CRITICAL] - 1.0)
            elif tier == EXPOSURE_HIGH:
                status = ROAD_STATUS_HAZARDOUS
                rel_class = RELATIVE_EXPOSURE_HIGH
                evidence_type = exp.evidence_type if exp else EVIDENCE_TERRAIN_SUSCEPTIBILITY
                summary = f"HIGH RELATIVE EXPOSURE: Potential overbank reach ({exp.exposure_reason if exp else 'River corridor'}). Screening heuristic."
                penalty = d.get("estimated_travel_time_sec", 10.0) * (HAZARD_COST_MULTIPLIER[EXPOSURE_HIGH] - 1.0)
            elif tier == EXPOSURE_MODERATE or is_dir_assumed:
                status = ROAD_STATUS_CAUTION
                rel_class = RELATIVE_EXPOSURE_MODERATE
                evidence_type = exp.evidence_type if exp else EVIDENCE_TERRAIN_SUSCEPTIBILITY
                reasons = []
                if tier == EXPOSURE_MODERATE:
                    reasons.append("Moderate flood exposure")
                if is_dir_assumed:
                    reasons.append("Unverified directionality (provisional)")
                summary = f"MODERATE RELATIVE EXPOSURE: {', '.join(reasons)}. Caution advised."
                penalty = (d.get("estimated_travel_time_sec", 10.0) * 0.5) + (CAUTION_PENALTY_SEC if is_dir_assumed else 0.0)
            else:
                status = ROAD_STATUS_SAFE
                rel_class = RELATIVE_EXPOSURE_LOW
                evidence_type = exp.evidence_type if exp else EVIDENCE_TERRAIN_SUSCEPTIBILITY
                summary = "LOW RELATIVE EXPOSURE: Screened lower terrain susceptibility (Copernicus GLO-90 DSM, river setback). Not a guarantee of dry passage."
                penalty = 0.0

            item = RoadSafetyItem(
                edge_id=edge_id,
                road_name=d.get("name", "Unnamed Road"),
                highway=d.get("highway", "unclassified"),
                exposure_tier=tier,
                operational_status=status,
                is_blocked=is_blocked,
                closure_reason=closure.reason if closure else None,
                closure_authority=closure.reporting_authority if closure else None,
                directionality_status=dir_status,
                is_direction_assumed=is_dir_assumed,
                is_bridge=is_bridge,
                is_tunnel=is_tunnel,
                evidence_type=evidence_type,
                relative_exposure_classification=rel_class,
                dynamic_travel_penalty_sec=round(penalty, 1),
                safety_summary=summary
            )
            safety_items[edge_id] = item

        return safety_items

    def get_edge_safety(self, edge_id: str) -> Optional[RoadSafetyItem]:
        """Retrieves safety record for a single edge."""
        all_safety = self.evaluate_all_road_safety()
        return all_safety.get(edge_id)


# Global singleton instance
road_safety_service = RoadSafetyService()

