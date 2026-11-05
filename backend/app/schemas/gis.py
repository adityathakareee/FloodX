"""Pydantic schemas for GIS vector entities and spatial queries."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class SpatialFeatureResponse(BaseModel):
    id: int
    source_id: int
    feature_type: str
    osm_id: Optional[str] = None
    name: Optional[str] = None
    properties_json: Optional[Dict[str, Any]] = None
    geojson: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GISSummaryResponse(BaseModel):
    total_features: int
    layer_counts: Dict[str, int]
    study_domain: str

