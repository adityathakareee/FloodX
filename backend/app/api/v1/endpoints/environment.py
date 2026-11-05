"""API endpoints for environmental observation queries (Rainfall, Weather, River Levels)."""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.observation import (
    RainfallObservation,
    WeatherObservation,
    RiverLevelObservation,
)
from app.schemas.environment import (
    RainfallObservationResponse,
    WeatherObservationResponse,
    RiverLevelObservationResponse,
    PaginatedResponse,
)

logger = logging.getLogger("floodx.api.environment")
router = APIRouter(prefix="/environment", tags=["Environmental Intelligence"])


@router.get("/rainfall", response_model=PaginatedResponse)
def get_rainfall_observations(
    source_id: Optional[int] = Query(None, description="Filter by data source ID"),
    station_name: Optional[str] = Query(None, description="Filter by station name"),
    measurement_type: Optional[str] = Query(None, description="e.g. DAILY_ACCUMULATION, 5MIN_CUMULATIVE, INCREMENTAL, HOURLY_ACCUMULATION"),
    quality_flag: Optional[str] = Query(None, description="e.g. VALID, DERIVED, SUSPECT"),
    start_time: Optional[datetime] = Query(None, description="ISO format start datetime"),
    end_time: Optional[datetime] = Query(None, description="ISO format end datetime"),
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: Session = Depends(get_db),
):
    """Retrieves paginated rainfall observations with filtering."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    stmt = select(RainfallObservation)
    count_stmt = select(func.count(RainfallObservation.id))

    if source_id:
        stmt = stmt.where(RainfallObservation.source_id == source_id)
        count_stmt = count_stmt.where(RainfallObservation.source_id == source_id)
    if station_name:
        stmt = stmt.where(RainfallObservation.station_name.ilike(f"%{station_name}%"))
        count_stmt = count_stmt.where(RainfallObservation.station_name.ilike(f"%{station_name}%"))
    if measurement_type:
        stmt = stmt.where(RainfallObservation.measurement_type == measurement_type.upper())
        count_stmt = count_stmt.where(RainfallObservation.measurement_type == measurement_type.upper())
    if quality_flag:
        stmt = stmt.where(RainfallObservation.quality_flag == quality_flag.upper())
        count_stmt = count_stmt.where(RainfallObservation.quality_flag == quality_flag.upper())
    if start_time:
        stmt = stmt.where(RainfallObservation.observation_time >= start_time)
        count_stmt = count_stmt.where(RainfallObservation.observation_time >= start_time)
    if end_time:
        stmt = stmt.where(RainfallObservation.observation_time <= end_time)
        count_stmt = count_stmt.where(RainfallObservation.observation_time <= end_time)

    total = db.execute(count_stmt).scalar() or 0
    records = db.execute(stmt.order_by(desc(RainfallObservation.observation_time)).offset(offset).limit(limit)).scalars().all()

    return PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[RainfallObservationResponse.model_validate(r) for r in records],
    )


@router.get("/rainfall/summary")
def get_rainfall_summary(db: Session = Depends(get_db)):
    """Returns key rainfall statistics for the Pune pilot basin."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    max_cwprs = db.execute(
        select(func.max(RainfallObservation.rainfall_value))
        .where(RainfallObservation.station_name.ilike("%CWPRS%"))
    ).scalar() or 0.0

    max_chirps = db.execute(
        select(func.max(RainfallObservation.rainfall_value))
        .where(RainfallObservation.measurement_type == "DAILY_ACCUMULATION")
    ).scalar() or 0.0

    total_records = db.execute(select(func.count(RainfallObservation.id))).scalar() or 0

    return {
        "total_records": total_records,
        "cwprs_24h_cumulative_peak_mm": max_cwprs,
        "cwprs_peak_event": "2024-07-25 08:25 IST (Cloudburst event resetting at 08:35 IST)",
        "chirps_basin_daily_peak_mm": max_chirps,
        "stations": ["Khadakwasla (CWPRS)", "CHIRPS_V3_PUNE_BASIN_AGGREGATE"],
    }


@router.get("/weather", response_model=PaginatedResponse)
def get_weather_observations(
    data_category: Optional[str] = Query(None, description="OBSERVED or FORECAST"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: Session = Depends(get_db),
):
    """Retrieves paginated surface and soil weather observations."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    stmt = select(WeatherObservation)
    count_stmt = select(func.count(WeatherObservation.id))

    if data_category:
        stmt = stmt.where(WeatherObservation.data_category == data_category.upper())
        count_stmt = count_stmt.where(WeatherObservation.data_category == data_category.upper())
    if start_time:
        stmt = stmt.where(WeatherObservation.observation_time >= start_time)
        count_stmt = count_stmt.where(WeatherObservation.observation_time >= start_time)
    if end_time:
        stmt = stmt.where(WeatherObservation.observation_time <= end_time)
        count_stmt = count_stmt.where(WeatherObservation.observation_time <= end_time)

    total = db.execute(count_stmt).scalar() or 0
    records = db.execute(stmt.order_by(desc(WeatherObservation.observation_time)).offset(offset).limit(limit)).scalars().all()

    return PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[WeatherObservationResponse.model_validate(r) for r in records],
    )


@router.get("/river-levels", response_model=PaginatedResponse)
def get_river_level_observations(
    station_name: Optional[str] = Query(None, description="Filter by station"),
    geographic_relevance: Optional[str] = Query(None, description="Filter by relevance (e.g. REGIONAL_REFERENCE_ONLY)"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(50, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset"),
    db: Session = Depends(get_db),
):
    """Retrieves river stage telemetry observations."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    stmt = select(RiverLevelObservation)
    count_stmt = select(func.count(RiverLevelObservation.id))

    if station_name:
        stmt = stmt.where(RiverLevelObservation.station_name.ilike(f"%{station_name}%"))
        count_stmt = count_stmt.where(RiverLevelObservation.station_name.ilike(f"%{station_name}%"))
    if geographic_relevance:
        stmt = stmt.where(RiverLevelObservation.geographic_relevance == geographic_relevance.upper())
        count_stmt = count_stmt.where(RiverLevelObservation.geographic_relevance == geographic_relevance.upper())
    if start_time:
        stmt = stmt.where(RiverLevelObservation.observation_time >= start_time)
        count_stmt = count_stmt.where(RiverLevelObservation.observation_time >= start_time)
    if end_time:
        stmt = stmt.where(RiverLevelObservation.observation_time <= end_time)
        count_stmt = count_stmt.where(RiverLevelObservation.observation_time <= end_time)

    total = db.execute(count_stmt).scalar() or 0
    records = db.execute(stmt.order_by(desc(RiverLevelObservation.observation_time)).offset(offset).limit(limit)).scalars().all()

    return PaginatedResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[RiverLevelObservationResponse.model_validate(r) for r in records],
    )

