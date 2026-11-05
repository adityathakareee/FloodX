"""Health check endpoints for FLOOD-X."""

import time
from fastapi import APIRouter, status
from app.core.config import settings
from app.core.database import check_db_connection
from app.schemas.health import HealthResponse, DatabaseHealth

router = APIRouter()

# Global start timestamp to calculate process uptime
APP_START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health & Database Verification",
    description=(
        "Returns the operational health of the FLOOD-X API and its PostGIS database connection. "
        "Distinguishes healthy, degraded, and unhealthy states. If PostgreSQL is offline, "
        "the endpoint returns HTTP 200 with status='degraded' to allow graceful service discovery."
    ),
)
def get_health() -> HealthResponse:
    """Evaluates API and Database readiness."""
    is_connected, latency_ms, db_error = check_db_connection()
    uptime_seconds = round(time.time() - APP_START_TIME, 2)

    db_health = DatabaseHealth(
        status="connected" if is_connected else "disconnected",
        database_engine="PostgreSQL 16 / PostGIS 3.4",
        latency_ms=latency_ms,
        error=db_error,
    )

    overall_status = "healthy" if is_connected else "degraded"

    return HealthResponse(
        status=overall_status,
        app_name=settings.PROJECT_NAME,
        app_version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=uptime_seconds,
        database=db_health,
    )

