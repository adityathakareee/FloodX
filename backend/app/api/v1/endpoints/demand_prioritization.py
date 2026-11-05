"""REST API Endpoints for Emergency Demand Estimation and Response Prioritization (FLOOD-X Phase 4)."""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status

from app.services.resource_optimization.resource_models import (
    DemandAssessmentResponse,
    PriorityRankingResponse,
)
from app.services.resource_optimization.emergency_demand_service import emergency_demand_service
from app.services.resource_optimization.priority_assessment_service import priority_assessment_service

logger = logging.getLogger("floodx.api.demand_prioritization")

router = APIRouter(tags=["Emergency Demand & Decision Intelligence"])


@router.get("/demand/assessments", response_model=DemandAssessmentResponse)
def get_demand_assessments(
    rainfall_multiplier: float = Query(1.0, ge=0.5, le=5.0, description="Simulated rainfall multiplier"),
    dam_discharge_cfs: float = Query(0.0, ge=0.0, le=100000.0, description="Simulated Khadakwasla Dam discharge in cfs"),
) -> DemandAssessmentResponse:
    """Evaluates emergency resource demand across 8 operational sectors in Pune Basin."""
    return emergency_demand_service.generate_demand_assessments(
        rainfall_multiplier=rainfall_multiplier,
        dam_discharge_cfs=dam_discharge_cfs,
        is_simulation=False,
    )


@router.get("/decision/priorities", response_model=PriorityRankingResponse)
def get_priority_rankings() -> PriorityRankingResponse:
    """Retrieves ranked priority operational areas with transparent multi-factor scoring breakdown."""
    return priority_assessment_service.get_ranked_priority_areas()

