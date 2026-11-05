"""Pydantic schemas for data sources, ingestion logs, and orchestrator management."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class DataSourceBase(BaseModel):
    source_name: str
    source_type: str
    provider: str
    description: Optional[str] = None
    data_format: str
    units: Optional[str] = None
    temporal_resolution: Optional[str] = None
    spatial_resolution: Optional[str] = None
    is_active: bool = True
    metadata_json: Optional[Dict[str, Any]] = None


class DataSourceResponse(DataSourceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataIngestionLogResponse(BaseModel):
    id: int
    source_id: int
    ingestion_type: str
    file_name: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    records_read: int
    records_inserted: int
    records_skipped: int
    records_failed: int
    error_message: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class IngestionOverviewResponse(BaseModel):
    counts: Dict[str, int]
    breakdowns: Dict[str, Dict[str, int]]
    recent_logs: List[Dict[str, Any]]
    quality_issues: List[Dict[str, Any]]


class IngestionRunRequest(BaseModel):
    source: str = "all"
    fast_mode: bool = False


class IngestionRunResponse(BaseModel):
    status: str
    message: str
    details: Dict[str, Any]

