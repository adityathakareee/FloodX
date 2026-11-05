"""Service for Emergency Response Area Prioritization and Transparent Explanations."""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Any
from app.services.resource_optimization.resource_constants import (
    WEIGHT_RISK,
    WEIGHT_DEMAND,
    WEIGHT_ACCESSIBILITY,
    WEIGHT_INFRASTRUCTURE,
    NDMA_SOP_GUIDELINES,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_MODERATE,
    PRIORITY_LOW,
)
from app.services.resource_optimization.resource_models import (
    PriorityAreaItem,
    PriorityRankingResponse,
    DemandAssessmentItem,
)
from app.services.resource_optimization.emergency_demand_service import emergency_demand_service

logger = logging.getLogger("floodx.services.priority_assessment")


class PriorityAssessmentService:
    """Ranks geographic sectors in Pune Basin using a multi-factor transparent prioritization model."""

    def __init__(self, db_engine=None):
        self._engine = db_engine

    def get_ranked_priority_areas(
        self,
        demand_items: Optional[List[DemandAssessmentItem]] = None
    ) -> PriorityRankingResponse:
        """Returns ordered response priority areas with transparent explanations."""
        now = datetime.now(timezone.utc)

        # Generate fresh assessments if not provided
        if not demand_items:
            res = emergency_demand_service.generate_demand_assessments()
            demand_items = res.sectors

        # Sort descending by composite priority score
        sorted_sectors = sorted(demand_items, key=lambda s: s.priority_score, reverse=True)

        ranked_items: List[PriorityAreaItem] = []
        for idx, item in enumerate(sorted_sectors, start=1):
            # Breakdown of weighted contributions
            breakdown = {
                "risk_contribution_pts": round(item.risk_score * WEIGHT_RISK, 2),
                "demand_contribution_pts": round(item.demand_score * WEIGHT_DEMAND, 2),
                "accessibility_penalty_pts": round(item.accessibility_score * WEIGHT_ACCESSIBILITY, 2),
                "infrastructure_vulnerability_pts": round(item.infrastructure_score * WEIGHT_INFRASTRUCTURE, 2),
            }

            # Identify primary driver
            max_driver = max(breakdown.items(), key=lambda kv: kv[1])
            driver_names = {
                "risk_contribution_pts": "Hydrological Flood Susceptibility & Terrain Depression (<550m DEM)",
                "demand_contribution_pts": "High Estimated Medical and Swift Water Rescue Demand",
                "accessibility_penalty_pts": "Road Closure Network Disconnection & Barrier Isolation",
                "infrastructure_vulnerability_pts": "Extended Distance to Level-1 Trauma Hospital Facilities",
            }
            primary_driver = driver_names.get(max_driver[0], "Multi-factor environmental hazard")

            # Contributing indicators
            indicators = [
                f"Terrain Risk Score: {item.risk_score}/100 (Weight: {int(WEIGHT_RISK*100)}%)",
                f"Emergency Demand Score: {item.demand_score}/100 (Weight: {int(WEIGHT_DEMAND*100)}%)",
                f"Road Inaccessibility Penalty: {item.accessibility_score}/100 (Weight: {int(WEIGHT_ACCESSIBILITY*100)}%)",
                f"Critical Facility Vulnerability: {item.infrastructure_score}/100 (Weight: {int(WEIGHT_INFRASTRUCTURE*100)}%)",
                f"Requires: {item.required_ambulances} Ambulances, {item.required_rescue_teams} Rescue Teams, {item.required_food_packets} Meals",
            ]

            # Recommended tactical action from NDMA SOP
            sop_actions = NDMA_SOP_GUIDELINES.get(item.priority_level, NDMA_SOP_GUIDELINES[PRIORITY_MODERATE])
            tactical_action = sop_actions[0] if sop_actions else "Maintain active civil defense monitoring."

            ranked_items.append(
                PriorityAreaItem(
                    rank=idx,
                    sector_id=item.sector_id,
                    sector_name=item.sector_name,
                    latitude=item.latitude,
                    longitude=item.longitude,
                    priority_level=item.priority_level,
                    priority_score=item.priority_score,
                    score_breakdown=breakdown,
                    primary_risk_driver=primary_driver,
                    contributing_indicators=indicators,
                    missing_data_disclaimer=(
                        "Demographic counts and casualty numbers are unverified heuristics. "
                        "Prioritization is an operational guideline based on topographic elevation and river proximity."
                    ),
                    recommended_tactical_action=tactical_action,
                )
            )

        weight_formula = (
            f"Priority Score = ({WEIGHT_RISK} × Risk) + ({WEIGHT_DEMAND} × Demand) + "
            f"({WEIGHT_ACCESSIBILITY} × Accessibility) + ({WEIGHT_INFRASTRUCTURE} × Infrastructure)"
        )

        return PriorityRankingResponse(
            ranked_at=now,
            methodology="Multi-Factor Linear Weighted Prioritization Model with NDMA SOP Alignment",
            weight_formula=weight_formula,
            ranked_areas=ranked_items,
        )


# Singleton instance
priority_assessment_service = PriorityAssessmentService()
