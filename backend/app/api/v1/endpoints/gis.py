"""API endpoints for GIS vector features, layer catalogs, and spatial queries."""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from geoalchemy2.shape import to_shape

from app.core.database import get_db
from app.models.spatial import SpatialFeature
from app.schemas.gis import SpatialFeatureResponse, GISSummaryResponse
from app.schemas.environment import PaginatedResponse

logger = logging.getLogger("floodx.api.gis")
router = APIRouter(prefix="/gis", tags=["GIS & Spatial Infrastructure"])


@router.get("/summary", response_model=GISSummaryResponse)
def get_gis_summary(db: Session = Depends(get_db)):
    """Returns spatial layer feature counts and bounding extent for the Pune study area."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    counts = dict(
        db.execute(
            select(SpatialFeature.feature_type, func.count(SpatialFeature.id)).group_by(
                SpatialFeature.feature_type
            )
        ).all()
    )
    total = sum(counts.values())

    return GISSummaryResponse(
        total_features=total,
        layer_counts=counts,
        study_domain="Pune / Mula-Mutha River Basin (EPSG:4326)",
    )


@router.get("/features", response_model=PaginatedResponse)
def get_spatial_features(
    feature_type: Optional[str] = Query(None, description="e.g. WATERWAY, BRIDGE, HEALTHCARE, EDUCATION, COMMUNITY_CIVIC, EVACUATION_ROAD"),
    name: Optional[str] = Query(None, description="Filter by facility or road name"),
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: Session = Depends(get_db),
):
    """Retrieves spatial infrastructure features with GeoJSON geometries."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    stmt = select(SpatialFeature)
    count_stmt = select(func.count(SpatialFeature.id))

    if feature_type:
        stmt = stmt.where(SpatialFeature.feature_type == feature_type.upper())
        count_stmt = count_stmt.where(SpatialFeature.feature_type == feature_type.upper())
    if name:
        stmt = stmt.where(SpatialFeature.name.ilike(f"%{name}%"))
        count_stmt = count_stmt.where(SpatialFeature.name.ilike(f"%{name}%"))

    total = db.execute(count_stmt).scalar() or 0
    records = db.execute(stmt.offset(offset).limit(limit)).scalars().all()

    items = []
    for r in records:
        geom_dict = None
        try:
            if r.geom is not None:
                sh = to_shape(r.geom)
                geom_dict = sh.__geo_interface__
        except Exception as e:
            logger.debug("Failed to serialize geometry for id %d: %s", r.id, e)

        items.append({
            "id": r.id,
            "source_id": r.source_id,
            "feature_type": r.feature_type,
            "osm_id": r.osm_id,
            "name": r.name,
            "properties_json": r.properties_json,
            "geojson": geom_dict,
            "created_at": r.created_at,
        })

    return PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )

