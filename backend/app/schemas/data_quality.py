"""Pydantic schemas for data quality issues, limitations, and semantic audit tracking."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class DataQualityIssueResponse(BaseModel):
    id: int
    source_id: int
    issue_type: str
    severity: str
    description: str
    affected_record_count: int
    detected_at: datetime
    resolution_status: str
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class DataQualitySummaryResponse(BaseModel):
    total_issues: int
    by_severity: Dict[str, int]
    issues: List[DataQualityIssueResponse]

