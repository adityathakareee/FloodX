"""System information and module readiness endpoints for FLOOD-X."""

from fastapi import APIRouter, status
from app.core.config import settings
from app.core.database import check_db_connection
from app.schemas.system import (
    SystemInfoResponse,
    PilotRegion,
    ModuleReadiness,
)

router = APIRouter()

# Canonical catalog of FLOOD-X platform modules across all six phases
MODULE_CATALOG: list[ModuleReadiness] = [
    ModuleReadiness(
        id="mod-core-01",
        name="Authority Web Dashboard",
        description="GIS-enabled situational command dashboard for disaster response authorities (PMC/PCMC)",
        target_phase=0,
        phase_title="Phase 0: Project Foundation & System Architecture",
        status="foundation_ready",
        is_operational=True,
        implementation_notes="Phase 0 architecture, routing, shell layout, and health monitoring active.",
    ),
    ModuleReadiness(
        id="mod-core-02",
        name="Citizen Android Mobile App",
        description="Public flood alerts, SOS reporting, and safe evacuation route navigation client",
        target_phase=0,
        phase_title="Phase 0: Project Foundation & System Architecture",
        status="foundation_ready",
        is_operational=True,
        implementation_notes="Phase 0 React Native / Expo shell and API communication layer established.",
    ),
    ModuleReadiness(
        id="mod-data-01",
        name="Multi-Source Environmental Data Ingestion",
        description="Automated ingestion from IMD, CWC river sensors, Khadakwasla dam discharge, and Open-Meteo",
        target_phase=1,
        phase_title="Phase 1: Real-Time Data Integration & GIS Intelligence",
        status="planned",
        is_operational=False,
        implementation_notes="Scheduled for Phase 1. API adapters and telemetry validation pipelines planned.",
    ),
    ModuleReadiness(
        id="mod-gis-01",
        name="GIS Flood Visualization & Spatial Engine",
        description="PostGIS spatial layer indexing, Pune DEM processing, and interactive catchment mapping",
        target_phase=1,
        phase_title="Phase 1: Real-Time Data Integration & GIS Intelligence",
        status="planned",
        is_operational=False,
        implementation_notes="Scheduled for Phase 1. MapLibre/Leaflet vector tile rendering pending.",
    ),
    ModuleReadiness(
        id="mod-ai-01",
        name="AI/ML Flood-Risk Prediction Engine",
        description="Hydrological runoff modeling and machine learning flood risk regression/classification",
        target_phase=2,
        phase_title="Phase 2: AI/ML Flood Prediction & Vulnerability Analysis",
        status="planned",
        is_operational=False,
        implementation_notes="Scheduled for Phase 2. Model training and validation pipelines will be created.",
    ),
    ModuleReadiness(
        id="mod-vuln-01",
        name="Vulnerability & Population Exposure Analysis",
        description="Socio-economic vulnerability indexing and demographic exposure mapping along riverbanks",
        target_phase=2,
        phase_title="Phase 2: AI/ML Flood Prediction & Vulnerability Analysis",
        status="planned",
        is_operational=False,
        implementation_notes="Scheduled for Phase 2. Pune ward census overlay and critical infrastructure risk scoring.",
    ),
    ModuleReadiness(
        id="mod-impact-01",
        name="Time-to-Impact Estimation",
        description="Dynamic wave propagation speed and estimated flood inundation arrival times at downstream bridges",
        target_phase=2,
        phase_title="Phase 2: AI/ML Flood Prediction & Vulnerability Analysis",
        status="planned",
        is_operational=False,
        implementation_notes="Scheduled for Phase 2. Hydrodynamic wave velocity estimation across Mula-Mutha reaches.",
    ),
    ModuleReadiness(
        id="mod-nav-01",
        name="Dynamic Safe Evacuation Routing",
        description="Topography-aware pathfinding avoiding inundated road segments and bridge bottlenecks",
        target_phase=3,
        phase_title="Phase 3: Dynamic Evacuation & Safe Routing",
        status="planned",
        is_operational=False,
        implementation_notes="Scheduled for Phase 3. PostGIS pgRouting graph integration planned.",
    ),
    ModuleReadiness(
        id="mod-shelter-01",
        name="Shelter Identification & Capacity Management",
        description="Safe high-ground shelter registry with real-time occupancy and ration tracking",
        target_phase=3,
        phase_title="Phase 3: Dynamic Evacuation & Safe Routing",
        status="planned",
        is_operational=False,
        implementation_notes="Scheduled for Phase 3. Municipal school and community center registry.",
    ),
    ModuleReadiness(
        id="mod-res-01",
        name="Emergency Resource Optimization",
        description="Constraint-based dispatch optimization for rescue boats, ambulances, NDRF/SDRF teams",
        target_phase=4,
        phase_title="Phase 4: Resource Optimization & Nugen Decision Intelligence",
        status="planned",
        is_operational=False,
        implementation_notes="Scheduled for Phase 4. Google OR-Tools vehicle routing and resource allocation.",
    ),
    ModuleReadiness(
        id="mod-nugen-01",
        name="Nugen Aligned-Model Decision Intelligence",
        description="Explainable natural language disaster action recommendations aligned with SOP guidelines",
        target_phase=4,
        phase_title="Phase 4: Resource Optimization & Nugen Decision Intelligence",
        status="planned",
        is_operational=False,
        implementation_notes="Scheduled for Phase 4. Nugen decision intelligence engine integration.",
    ),
    ModuleReadiness(
        id="mod-sim-01",
        name="What-If Scenario Simulation",
        description="Interactive dam release rate simulation (e.g. 50k cusecs vs 100k cusecs) and flood footprint projection",
        target_phase=4,
        phase_title="Phase 4: Resource Optimization & Nugen Decision Intelligence",
        status="planned",
        is_operational=False,
        implementation_notes="Scheduled for Phase 4. Dam discharge impact scenario runner.",
    ),
]


@router.get(
    "/system/info",
    response_model=SystemInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="System Architecture & Module Catalog",
    description=(
        "Returns comprehensive metadata about FLOOD-X, the Pune pilot geographical region, "
        "and the exact implementation status of all platform subsystems across Phases 0 through 5."
    ),
)
def get_system_info() -> SystemInfoResponse:
    """Returns current architecture metadata and subsystem readiness."""
    is_connected, _, _ = check_db_connection()
    system_status = "operational" if is_connected else "degraded"

    return SystemInfoResponse(
        project_name=settings.PROJECT_NAME,
        project_tagline=settings.PROJECT_TAGLINE,
        project_version=settings.APP_VERSION,
        api_version="v1",
        environment=settings.ENVIRONMENT,
        current_phase="Phase 0: Project Foundation & System Architecture",
        pilot_region=PilotRegion(),
        system_status=system_status,
        modules=MODULE_CATALOG,
    )

