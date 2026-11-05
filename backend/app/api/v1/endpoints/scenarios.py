"""REST API Endpoints for What-If Disaster Scenario Simulation (FLOOD-X Phase 4)."""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status

from app.services.resource_optimization.resource_models import (
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
)
from app.services.resource_optimization.scenario_simulation_service import scenario_simulation_service

logger = logging.getLogger("floodx.api.scenarios")

router = APIRouter(prefix="/scenarios", tags=["What-If Disaster Simulation"])


@router.post("/simulate", response_model=ScenarioSimulationResponse)
def simulate_disaster_scenario(
    payload: ScenarioSimulationRequest,
) -> ScenarioSimulationResponse:
    """Executes isolated in-memory what-if disaster simulation without mutating live database records."""
    return scenario_simulation_service.run_simulation(payload)

