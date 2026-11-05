"""FastAPI REST endpoints for Road Network Intelligence & Routable GIS Graph.

PCCOE International Grand Challenge 2026.
FLOOD-X Phase 3.1: Road Network Intelligence & GIS Graph Construction.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query, Header

from app.services.routing.routing_models import (
    NetworkStatusResponse,
    NetworkStatisticsResponse,
    RoadsPaginatedResponse,
    NodesPaginatedResponse,
    RebuildResponse
)
from app.services.routing.road_network_service import road_network_service
from app.services.routing.routing_constants import ROUTING_REBUILD_TOKEN

logger = logging.getLogger("floodx.api.routing")
router = APIRouter(prefix="/routing", tags=["Road Network & Evacuation Routing"])


@router.get("/network/status", response_model=NetworkStatusResponse)
def get_road_network_status() -> NetworkStatusResponse:
    """Returns operational status, topology metrics, and data quality warnings for the road graph."""
    try:
        return road_network_service.get_status()
    except Exception as e:
        logger.error("Error retrieving road network status: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Road network status error: {str(e)}"
        )


@router.get("/network/statistics", response_model=NetworkStatisticsResponse)
def get_road_network_statistics() -> NetworkStatisticsResponse:
    """Returns detailed attribute distributions, degree metrics, and connected component statistics."""
    try:
        return road_network_service.get_statistics()
    except Exception as e:
        logger.error("Error computing road network statistics: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Road network statistics error: {str(e)}"
        )


@router.get("/network/roads", response_model=RoadsPaginatedResponse)
def get_road_edges(
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    highway: Optional[str] = Query(None, description="Filter by highway classification (e.g. primary, secondary, trunk)"),
    min_lat: Optional[float] = Query(None, ge=18.0, le=19.0, description="Bounding box min latitude"),
    max_lat: Optional[float] = Query(None, ge=18.0, le=19.0, description="Bounding box max latitude"),
    min_lon: Optional[float] = Query(None, ge=73.0, le=75.0, description="Bounding box min longitude"),
    max_lon: Optional[float] = Query(None, ge=73.0, le=75.0, description="Bounding box max longitude")
) -> RoadsPaginatedResponse:
    """Retrieves paginated road edges with GeoJSON geometry, metric length, and estimated travel time."""
    try:
        return road_network_service.get_roads(
            limit=limit,
            offset=offset,
            highway=highway,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon
        )
    except Exception as e:
        logger.error("Error retrieving road edges: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Road edges query error: {str(e)}"
        )


@router.get("/network/nodes", response_model=NodesPaginatedResponse)
def get_graph_nodes(
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    min_lat: Optional[float] = Query(None, ge=18.0, le=19.0, description="Bounding box min latitude"),
    max_lat: Optional[float] = Query(None, ge=18.0, le=19.0, description="Bounding box max latitude"),
    min_lon: Optional[float] = Query(None, ge=73.0, le=75.0, description="Bounding box min longitude"),
    max_lon: Optional[float] = Query(None, ge=73.0, le=75.0, description="Bounding box max longitude")
) -> NodesPaginatedResponse:
    """Retrieves paginated graph nodes with coordinates, degree metrics, and elevation layers."""
    try:
        return road_network_service.get_nodes(
            limit=limit,
            offset=offset,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon
        )
    except Exception as e:
        logger.error("Error retrieving graph nodes: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph nodes query error: {str(e)}"
        )


@router.post("/network/rebuild", response_model=RebuildResponse)
def rebuild_road_network_graph(
    x_routing_token: Optional[str] = Header(None, alias="X-Routing-Token", description="Authorization token for administrative graph rebuild"),
    token: Optional[str] = Query(None, description="Optional query parameter token fallback")
) -> RebuildResponse:
    """Rebuilds the routable road graph from source geometries with fresh intersection splitting."""
    auth_token = x_routing_token or token
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required for road graph rebuild (pass X-Routing-Token header)"
        )

    try:
        return road_network_service.rebuild_graph(auth_token)
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe)
        )
    except Exception as e:
        logger.error("Error rebuilding road network graph: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph rebuild error: {str(e)}"
        )

