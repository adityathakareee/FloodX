"""API endpoints for data ingestion monitoring, source registration, and pipeline triggering."""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.data_source import DataSource
from app.models.ingestion import DataIngestionLog
from app.schemas.ingestion import (
    DataSourceResponse,
    DataIngestionLogResponse,
    IngestionOverviewResponse,
    IngestionRunRequest,
    IngestionRunResponse,
)
from app.services.ingestion.orchestrator import IngestionOrchestrator

logger = logging.getLogger("floodx.api.ingestion")
router = APIRouter(prefix="/ingestion", tags=["Data Ingestion & Pipelines"])
orchestrator = IngestionOrchestrator()


@router.get("/overview", response_model=IngestionOverviewResponse)
def get_ingestion_overview(db: Session = Depends(get_db)):
    """Returns real-time statistics and summary of all ingested environmental and GIS data."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")
    return orchestrator.get_overview(db)


@router.get("/sources", response_model=List[DataSourceResponse])
def get_data_sources(
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    """Lists registered environmental and spatial data sources."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    stmt = select(DataSource)
    if source_type:
        stmt = stmt.where(DataSource.source_type == source_type.upper())
    if is_active is not None:
        stmt = stmt.where(DataSource.is_active == is_active)

    stmt = stmt.order_by(DataSource.id)
    return db.execute(stmt).scalars().all()


@router.get("/logs", response_model=List[DataIngestionLogResponse])
def get_ingestion_logs(
    source_id: Optional[int] = Query(None, description="Filter by data source ID"),
    status: Optional[str] = Query(None, description="Filter by execution status"),
    limit: int = Query(20, ge=1, le=100, description="Max logs to return"),
    db: Session = Depends(get_db),
):
    """Retrieves transactional execution logs of data ingestion jobs."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    stmt = select(DataIngestionLog)
    if source_id:
        stmt = stmt.where(DataIngestionLog.source_id == source_id)
    if status:
        stmt = stmt.where(DataIngestionLog.status == status.upper())

    stmt = stmt.order_by(desc(DataIngestionLog.started_at)).limit(limit)
    return db.execute(stmt).scalars().all()


@router.post("/run", response_model=IngestionRunResponse)
def trigger_ingestion(
    request: IngestionRunRequest,
    db: Session = Depends(get_db),
):
    """Triggers ingestion for a specific data source or executes the full pipeline."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    source_key = request.source.lower().strip()
    try:
        if source_key == "all":
            result = orchestrator.run_all(db, fast_mode=request.fast_mode)
            return IngestionRunResponse(
                status="COMPLETED",
                message="Executed full multi-source ingestion pipeline",
                details=result,
            )
        else:
            result = orchestrator.run_source(db, source_key)
            return IngestionRunResponse(
                status="COMPLETED",
                message=f"Executed ingestion for source '{request.source}'",
                details=result,
            )
    except Exception as exc:
        logger.exception("Failed to trigger ingestion for %s: %s", request.source, exc)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(exc)}")

