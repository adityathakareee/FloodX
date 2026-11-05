"""Pydantic schemas for hydrological feature engineering API endpoints."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class FeatureDatasetResponse(BaseModel):
    """Cataloged feature dataset response schema."""
    id: int
    feature_set_name: str
    category: str
    file_path_csv: Optional[str] = None
    file_path_parquet: Optional[str] = None
    total_records: int
    columns_json: Optional[List[str]] = None
    temporal_range: Optional[str] = None
    spatial_domain: Optional[str] = None
    quality_notes: Optional[str] = None
    provenance_manifest: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureSummaryResponse(BaseModel):
    """High-level summary of all engineered hydrological feature domains."""
    total_feature_sets: int
    categories: Dict[str, int]
    total_records: int
    feature_sets: List[FeatureDatasetResponse]


class FeatureGenerationResponse(BaseModel):
    """Result from triggering the feature generation pipeline."""
    status: str
    duration_seconds: float
    total_datasets: int
    manifest_file: Optional[str] = None
    datasets: List[Dict[str, Any]]

