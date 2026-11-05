"""Hydrological feature engineering catalog model for FLOOD-X."""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.models.base import Base, utc_now


class FeatureDataset(Base):
    """Tracks generated feature datasets, schemas, temporal bounds, and provenance manifests."""
    __tablename__ = "feature_datasets"

    id = Column(Integer, primary_key=True, index=True)
    feature_set_name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    # Categories: RAINFALL, WEATHER, TERRAIN, GEOSPATIAL, INTEGRATED
    file_path_csv = Column(String(255), nullable=True)
    file_path_parquet = Column(String(255), nullable=True)
    total_records = Column(Integer, nullable=False, default=0)
    columns_json = Column(JSON, nullable=True)
    temporal_range = Column(String(100), nullable=True)
    spatial_domain = Column(String(150), nullable=True)
    quality_notes = Column(Text, nullable=True)
    provenance_manifest = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<FeatureDataset(name='{self.feature_set_name}', cat='{self.category}', records={self.total_records})>"

