"""Spatial feature model for PostGIS GIS vector entities in FLOOD-X."""
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import Base, utc_now


class SpatialFeature(Base):
    """Stores OpenStreetMap and municipal spatial entities (rivers, bridges, facilities, roads)."""
    __tablename__ = "spatial_features"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_type = Column(String(50), nullable=False, index=True)
    # Types: WATERWAY, BRIDGE, HEALTHCARE, EDUCATION, COMMUNITY_CIVIC, EVACUATION_ROAD
    osm_id = Column(String(50), nullable=True, index=True)
    name = Column(String(255), nullable=True)
    properties_json = Column(JSON, nullable=True)
    geom = Column(Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    source = relationship("DataSource", back_populates="spatial_features")

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "feature_type",
            "osm_id",
            name="uq_spatial_feature_record",
        ),
        Index("ix_spatial_feature_type_name", "feature_type", "name"),
    )

    def __repr__(self) -> str:
        return f"<SpatialFeature(id={self.id}, type='{self.feature_type}', name='{self.name}', osm_id='{self.osm_id}')>"

