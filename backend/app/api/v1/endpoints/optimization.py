"""REST API Endpoints for Google OR-Tools Mathematical Optimization (FLOOD-X Phase 4)."""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status, Depends

from app.core.security import require_admin_authority, AuthenticatedAuthority
from app.services.resource_optimization.resource_models import (
    OptimizationRunRequest,
    OptimizationRunResponse,
)
from app.services.resource_optimization.resource_allocation_service import resource_allocation_service

logger = logging.getLogger("floodx.api.optimization")

router = APIRouter(prefix="/optimization", tags=["Google OR-Tools Optimization"])


@router.post("/run", response_model=OptimizationRunResponse)
def execute_optimization_run(
    payload: OptimizationRunRequest,
    authority: AuthenticatedAuthority = Depends(require_admin_authority),
) -> OptimizationRunResponse:
    """Solves multi-sector emergency resource optimization using Google OR-Tools MIP (Requires ADMIN Authority)."""
    return resource_allocation_service.execute_and_record_optimization(
        request=payload,
        officer=authority.actor,
    )


@router.get("/runs")
def list_optimization_runs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    """Retrieves history of mathematical optimization runs and their high-level outcomes."""
    return resource_allocation_service.get_optimization_runs(limit=limit, offset=offset)


@router.get("/runs/{run_id}")
def get_optimization_run(run_id: str) -> Dict[str, Any]:
    """Retrieves complete details of a specific optimization run including all dispatches and routes."""
    item = resource_allocation_service.get_optimization_run(run_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Optimization run '{run_id}' not found.")
    return item
