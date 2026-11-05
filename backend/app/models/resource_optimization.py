"""SQLAlchemy models for FLOOD-X Phase 4 Emergency Resource Optimization & Decision Intelligence."""

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
from app.models.base import Base, utc_now


class EmergencyResource(Base):
    """Stores municipal and relief resources (ambulances, rescue teams, relief supplies, infrastructure)."""
    __tablename__ = "emergency_resources"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(64), unique=True, nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)
    # Categories: EMERGENCY_VEHICLE, HUMAN_RESOURCE, RELIEF_RESOURCE, INFRASTRUCTURE
    resource_type = Column(String(64), nullable=False, index=True)
    # Types: AMBULANCE_BLS, AMBULANCE_ALS, RESCUE_BOAT, FIRE_ENGINE, RESCUE_TEAM_FLOOD,
    #        MEDICAL_TEAM, FOOD_PACKETS, DRINKING_WATER, MEDICAL_KITS, BLANKETS, EMERGENCY_EQUIPMENT
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_quantity = Column(Integer, nullable=False, default=1)
    available_quantity = Column(Integer, nullable=False, default=1)
    allocated_quantity = Column(Integer, nullable=False, default=0)
    operational_status = Column(String(32), nullable=False, default="AVAILABLE", index=True)
    # Statuses: AVAILABLE, ALLOCATED, DEPLOYED, UNAVAILABLE, UNDER_MAINTENANCE, UNKNOWN_STATUS
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    base_address = Column(String(255), nullable=True)
    assigned_location_name = Column(String(255), nullable=True)
    responsible_authority = Column(String(128), nullable=False, default="PMC Disaster Management Cell")
    capacity_specs = Column(JSON, nullable=True)
    # e.g., {"patient_capacity": 2, "crew_size": 4, "payload_kg": 1000}
    is_simulated = Column(Boolean, nullable=False, default=True)
    data_source = Column(String(128), nullable=False, default="MUNICIPAL_REGISTER_SIMULATED")
    verification_status = Column(String(64), nullable=False, default="SIMULATED_DEMO")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    history = relationship("ResourceInventoryHistory", back_populates="resource", cascade="all, delete-orphan")
    allocations = relationship("ResourceAllocation", back_populates="resource", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<EmergencyResource(id={self.id}, code='{self.resource_id}', name='{self.name}', status='{self.operational_status}')>"


class ResourceInventoryHistory(Base):
    """Tracks audit trail of resource quantity, availability, and operational status transitions."""
    __tablename__ = "resource_inventory_history"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("emergency_resources.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    # Events: INITIAL_REGISTRATION, QUANTITY_UPDATE, STATUS_CHANGE, ALLOCATION, RELEASE, DEPLOYMENT
    previous_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=True)
    previous_available = Column(Integer, nullable=True)
    new_available = Column(Integer, nullable=True)
    actor = Column(String(128), nullable=False, default="Disaster Management Administrator")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    resource = relationship("EmergencyResource", back_populates="history")


class EmergencyDemandAssessment(Base):
    """Maintains estimated resource requirements and priorities for geographic sectors in Pune Basin."""
    __tablename__ = "emergency_demand_assessments"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(String(64), unique=True, nullable=False, index=True)
    sector_id = Column(String(64), nullable=False, index=True)
    sector_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    priority_level = Column(String(32), nullable=False, default="MODERATE_PRIORITY", index=True)
    # Priorities: CRITICAL_PRIORITY, HIGH_PRIORITY, MODERATE_PRIORITY, LOW_PRIORITY, INSUFFICIENT_DATA
    priority_score = Column(Float, nullable=False, default=50.0)
    risk_score = Column(Float, nullable=False, default=50.0)
    demand_score = Column(Float, nullable=False, default=50.0)
    accessibility_score = Column(Float, nullable=False, default=50.0)
    infrastructure_score = Column(Float, nullable=False, default=50.0)
    evidence_type = Column(String(64), nullable=False, default="TERRAIN_SUSCEPTIBILITY")
    # Types: OBSERVED_INCIDENT, FORECAST_DERIVED, TERRAIN_SUSCEPTIBILITY, SIMULATED_SCENARIO
    required_ambulances = Column(Integer, nullable=False, default=0)
    required_rescue_teams = Column(Integer, nullable=False, default=0)
    required_food_packets = Column(Integer, nullable=False, default=0)
    required_water_liters = Column(Integer, nullable=False, default=0)
    required_medical_kits = Column(Integer, nullable=False, default=0)
    required_blankets = Column(Integer, nullable=False, default=0)
    urgency_reason = Column(Text, nullable=True)
    missing_data_notes = Column(Text, nullable=True)
    is_simulated = Column(Boolean, nullable=False, default=True)
    assessed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("ix_demand_sector_priority", "sector_id", "priority_level"),
    )


