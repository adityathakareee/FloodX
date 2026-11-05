"""REST API Endpoints for Nugen Decision Intelligence and NDMA SOP Advisories (FLOOD-X Phase 4)."""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status

from app.services.resource_optimization.resource_models import (
    NugenStatusResponse,
    DecisionAdvisoryRequest,
    DecisionAdvisoryResponse,
)
from app.services.resource_optimization.nugen_service import nugen_decision_service

logger = logging.getLogger("floodx.api.nugen")

router = APIRouter(prefix="/nugen", tags=["Nugen Decision Intelligence & NDMA SOP Advisory"])


@router.get("/status", response_model=NugenStatusResponse)
def get_nugen_integration_status() -> NugenStatusResponse:
    """Inspects Nugen credentials and reports whether live API or deterministic NDMA SOP fallback is active."""
    return nugen_decision_service.get_status()


@router.post("/advisory", response_model=DecisionAdvisoryResponse)
def generate_decision_advisory(
    payload: DecisionAdvisoryRequest,
) -> DecisionAdvisoryResponse:
    """Generates comprehensive tactical response plan aligned with NDMA Flood Standard Operating Procedures."""
    return nugen_decision_service.generate_advisory(payload)

