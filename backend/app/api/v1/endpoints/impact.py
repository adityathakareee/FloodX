"""FastAPI endpoints for Multi-Sector Flood Impact Assessment & SAR Satellite Overlays.

FLOOD-X Phase 5: Complete Intelligence Integration.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.impact import (
    ImpactAssessmentResponse,
    ImpactAssessmentRequest,
    ImpactScenariosResponse,
    ImpactLayersResponse,
)
from app.services.impact.impact_assessment_service import impact_assessment_service

logger = logging.getLogger("floodx.api.impact")
router = APIRouter(prefix="/impact", tags=["Flood Impact Assessment"])


@router.get("/latest", response_model=ImpactAssessmentResponse)
def get_latest_impact_assessment(
    hazard_source: str = Query("OBSERVED_SAR_EXTENT", description="Hazard source (OBSERVED_SAR_EXTENT or SIMULATED_SCENARIO)")
) -> ImpactAssessmentResponse:
    """Returns the baseline or latest observed multi-sector flood impact assessment."""
    try:
        return impact_assessment_service.assess_impact(
            hazard_source=hazard_source,
            scenario_name="Baseline Sentinel-1 Observed Extent"
        )
    except Exception as e:
        logger.error("Error generating latest impact assessment: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Impact assessment error: {str(e)}"
        )


@router.post("/assess", response_model=ImpactAssessmentResponse)
def run_scenario_impact_assessment(
    request: ImpactAssessmentRequest
) -> ImpactAssessmentResponse:
    """Executes a multi-sector GIS impact assessment for a simulated discharge or hazard input."""
    try:
        return impact_assessment_service.assess_impact(
            hazard_source=request.hazard_source,
            simulated_discharge_cfs=request.simulated_discharge_cfs,
            rain_rate_mmh=request.rain_rate_mmh,
            scenario_name=request.scenario_name or "Custom Dam Release Scenario"
        )
    except Exception as e:
        logger.error("Error generating scenario impact assessment: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario impact error: {str(e)}"
        )


@router.get("/scenarios", response_model=ImpactScenariosResponse)
def get_historical_impact_scenarios() -> ImpactScenariosResponse:
    """Returns audited historical flood disaster impact comparisons for Pune (July 2024, Aug 2019, Sept 2019)."""
    try:
        return impact_assessment_service.get_historical_scenarios()
    except Exception as e:
        logger.error("Error fetching historical impact scenarios: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Historical scenarios error: {str(e)}"
        )


@router.get("/layers", response_model=ImpactLayersResponse)
def get_impact_map_layers(
    hazard_source: str = Query("OBSERVED_SAR_EXTENT", description="Hazard source layer")
) -> ImpactLayersResponse:
    """Returns GeoJSON FeatureCollections for SAR flood extent, critical bridges, exposed healthcare, and road segments."""
    try:
        return impact_assessment_service.get_impact_map_layers(hazard_source=hazard_source)
    except Exception as e:
        logger.error("Error generating impact map layers: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Map layers error: {str(e)}"
        )

