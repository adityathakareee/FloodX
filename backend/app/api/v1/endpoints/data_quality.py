"""API endpoints for Data Quality management, audit summaries, and limitation tracking."""
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.ingestion import DataQualityIssue
from app.schemas.data_quality import (
    DataQualityIssueResponse,
    DataQualitySummaryResponse,
)

logger = logging.getLogger("floodx.api.data_quality")
router = APIRouter(prefix="/data-quality", tags=["Data Quality & Integrity"])


@router.get("/summary", response_model=DataQualitySummaryResponse)
def get_data_quality_summary(db: Session = Depends(get_db)):
    """Returns aggregated data quality metrics, breakdown by severity, and active issue list."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    by_severity = dict(
        db.execute(
            select(DataQualityIssue.severity, func.count(DataQualityIssue.id)).group_by(
                DataQualityIssue.severity
            )
        ).all()
    )

    issues = (
        db.execute(select(DataQualityIssue).order_by(desc(DataQualityIssue.detected_at)))
        .scalars()
        .all()
    )

    return DataQualitySummaryResponse(
        total_issues=len(issues),
        by_severity=by_severity,
        issues=[DataQualityIssueResponse.model_validate(q) for q in issues],
    )


@router.get("/issues", response_model=List[DataQualityIssueResponse])
def get_data_quality_issues(
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL, INFO"),
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    db: Session = Depends(get_db),
):
    """Retrieves all documented data quality issues and geographic caveats."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    stmt = select(DataQualityIssue)
    if severity:
        stmt = stmt.where(DataQualityIssue.severity == severity.upper())
    if source_id:
        stmt = stmt.where(DataQualityIssue.source_id == source_id)

    stmt = stmt.order_by(desc(DataQualityIssue.detected_at))
    return db.execute(stmt).scalars().all()

