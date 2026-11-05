"""FastAPI REST endpoints for Prospective Flood-Risk Intelligence and Forecast Integration.

PCCOE International Grand Challenge 2026.
FLOOD-X Phase 2.3: Prospective Flood-Risk Intelligence & Forecast Integration.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query

from app.schemas.prospective import (
    ProspectiveStatusResponse,
    ProspectiveForecastResponse,
    ProspectiveSourcesResponse,
    ProspectiveAssessmentResponse,
    ScenarioAssessmentRequest,
    ScenarioAssessmentResponse
)
from app.services.prospective.forecast_service import forecast_service
from app.services.prospective.dam_telemetry_service import dam_telemetry_service
from app.services.prospective.prospective_inference import prospective_inference_service

logger = logging.getLogger("floodx.api.prospective")
router = APIRouter(prefix="/prospective", tags=["Prospective Intelligence"])


@router.get("/status", response_model=ProspectiveStatusResponse)
def get_prospective_status() -> ProspectiveStatusResponse:
    """Returns operational status, forecast freshness, and dam telemetry availability."""
    now_utc = datetime.now(timezone.utc).isoformat()
    freshness = forecast_service.evaluate_freshness()
    dam_status = dam_telemetry_service.check_telemetry_status()

    # Determine status based on freshness
    op_status = "READY"
    if freshness["data_freshness_status"] in ["STALE", "EXPIRED"]:
        op_status = "DEGRADED"
    elif freshness["data_freshness_status"] == "DATA_INSUFFICIENT":
        op_status = "ERROR"

    return ProspectiveStatusResponse(
        status=op_status,
        engine_name="FLOOD-X Prospective Hydrometeorological Risk Engine v1.0",
        engine_type="EXPERIMENTAL_RULE_BASED_ENGINE",
        prediction_task="PROSPECTIVE_RISK_ASSESSMENT",
        horizons_supported=["6h", "12h", "24h", "48h"],
        forecast_source="Open-Meteo High-Resolution Numerical Weather Prediction (ECMWF/DWD/GFS)",
        forecast_freshness_status=freshness["data_freshness_status"],
        forecast_issue_time_utc=freshness["forecast_issue_time_utc"] or now_utc,
        api_retrieval_time_utc=freshness["last_retrieval_utc"],
        cache_age_hours=freshness["cache_age_hours"],
        forecast_age_hours=freshness["forecast_age_hours"],
        freshness_warning=freshness["freshness_warning"],
        dam_telemetry_status=dam_status["telemetry_status"],
        human_verification_required=True,
        timestamp_utc=now_utc
    )


@router.get("/forecast", response_model=ProspectiveForecastResponse)
def get_prospective_forecast(
    horizon_hours: int = Query(48, ge=6, le=168, description="Forecast horizon in hours (6 to 168)")
) -> ProspectiveForecastResponse:
    """Returns forward-looking hourly forecast data for Pune pilot basin."""
    try:
        return forecast_service.get_forecast_summary(max_hours=horizon_hours)
    except Exception as e:
        logger.error("Error retrieving prospective forecast: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast retrieval error: {str(e)}"
        )


@router.get("/sources", response_model=ProspectiveSourcesResponse)
def get_sources_assessment() -> ProspectiveSourcesResponse:
    """Returns the official assessment and status catalog of investigated forecast and dam sources."""
    return prospective_inference_service.get_sources_catalog()


@router.get("/benchmarks")
def get_dam_discharge_benchmarks() -> Dict[str, Any]:
    """Returns documented physical discharge benchmarks for Khadakwasla Dam and Pune riverbanks."""
    return dam_telemetry_service.get_canonical_benchmarks()


@router.post("/assess", response_model=ProspectiveAssessmentResponse)
def assess_prospective_risk(
    simulated_dam_discharge_cfs: Optional[float] = Query(
        None,
        description="Optional Khadakwasla Dam discharge scenario in cfs (e.g., 15000 for Bhide causeway, 35574 for July 2024 disaster)"
    )
) -> ProspectiveAssessmentResponse:
    """Executes multi-horizon prospective flood risk assessment across 6h, 12h, 24h, and 48h windows."""
    try:
        return prospective_inference_service.generate_live_assessment(
            simulated_dam_discharge_cfs=simulated_dam_discharge_cfs
        )
    except Exception as e:
        logger.error("Error generating prospective assessment: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prospective assessment error: {str(e)}"
        )


@router.post("/scenario", response_model=ScenarioAssessmentResponse)
def assess_what_if_scenario(request: ScenarioAssessmentRequest) -> ScenarioAssessmentResponse:
    """Runs a What-If scenario simulation with custom rainfall scaling, peak intensity, and dam discharge."""
    try:
        return prospective_inference_service.generate_scenario_assessment(request)
    except Exception as e:
        logger.error("Error generating scenario assessment: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario simulation error: {str(e)}"
        )

