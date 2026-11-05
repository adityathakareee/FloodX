"""FastAPI Endpoints for FLOOD-X Phase 3.2 Flood-Aware Evacuation Intelligence System.

Provides endpoints for:
- Operational readiness and aggregate statistics.
- Road flood exposure and road safety classification.
- Critical bridge and underpass hazard monitoring.
- Municipal road closure registration and management.
- Dynamic MultiDiGraph evacuation route planning (Fastest, Safest, Balanced).
- Shelter discovery, registration, capacity updates, and multi-factor destination ranking.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status, Header, Depends

from app.core.security import require_admin_authority, AuthenticatedAuthority, AuthorityRole
from app.services.evacuation import (
    evacuation_service,
    flood_exposure_service,
    road_safety_service,
    bridge_safety_service,
    road_closure_service,
    shelter_service,
    destination_optimizer,
    evacuation_routing_engine,
    EvacuationStatusResponse,
    EvacuationStatisticsResponse,
    RoadExposureItem,
    RoadSafetyItem,
    InfrastructureSafetyItem,
    RoadClosureCreate,
    RoadClosureUpdate,
    RoadClosureItem,
    ShelterCreate,
    ShelterUpdate,
    ShelterItem,
    RouteRequest,
    RoutePlanResponse,
    ShelterRecommendationResponse
)

router = APIRouter(prefix="/evacuation", tags=["Evacuation Intelligence"])


def verify_authority_token(authority: AuthenticatedAuthority = Depends(require_admin_authority)) -> AuthenticatedAuthority:
    """Enforces role/token authorization on all administrative write endpoints.
    
    Verifies authentication and server-established ADMIN role. Fails closed if unconfigured.
    """
    return authority


# ---------------------------------------------------------------------------
# Subsystem Status & Statistics
# ---------------------------------------------------------------------------

@router.get("/status", response_model=EvacuationStatusResponse)
def get_evacuation_status() -> EvacuationStatusResponse:
    """Returns high-level operational status, edge counts, and component readiness."""
    return evacuation_service.get_operational_status()


@router.get("/statistics", response_model=EvacuationStatisticsResponse)
def get_evacuation_statistics() -> EvacuationStatisticsResponse:
    """Returns aggregate distribution of road exposure tiers, safety statuses, and shelter capacity."""
    return evacuation_service.get_statistics()


# ---------------------------------------------------------------------------
# Road Exposure & Safety
# ---------------------------------------------------------------------------

@router.get("/roads/exposure")
def get_road_exposures(
    tier: Optional[str] = Query(None, description="Filter by exposure tier: CRITICAL_EXPOSURE, HIGH_EXPOSURE, MODERATE_EXPOSURE, LOW_EXPOSURE"),
    limit: int = Query(100, ge=1, le=2000, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Retrieves road flood hazard exposures computed from Copernicus DEM and PostGIS waterways."""
    all_exposures = flood_exposure_service.compute_all_exposures()
    items = list(all_exposures.values())

    if tier:
        items = [i for i in items if i.exposure_tier.upper() == tier.upper()]

    total = len(items)
    paginated = items[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": paginated
    }


@router.get("/roads/{edge_id}/safety", response_model=RoadSafetyItem)
def get_road_edge_safety(edge_id: str) -> RoadSafetyItem:
    """Retrieves synthesized operational safety assessment for a specific road graph edge."""
    item = road_safety_service.get_edge_safety(edge_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Road edge '{edge_id}' not found in road graph."
        )
    return item


# ---------------------------------------------------------------------------
# Critical Infrastructure (Bridges & Underpasses)
# ---------------------------------------------------------------------------

@router.get("/infrastructure", response_model=List[InfrastructureSafetyItem])
def get_all_infrastructure(
    discharge_cfs: Optional[float] = Query(None, description="Simulated Khadakwasla Dam discharge in cfs")
) -> List[InfrastructureSafetyItem]:
    """Retrieves real-time or simulated flood safety status for monitored Pune bridges and underpasses."""
    return bridge_safety_service.get_all_infrastructure(current_discharge_cfs=discharge_cfs)


@router.get("/infrastructure/{infra_id}", response_model=InfrastructureSafetyItem)
def get_infrastructure_item(
    infra_id: str,
    discharge_cfs: Optional[float] = Query(None, description="Simulated Khadakwasla Dam discharge in cfs")
) -> InfrastructureSafetyItem:
    """Retrieves safety status for a specific bridge or underpass."""
    items = bridge_safety_service.get_all_infrastructure(current_discharge_cfs=discharge_cfs)
    for it in items:
        if it.id == infra_id or it.name.lower() == infra_id.lower():
            return it
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Infrastructure item '{infra_id}' not found."
    )


# ---------------------------------------------------------------------------
# Municipal Road Closures
# ---------------------------------------------------------------------------

@router.get("/closures", response_model=List[RoadClosureItem])
def get_road_closures(
    active_only: bool = Query(True, description="Whether to return only currently active closures")
) -> List[RoadClosureItem]:
    """Returns municipal road closures and blockages."""
    if active_only:
        return road_closure_service.get_active_closures()
    return road_closure_service.get_all_closures()


@router.post("/closures", response_model=RoadClosureItem, status_code=status.HTTP_201_CREATED)
def create_road_closure(
    payload: RoadClosureCreate,
    authority: AuthenticatedAuthority = Depends(require_admin_authority)
) -> RoadClosureItem:
    """Registers an official municipal road closure or field hazard blockage (Requires ADMIN token)."""
    try:
        return road_closure_service.create_closure(payload, actor=authority.actor)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create road closure: {str(e)}"
        )


