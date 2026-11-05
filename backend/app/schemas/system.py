"""Pydantic schemas for system information and module readiness endpoints."""

from datetime import datetime, timezone
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class ModuleReadiness(BaseModel):
    """Specification of an architectural subsystem and its readiness status."""
    id: str = Field(..., description="Unique module identifier")
    name: str = Field(..., description="Human-readable module name")
    description: str = Field(..., description="Function of the module")
    target_phase: int = Field(..., description="Project phase when this module is implemented")
    phase_title: str = Field(..., description="Name of the target phase")
    status: Literal["operational", "foundation_ready", "planned", "not_configured"] = Field(
        ...,
        description="Current operational status of the module"
    )
    is_operational: bool = Field(
        default=False,
        description="Whether the module is actively accepting live workloads"
    )
    implementation_notes: Optional[str] = Field(
        default=None,
        description="Architectural or implementation details"
    )


class PilotRegion(BaseModel):
    """Target hydrological pilot geography."""
    name: str = "Pune / Mula-Mutha River Basin"
    state: str = "Maharashtra, India"
    latitude: float = 18.5204
    longitude: float = 73.8567
    rivers: List[str] = ["Mula River", "Mutha River", "Pavana River", "Indrayani River"]
    target_dams: List[str] = ["Khadakwasla Dam", "Mulshi Dam", "Panshet Dam", "Varasgaon Dam", "Pawana Dam"]
    vulnerability_focus: str = "Urban flash-floods, downstream low-lying settlements, bridge chokepoints"


class SystemInfoResponse(BaseModel):
    """System metadata and modular readiness status."""
    project_name: str = Field(..., description="Official project title")
    project_tagline: str = Field(..., description="Official motto")
    project_version: str = Field(..., description="Semantic project version")
    api_version: str = Field(..., description="REST API version")
    environment: str = Field(..., description="Runtime environment")
    current_phase: str = Field(..., description="Currently active development phase")
    pilot_region: PilotRegion = Field(default_factory=PilotRegion)
    system_status: Literal["operational", "degraded", "maintenance"] = Field(
        ...,
        description="Overall platform operational status"
    )
    modules: List[ModuleReadiness] = Field(
        ...,
        description="Complete catalog of FLOOD-X subsystems and their implementation state"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Current UTC timestamp"
    )
