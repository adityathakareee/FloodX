"""Aggregated API v1 Router for FLOOD-X."""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    system,
    ingestion,
    environment,
    gis,
    data_quality,
    features,
    ml,
    prospective,
    routing,
    evacuation,
    resources,
    demand_prioritization,
    optimization,
    scenarios,
    nugen,
    impact,
    auth,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(system.router, tags=["System Architecture"])
api_router.include_router(auth.router)
api_router.include_router(ingestion.router)
api_router.include_router(environment.router)
api_router.include_router(gis.router)
api_router.include_router(data_quality.router)
api_router.include_router(features.router)
api_router.include_router(ml.router)
api_router.include_router(prospective.router)
api_router.include_router(routing.router)
api_router.include_router(evacuation.router)
api_router.include_router(resources.router)
api_router.include_router(demand_prioritization.router)
api_router.include_router(optimization.router)
api_router.include_router(scenarios.router)
api_router.include_router(nugen.router)
api_router.include_router(impact.router)