@router.patch("/closures/{closure_id}", response_model=RoadClosureItem)
def update_road_closure(
    closure_id: int,
    payload: RoadClosureUpdate,
    authority: AuthenticatedAuthority = Depends(require_admin_authority)
) -> RoadClosureItem:
    """Updates status or clears an active road closure (Requires ADMIN token)."""
    item = road_closure_service.update_closure(closure_id, payload, actor=authority.actor)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Road closure with ID {closure_id} not found."
        )
    return item


@router.delete("/closures/{closure_id}", response_model=Dict[str, Any])
def delete_road_closure(
    closure_id: int,
    cleared_by: Optional[str] = Query(None, description="Optional officer or authority identifier"),
    authority: AuthenticatedAuthority = Depends(require_admin_authority)
) -> Dict[str, Any]:
    """Deactivates and removes a road closure record (Requires ADMIN token)."""
    effective_actor = cleared_by or authority.actor
    success = road_closure_service.delete_closure(closure_id, actor=effective_actor)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Road closure with ID {closure_id} not found."
        )
    return {"status": "SUCCESS", "closure_id": closure_id, "cleared_by": effective_actor}


# ---------------------------------------------------------------------------
# Dynamic Evacuation Routing
# ---------------------------------------------------------------------------

@router.post("/routes/plan", response_model=RoutePlanResponse)
def plan_evacuation_route(request: RouteRequest) -> RoutePlanResponse:
    """Plans flood-aware evacuation route and alternatives on the MultiDiGraph."""
    return evacuation_service.plan_route(request)


# ---------------------------------------------------------------------------
# Emergency Shelters & Relief Centres
# ---------------------------------------------------------------------------

@router.get("/shelters")
def get_shelters(
    status_filter: Optional[str] = Query(None, alias="status", description="VERIFIED_SHELTER, CANDIDATE_SHELTER, UNVERIFIED_FACILITY"),
    has_medical: Optional[bool] = Query(None, description="Filter shelters with on-site medical post"),
    is_wheelchair_accessible: Optional[bool] = Query(None, description="Filter wheelchair accessible shelters"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Retrieves emergency shelters and relief facilities with capacity status."""
    items, total = shelter_service.get_shelters(
        status=status_filter,
        has_medical=has_medical,
        is_wheelchair_accessible=is_wheelchair_accessible,
        limit=limit,
        offset=offset
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items
    }


@router.get("/shelters/recommendations", response_model=ShelterRecommendationResponse)
def recommend_shelters(
    origin_lat: float = Query(..., description="Evacuation origin latitude (e.g. 18.5204)"),
    origin_lon: float = Query(..., description="Evacuation origin longitude (e.g. 73.8567)"),
    cost_profile: str = Query("BALANCED", description="FASTEST, SAFEST, BALANCED"),
    need_medical: Optional[bool] = Query(None, description="Filter for medical support"),
    need_wheelchair: Optional[bool] = Query(None, description="Filter for wheelchair accessibility"),
    max_results: int = Query(5, ge=1, le=20, description="Max shelters to recommend")
) -> ShelterRecommendationResponse:
    """Evaluates and ranks reachable emergency shelters for an evacuating citizen/ward."""
    return evacuation_service.recommend_shelters(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        cost_profile=cost_profile,
        need_medical=need_medical,
        need_wheelchair=need_wheelchair,
        max_results=max_results
    )


@router.get("/shelters/{shelter_id}", response_model=ShelterItem)
def get_shelter(shelter_id: int) -> ShelterItem:
    """Retrieves details of a single shelter by ID."""
    item = shelter_service.get_shelter_by_id(shelter_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelter with ID {shelter_id} not found."
        )
    return item


@router.post("/shelters", response_model=ShelterItem, status_code=status.HTTP_201_CREATED)
def create_shelter(
    payload: ShelterCreate,
    authority: AuthenticatedAuthority = Depends(require_admin_authority)
) -> ShelterItem:
    """Registers a new verified municipal emergency shelter (Requires ADMIN token)."""
    try:
        return shelter_service.create_shelter(payload, actor=authority.actor)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create shelter: {str(e)}"
        )


@router.patch("/shelters/{shelter_id}", response_model=ShelterItem)
def update_shelter(
    shelter_id: int,
    payload: ShelterUpdate,
    authority: AuthenticatedAuthority = Depends(require_admin_authority)
) -> ShelterItem:
    """Updates capacity, occupancy, verification status, or amenities for a shelter (Requires ADMIN token)."""
    item = shelter_service.update_shelter(shelter_id, payload, actor=authority.actor)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelter with ID {shelter_id} not found."
        )
    return item


@router.delete("/shelters/{shelter_id}", response_model=Dict[str, Any])
def delete_shelter(
    shelter_id: int,
    deleted_by: Optional[str] = Query(None, description="Optional officer or authority identifier"),
    authority: AuthenticatedAuthority = Depends(require_admin_authority)
) -> Dict[str, Any]:
    """Deactivates or deletes a shelter record (Requires ADMIN token)."""
    effective_actor = deleted_by or authority.actor
    success = shelter_service.delete_shelter(shelter_id, deleted_by=effective_actor)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shelter with ID {shelter_id} not found."
        )
    return {"status": "SUCCESS", "shelter_id": shelter_id, "deleted_by": effective_actor}
