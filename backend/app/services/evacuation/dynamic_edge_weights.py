"""Dynamic Road-Edge Weighting Engine for FLOOD-X Phase 3.2.

Computes dynamic traversal costs for Dijkstra and A* pathfinding algorithms across
different operational routing profiles (FASTEST, SAFEST, BALANCED) without
mutating baseline graph attributes or destroying physical network measurements.
"""

import math
from typing import Dict, Set, Optional, Any
from app.services.evacuation.evacuation_constants import (
    PROFILE_FASTEST,
    PROFILE_SAFEST,
    PROFILE_BALANCED,
    EXPOSURE_LOW,
    EXPOSURE_MODERATE,
    EXPOSURE_HIGH,
    EXPOSURE_CRITICAL,
    EXPOSURE_UNKNOWN,
    HAZARD_COST_MULTIPLIER,
    CAUTION_PENALTY_SEC,
    CLOSED_EDGE_PENALTY
)
from app.services.evacuation.evacuation_models import RoadExposureItem


class DynamicEdgeWeightCalculator:
    """Calculates non-destructive dynamic edge traversal costs."""

    def __init__(self):
        pass

    def compute_edge_weight(
        self,
        edge_data: Dict[str, Any],
        exposure: Optional[RoadExposureItem],
        blocked_edge_ids: Set[str],
        cost_profile: str = PROFILE_SAFEST,
        avoid_closed_roads: bool = True,
        penalty_edge_ids: Optional[Set[str]] = None,
        penalty_multiplier: float = 2.5
    ) -> float:
        """Calculates dynamic routing cost in seconds for a single directed edge.
        
        Args:
            edge_data: Edge attribute dictionary from MultiDiGraph.
            exposure: Precomputed environmental hazard exposure item.
            blocked_edge_ids: Set of active closure edge IDs.
            cost_profile: FASTEST, SAFEST, or BALANCED.
            avoid_closed_roads: If True, returns CLOSED_EDGE_PENALTY (infinity) for blocked edges.
            penalty_edge_ids: Optional set of edges to penalize (for alternative route generation).
            penalty_multiplier: Multiplier applied to penalty_edge_ids.
        """
        edge_id = edge_data.get("edge_id", "")

        # 1. Blocked / Closed Road Check - Hard Exclusion
        if avoid_closed_roads and edge_id in blocked_edge_ids:
            return float("inf")

        # 2. Baseline Kinematic Travel Time (seconds)
        t_baseline = float(edge_data.get("estimated_travel_time_sec", 10.0))
        tier = exposure.exposure_tier if exposure else EXPOSURE_UNKNOWN
        is_dir_assumed = bool(edge_data.get("is_direction_assumed", False))

        # 3. Apply Profile Cost Formula
        if cost_profile == PROFILE_FASTEST:
            # Minimize pure travel time; slight caution for unverified directionality
            cost = t_baseline + (10.0 if is_dir_assumed else 0.0)

        elif cost_profile == PROFILE_SAFEST:
            # Heavily penalize flood hazard exposure and riverbank proximity
            hazard_mult = HAZARD_COST_MULTIPLIER.get(tier, 2.0)
            caution_fixed = CAUTION_PENALTY_SEC if is_dir_assumed else 0.0
            cost = (t_baseline * hazard_mult) + caution_fixed

        elif cost_profile == PROFILE_BALANCED:
            # Trade-off between travel time efficiency and hazard exposure
            hazard_mult = HAZARD_COST_MULTIPLIER.get(tier, 2.0)
            balanced_mult = 1.0 + 0.35 * (hazard_mult - 1.0)
            cost = t_baseline * balanced_mult + (15.0 if is_dir_assumed else 0.0)

        else:
            cost = t_baseline

        # 4. Apply Alternative Route Penalty (if requested to find disjoint paths)
        if penalty_edge_ids and edge_id in penalty_edge_ids:
            cost *= penalty_multiplier

        if math.isinf(cost):
            return float("inf")

        return max(0.1, round(cost, 2))


# Global calculator instance
dynamic_weight_calculator = DynamicEdgeWeightCalculator()