class OptimizationRun(Base):
    """Tracks Google OR-Tools mathematical optimization executions and outcomes."""
    __tablename__ = "optimization_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    solver_type = Column(String(64), nullable=False, default="ORTOOLS_MIP_SCIP")
    status = Column(String(32), nullable=False, default="OPTIMAL", index=True)
    # Statuses: OPTIMAL, FEASIBLE, INFEASIBLE, TIME_LIMIT_REACHED, NO_RESOURCES_AVAILABLE, INSUFFICIENT_DATA
    objective_value = Column(Float, nullable=True)
    total_response_time_minutes = Column(Float, nullable=True)
    total_assigned_resources = Column(Integer, nullable=False, default=0)
    total_unmet_demand = Column(Integer, nullable=False, default=0)
    demand_coverage_pct = Column(Float, nullable=False, default=0.0)
    execution_duration_ms = Column(Float, nullable=True)
    parameters_json = Column(JSON, nullable=True)
    summary_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    allocations = relationship("ResourceAllocation", back_populates="optimization_run", cascade="all, delete-orphan")


class ResourceAllocation(Base):
    """Stores resource dispatch proposals and approved deployments with Phase 3 graph routing paths."""
    __tablename__ = "resource_allocations"

    id = Column(Integer, primary_key=True, index=True)
    allocation_id = Column(String(64), unique=True, nullable=False, index=True)
    optimization_run_id = Column(Integer, ForeignKey("optimization_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    resource_id = Column(Integer, ForeignKey("emergency_resources.id", ondelete="CASCADE"), nullable=False, index=True)
    demand_sector_id = Column(String(64), nullable=False, index=True)
    assigned_quantity = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="PROPOSED", index=True)
    # Statuses: PROPOSED, APPROVED, DEPLOYED, RELEASED, CANCELLED
    estimated_travel_time_sec = Column(Float, nullable=True)
    estimated_distance_m = Column(Float, nullable=True)
    route_edge_ids = Column(JSON, nullable=True)
    route_geojson = Column(JSON, nullable=True)
    route_uncertainty_note = Column(Text, nullable=True)
    allocated_by = Column(String(128), nullable=False, default="Disaster Management Administrator")
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    resource = relationship("EmergencyResource", back_populates="allocations")
    optimization_run = relationship("OptimizationRun", back_populates="allocations")


class DisasterScenario(Base):
    """Maintains user-defined and drill scenario configurations for what-if disaster simulation."""
    __tablename__ = "disaster_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rainfall_multiplier = Column(Float, nullable=False, default=1.0)
    dam_discharge_cfs = Column(Float, nullable=False, default=0.0)
    simulated_closed_edge_ids = Column(JSON, nullable=True)
    resource_availability_factor = Column(Float, nullable=False, default=1.0)
    demand_surge_factor = Column(Float, nullable=False, default=1.0)
    created_by = Column(String(128), nullable=False, default="Disaster Management Administrator")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

