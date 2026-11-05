"""Data source catalog model for FLOOD-X."""
from sqlalchemy import Column, String, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class DataSource(BaseModel):
    """Catalog of all environmental, geospatial, and telemetry data sources."""
    __tablename__ = "data_sources"

    source_name = Column(String(100), unique=True, nullable=False, index=True)
    source_type = Column(String(100), nullable=False, index=True)
    provider = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    data_format = Column(String(50), nullable=False)
    units = Column(String(100), nullable=True)
    temporal_resolution = Column(String(50), nullable=True)
    spatial_resolution = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    rainfall_observations = relationship("RainfallObservation", back_populates="source", cascade="all, delete-orphan")
    weather_observations = relationship("WeatherObservation", back_populates="source", cascade="all, delete-orphan")
    river_level_observations = relationship("RiverLevelObservation", back_populates="source", cascade="all, delete-orphan")
    spatial_features = relationship("SpatialFeature", back_populates="source", cascade="all, delete-orphan")
    ingestion_logs = relationship("DataIngestionLog", back_populates="source")
    quality_issues = relationship("DataQualityIssue", back_populates="source")

    def __repr__(self) -> str:
        return f"<DataSource(id={self.id}, name='{self.source_name}', type='{self.source_type}')>"

