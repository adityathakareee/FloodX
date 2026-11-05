"""REST API Endpoints for Emergency Resource Inventory and Allocations (FLOOD-X Phase 4)."""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status, Depends

from app.core.security import require_admin_authority, AuthenticatedAuthority
from app.services.resource_optimization.resource_models import (
    ResourceCreate,
    ResourceUpdate,
    ResourceQuantityUpdate,
    ResourceItem,
    ResourceListResponse,
    ResourceAllocateRequest,
    ResourceAllocationItem,
    AllocationApprovalRequest,
)
from app.services.resource_optimization.resource_inventory_service import resource_inventory_service
from app.services.resource_optimization.resource_allocation_service import resource_allocation_service

logger = logging.getLogger("floodx.api.resources")

router = APIRouter(prefix="/resources", tags=["Emergency Resources & Inventory"])


@router.get("", response_model=ResourceListResponse)
def list_resources(
    category: Optional[str] = Query(None, description="Filter by category (EMERGENCY_VEHICLE, HUMAN_RESOURCE, etc.)"),
    operational_status: Optional[str] = Query(None, description="Filter by status (AVAILABLE, ALLOCATED, etc.)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ResourceListResponse:
    """Lists tracked emergency resources with filtering and pagination."""
    items, total, avail_total, alloc_total = resource_inventory_service.get_resources(
        category=category,
        operational_status=operational_status,
        limit=limit,
        offset=offset,
    )
    return ResourceListResponse(
        total=total,
        limit=limit,
        offset=offset,
        available_total=avail_total,
        allocated_total=alloc_total,
        items=items,
    )


@router.get("/allocations", response_model=List[ResourceAllocationItem])
def list_allocations(
    status: Optional[str] = Query(None, description="Filter by status (PROPOSED, APPROVED, DEPLOYED, RELEASED)"),
    sector_id: Optional[str] = Query(None, description="Filter by sector ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[ResourceAllocationItem]:
    """Lists current and historical resource allocations and dispatch routes."""
    return resource_allocation_service.get_allocations(
        status=status,
        sector_id=sector_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{resource_id}", response_model=ResourceItem)
def get_resource(resource_id: int) -> ResourceItem:
    """Retrieves details of a specific emergency resource."""
    item = resource_inventory_service.get_resource_by_id(resource_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource ID {resource_id} not found.")
    return item


@router.post("", response_model=ResourceItem, status_code=status.HTTP_201_CREATED)
def create_resource(
    payload: ResourceCreate,
    authority: AuthenticatedAuthority = Depends(require_admin_authority),
) -> ResourceItem:
    """Registers a new emergency resource in inventory (Requires ADMIN Authority)."""
    try:
        return resource_inventory_service.create_resource(payload, authority.actor)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{resource_id}", response_model=ResourceItem)
def update_resource(
    resource_id: int,
    payload: ResourceUpdate,
    authority: AuthenticatedAuthority = Depends(require_admin_authority),
) -> ResourceItem:
    """Updates emergency resource metadata or quantities (Requires ADMIN Authority)."""
    try:
        return resource_inventory_service.update_resource(resource_id, payload, authority.actor)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{resource_id}/quantity", response_model=ResourceItem)
def update_resource_quantity(
    resource_id: int,
    payload: ResourceQuantityUpdate,
    authority: AuthenticatedAuthority = Depends(require_admin_authority),
) -> ResourceItem:
    """Directly updates available quantity and logs audit record (Requires ADMIN Authority)."""
    update_data = ResourceUpdate(
        available_quantity=payload.available_quantity,
        operational_status=payload.operational_status,
    )
    try:
        updated = resource_inventory_service.update_resource(
            resource_id,
            update_data,
            authority.actor,
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource ID {resource_id} not found.")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    authority: AuthenticatedAuthority = Depends(require_admin_authority),
) -> Dict[str, Any]:
    """Deletes an emergency resource from inventory (Requires ADMIN Authority)."""
    success = resource_inventory_service.delete_resource(resource_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Resource ID {resource_id} not found.")
    return {"message": f"Resource {resource_id} deleted successfully.", "deleted": True}


@router.post("/seed-demo")
def seed_demo_inventory(
    force: bool = Query(False, description="Whether to re-seed even if resources exist"),
    authority: AuthenticatedAuthority = Depends(require_admin_authority),
) -> Dict[str, Any]:
    """Seeds simulated demo resources for Pune Metropolitan flood drills (Requires ADMIN Authority)."""
    count = resource_inventory_service.seed_sample_demo_inventory(force=force)
    return {"message": f"Seeded {count} simulated Pune demo resources.", "count": count}


@router.post("/allocations/manual", response_model=ResourceAllocationItem, status_code=status.HTTP_201_CREATED)
def create_manual_allocation(
    payload: ResourceAllocateRequest,
    authority: AuthenticatedAuthority = Depends(require_admin_authority),
) -> ResourceAllocationItem:
    """Manually creates a proposed allocation with real road routing (Requires ADMIN Authority)."""
    try:
        return resource_allocation_service.create_manual_allocation(payload, authority.actor)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/allocations/approve", response_model=List[ResourceAllocationItem])
def approve_allocations(
    payload: AllocationApprovalRequest,
    authority: AuthenticatedAuthority = Depends(require_admin_authority),
) -> List[ResourceAllocationItem]:
    """Approves proposed allocations and atomically deducts inventory availability (Requires ADMIN Authority)."""
    payload.officer_name = authority.actor
    return resource_allocation_service.approve_allocations(payload)


@router.post("/allocations/{allocation_id}/release", response_model=ResourceAllocationItem)
def release_allocation(
    allocation_id: int,
    notes: Optional[str] = Query(None, description="Stand-down reason notes"),
    authority: AuthenticatedAuthority = Depends(require_admin_authority),
) -> ResourceAllocationItem:
    """Releases an allocation and restores inventory availability (Requires ADMIN Authority)."""
    try:
        return resource_allocation_service.release_allocation(
            allocation_id=allocation_id,
            officer=authority.actor,
            notes=notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
