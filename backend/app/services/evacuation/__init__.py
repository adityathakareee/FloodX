"""Evacuation Intelligence Package for FLOOD-X Phase 3.2.

Provides complete flood-aware evacuation planning, environmental road exposure mapping,
critical bridge hazard monitoring, municipal road closure management, MultiDiGraph routing,
and shelter suitability assessment.
"""

from app.services.evacuation.evacuation_constants import (
    PROFILE_FASTEST,
    PROFILE_SAFEST,
    PROFILE_BALANCED,
    ROAD_STATUS_SAFE,
    ROAD_STATUS_CAUTION,
    ROAD_STATUS_HAZARDOUS,
    ROAD_STATUS_IMPASSABLE,
    EXPOSURE_LOW,
    EXPOSURE_MODERATE,
    EXPOSURE_HIGH,
    EXPOSURE_CRITICAL,
    SHELTER_VERIFIED,
    SHELTER_CANDIDATE,
    SHELTER_UNVERIFIED,
    SHELTER_INACTIVE,
    INFRA_STATUS_NORMAL,
    INFRA_STATUS_POTENTIALLY_EXPOSED,
    INFRA_STATUS_REQUIRES_VERIFICATION,
    INFRA_STATUS_CONFIRMED_BLOCKED,
    INFRA_STATUS_SIMULATED_BLOCKAGE,
    OFFICIAL_EMERGENCY_DISCLAIMER
)

from app.services.evacuation.evacuation_models import (
    RoadExposureItem,
    RoadSafetyItem,
    InfrastructureSafetyItem,
    RoadClosureCreate,
    RoadClosureUpdate,
    RoadClosureItem,
    ShelterCreate,
    ShelterUpdate,
    ShelterItem,
    RouteRequest,
    RouteStepItem,
    RouteAlternativeItem,
    RoutePlanResponse,
    ShelterRecommendationItem,
    ShelterRecommendationResponse,
    EvacuationStatusResponse,
    EvacuationStatisticsResponse
)

from app.services.evacuation.flood_exposure_service import flood_exposure_service, FloodExposureService
from app.services.evacuation.bridge_safety_service import bridge_safety_service, BridgeSafetyService
from app.services.evacuation.road_closure_service import road_closure_service, RoadClosureService
from app.services.evacuation.road_safety_service import road_safety_service, RoadSafetyService
from app.services.evacuation.dynamic_edge_weights import dynamic_weight_calculator, DynamicEdgeWeightCalculator
from app.services.evacuation.routing_algorithms import evacuation_routing_engine, EvacuationRoutingEngine
from app.services.evacuation.shelter_service import shelter_service, ShelterService
from app.services.evacuation.destination_optimizer import destination_optimizer, DestinationOptimizer
from app.services.evacuation.evacuation_service import evacuation_service, EvacuationIntelligenceService

__all__ = [
    "flood_exposure_service",
    "FloodExposureService",
    "bridge_safety_service",
    "BridgeSafetyService",
    "road_closure_service",
    "RoadClosureService",
    "road_safety_service",
    "RoadSafetyService",
    "dynamic_weight_calculator",
    "DynamicEdgeWeightCalculator",
    "evacuation_routing_engine",
    "EvacuationRoutingEngine",
    "shelter_service",
    "ShelterService",
    "destination_optimizer",
    "DestinationOptimizer",
    "evacuation_service",
    "EvacuationIntelligenceService",
    "RoadExposureItem",
    "RoadSafetyItem",
    "InfrastructureSafetyItem",
    "RoadClosureCreate",
    "RoadClosureUpdate",
    "RoadClosureItem",
    "ShelterCreate",
    "ShelterUpdate",
    "ShelterItem",
    "RouteRequest",
    "RouteStepItem",
    "RouteAlternativeItem",
    "RoutePlanResponse",
    "ShelterRecommendationItem",
    "ShelterRecommendationResponse",
    "EvacuationStatusResponse",
    "EvacuationStatisticsResponse",
    "PROFILE_FASTEST",
    "PROFILE_SAFEST",
    "PROFILE_BALANCED",
    "ROAD_STATUS_SAFE",
    "ROAD_STATUS_CAUTION",
    "ROAD_STATUS_HAZARDOUS",
    "ROAD_STATUS_IMPASSABLE",
    "EXPOSURE_LOW",
    "EXPOSURE_MODERATE",
    "EXPOSURE_HIGH",
    "EXPOSURE_CRITICAL",
    "SHELTER_VERIFIED",
    "SHELTER_CANDIDATE",
    "SHELTER_UNVERIFIED",
    "SHELTER_INACTIVE",
    "INFRA_STATUS_NORMAL",
    "INFRA_STATUS_POTENTIALLY_EXPOSED",
    "INFRA_STATUS_REQUIRES_VERIFICATION",
    "INFRA_STATUS_CONFIRMED_BLOCKED",
    "INFRA_STATUS_SIMULATED_BLOCKAGE",
    "OFFICIAL_EMERGENCY_DISCLAIMER"
]
