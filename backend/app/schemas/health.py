"""Pydantic schemas for system health check endpoints."""

from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    """Database connectivity details."""
    status: Literal["connected", "disconnected", "error"] = Field(
        ..., description="Database connectivity status"
    )
    database_engine: str = Field(
        default="PostgreSQL 16 / PostGIS 3.4",
        description="Target database engine"
    )
    latency_ms: Optional[float] = Field(
        default=None,
        description="Round-trip ping query latency in milliseconds"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error details if database is unreachable"
    )


class HealthResponse(BaseModel):
    """Overall system health evaluation response."""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ...,
        description="Overall system health status. 'healthy' when all core services are online, 'degraded' when database is unreachable but API is responsive."
    )
    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Application semantic version")
    environment: str = Field(..., description="Deployment environment")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check"
    )
    uptime_seconds: float = Field(
        ...,
        description="Application process uptime in seconds"
    )
    database: DatabaseHealth = Field(
        ...,
        description="PostgreSQL/PostGIS connectivity breakdown"
    )
