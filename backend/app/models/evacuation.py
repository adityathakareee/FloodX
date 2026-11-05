"""SQLAlchemy models for FLOOD-X Phase 3.2 Evacuation Intelligence & Shelter Management."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.models.base import Base, utc_now


class RoadClosure(Base):
    """Stores verified municipal road closures, police barricades, and simulated blockages."""
    __tablename__ = "road_closures"

    id = Column(Integer, primary_key=True, index=True)
    edge_id = Column(String(50), nullable=False, index=True)
    source_feature_id = Column(Integer, nullable=True)
    road_name = Column(String(255), nullable=False)
    closure_status = Column(String(50), nullable=False, default="CONFIRMED_BLOCKED")
    # Statuses: CONFIRMED_BLOCKED, SIMULATED_BLOCKAGE, PARTIALLY_BLOCKED, CLEARED
    reason = Column(Text, nullable=False)
    verification_source = Column(String(255), nullable=False)
    reporting_authority = Column(String(100), nullable=False, default="PMC Disaster Management Cell")
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    effective_from = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    audit_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_road_closures_edge_active", "edge_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<RoadClosure(id={self.id}, edge_id='{self.edge_id}', road='{self.road_name}', active={self.is_active})>"


class Shelter(Base):
    """Stores emergency evacuation shelters and candidate municipal relief facilities."""
    __tablename__ = "shelters"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("spatial_features.id", ondelete="SET NULL"), nullable=True, index=True)
    osm_id = Column(String(50), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    facility_type = Column(String(50), nullable=False, default="COMMUNITY_CENTRE")
    # Types: COMMUNITY_CENTRE, SCHOOL, COLLEGE, SPORTS_COMPLEX, HOSPITAL, CIVIC_HALL
    verification_status = Column(String(50), nullable=False, default="CANDIDATE_SHELTER", index=True)
    # Statuses: VERIFIED_SHELTER, CANDIDATE_SHELTER, UNVERIFIED_FACILITY, INACTIVE_SHELTER
    address = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=True)
    
    # Capacity management (None = unknown / not verified, strictly never invented)
    total_capacity = Column(Integer, nullable=True)
    current_occupancy = Column(Integer, nullable=True, default=None)
    available_capacity = Column(Integer, nullable=True)
    
    # Facility features
    has_medical_support = Column(Boolean, nullable=False, default=False)
    is_wheelchair_accessible = Column(Boolean, nullable=False, default=False)
    has_generator_power = Column(Boolean, nullable=False, default=False)
    emergency_contact = Column(String(100), nullable=True)
    
    # Verification provenance & evidence documentation
    source = Column(String(100), nullable=False, default="OSM")
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    evidence_document = Column(String(255), nullable=True)
    evidence_date = Column(String(50), nullable=True)
    properties_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    facility = relationship("SpatialFeature", foreign_keys=[facility_id])
    history = relationship("ShelterUpdateHistory", back_populates="shelter", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Shelter(id={self.id}, name='{self.name}', status='{self.verification_status}')>"


class ShelterUpdateHistory(Base):
    """Audit trail of capacity, occupancy, and status changes for registered shelters."""
    __tablename__ = "shelter_update_history"

    id = Column(Integer, primary_key=True, index=True)
    shelter_id = Column(Integer, ForeignKey("shelters.id", ondelete="CASCADE"), nullable=False, index=True)
    update_type = Column(String(50), nullable=False)
    # Types: CAPACITY_UPDATE, OCCUPANCY_UPDATE, STATUS_CHANGE, VERIFICATION
    previous_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=False)
    updated_by = Column(String(100), nullable=False, default="System Administrator")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    shelter = relationship("Shelter", back_populates="history")


class EvacuationAuditLog(Base):
    """Administrative audit trail for all evacuation decisions, closures, and route assessments."""
    __tablename__ = "evacuation_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    # Types: ROAD_CLOSURE_CREATED, ROAD_CLOSURE_EXPIRED, SHELTER_VERIFIED, CAPACITY_UPDATED, ROUTE_EVALUATION
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    actor = Column(String(100), nullable=False, default="Authority Operator")
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<EvacuationAuditLog(id={self.id}, event='{self.event_type}', entity='{self.entity_id}')>"

