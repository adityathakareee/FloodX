"""FLOOD-X Phase 4: Emergency Resource Optimization & Decision Intelligence Subsystem."""

from app.services.resource_optimization.resource_constants import (
    CATEGORY_VEHICLE,
    CATEGORY_HUMAN,
    CATEGORY_RELIEF,
    CATEGORY_INFRASTRUCTURE,
    ALL_RESOURCE_CATEGORIES,
    ALL_OPERATIONAL_STATUSES,
    ALL_PRIORITY_LEVELS,
    PUNE_OPERATIONAL_SECTORS,
    SECTOR_MAP,
    NDMA_SOP_GUIDELINES,
)
from app.services.resource_optimization.resource_models import (
    ResourceCreate,
    ResourceUpdate,
    ResourceQuantityUpdate,
    ResourceItem,
    ResourceListResponse,
    DemandAssessmentItem,
    DemandAssessmentResponse,
    PriorityAreaItem,
    PriorityRankingResponse,
    OptimizationRunRequest,
    OptimizationRunResponse,
    OptimizationAssignmentItem,
    UnmetDemandItem,
    ResourceAllocateRequest,
    ResourceAllocationItem,
    AllocationApprovalRequest,
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
    ScenarioDeltaMetric,
    NugenStatusResponse,
    DecisionAdvisoryRequest,
    DecisionAdvisoryResponse,
    TacticalActionItem,
)
from app.services.resource_optimization.resource_inventory_service import (
    ResourceInventoryService,
    resource_inventory_service,
)
from app.services.resource_optimization.emergency_demand_service import (
    EmergencyDemandService,
    emergency_demand_service,
)
from app.services.resource_optimization.priority_assessment_service import (
    PriorityAssessmentService,
    priority_assessment_service,
)
from app.services.resource_optimization.optimization_engine import (
    OptimizationEngine,
    optimization_engine,
)
from app.services.resource_optimization.resource_allocation_service import (
    ResourceAllocationService,
    resource_allocation_service,
)
from app.services.resource_optimization.nugen_service import (
    NugenDecisionService,
    nugen_decision_service,
)
from app.services.resource_optimization.scenario_simulation_service import (
    ScenarioSimulationService,
    scenario_simulation_service,
)

__all__ = [
    "CATEGORY_VEHICLE",
    "CATEGORY_HUMAN",
    "CATEGORY_RELIEF",
    "CATEGORY_INFRASTRUCTURE",
    "ALL_RESOURCE_CATEGORIES",
    "ALL_OPERATIONAL_STATUSES",
    "ALL_PRIORITY_LEVELS",
    "PUNE_OPERATIONAL_SECTORS",
    "SECTOR_MAP",
    "NDMA_SOP_GUIDELINES",
    "ResourceCreate",
    "ResourceUpdate",
    "ResourceQuantityUpdate",
    "ResourceItem",
    "ResourceListResponse",
    "DemandAssessmentItem",
    "DemandAssessmentResponse",
    "PriorityAreaItem",
    "PriorityRankingResponse",
    "OptimizationRunRequest",
    "OptimizationRunResponse",
    "OptimizationAssignmentItem",
    "UnmetDemandItem",
    "ResourceAllocateRequest",
    "ResourceAllocationItem",
    "AllocationApprovalRequest",
    "ScenarioSimulationRequest",
    "ScenarioSimulationResponse",
    "ScenarioDeltaMetric",
    "NugenStatusResponse",
    "DecisionAdvisoryRequest",
    "DecisionAdvisoryResponse",
    "TacticalActionItem",
    "ResourceInventoryService",
    "resource_inventory_service",
    "EmergencyDemandService",
    "emergency_demand_service",
    "PriorityAssessmentService",
    "priority_assessment_service",
    "OptimizationEngine",
    "optimization_engine",
    "ResourceAllocationService",
    "resource_allocation_service",
    "NugenDecisionService",
    "nugen_decision_service",
    "ScenarioSimulationService",
    "scenario_simulation_service",
]

