"""Pydantic schemas for environmental observations (rainfall, weather, river levels)."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class RainfallObservationResponse(BaseModel):
    id: int
    source_id: int
    station_name: str
    latitude: float
    longitude: float
    observation_time: datetime
    rainfall_value: float
    rainfall_unit: str
    measurement_type: str
    quality_flag: str
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class WeatherObservationResponse(BaseModel):
    id: int
    source_id: int
    location_name: str
    latitude: float
    longitude: float
    observation_time: datetime
    data_category: str
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    soil_moisture: Optional[float] = None
    quality_flag: str
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class RiverLevelObservationResponse(BaseModel):
    id: int
    source_id: int
    station_name: str
    river_name: str
    station_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    observation_time: datetime
    water_level: float
    level_unit: str
    vertical_datum: str
    geographic_relevance: str
    quality_flag: str
    metadata_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[Any]

