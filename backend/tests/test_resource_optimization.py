"""Automated Unit and Integration Tests for FLOOD-X Phase 4.

Covers:
- Emergency Resource Inventory Management (CRUD, atomic allocate/release, constraints, audit history).
- Multi-Sector Demand Estimation & NDMA Response Prioritization.
- Google OR-Tools Mathematical Constrained Optimization (MIP, SCIP, constraints, unserved demand, shelter rule).
- Nugen Decision Intelligence integration & NDMA SOP Rule-Based Fallback.
- What-If Disaster Scenario Simulation & Strict In-Memory Database Isolation Guarantee.
- REST API Endpoints and Role/Token Security Authorization.
"""

import json
from typing import Dict, Any
import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import TEST_ADMIN_AUTHORITY_TOKEN, TEST_OPERATOR_AUTHORITY_TOKEN
from app.services.resource_optimization.resource_constants import (
    CATEGORY_VEHICLE,
    CATEGORY_HUMAN,
    CATEGORY_RELIEF,
    TYPE_AMBULANCE_ALS,
    TYPE_RESCUE_BOAT,
    TYPE_FOOD_PACKETS,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    OPT_STATUS_OPTIMAL,
    OPT_STATUS_FEASIBLE,
    OPT_STATUS_NO_RESOURCES,
)
from app.services.resource_optimization.resource_models import (
    ResourceCreate,
    ResourceUpdate,
    OptimizationRunRequest,
    ScenarioSimulationRequest,
    DecisionAdvisoryRequest,
    ResourceAllocateRequest,
    AllocationApprovalRequest,
)
from app.services.resource_optimization.resource_inventory_service import resource_inventory_service
from app.services.resource_optimization.emergency_demand_service import emergency_demand_service
from app.services.resource_optimization.priority_assessment_service import priority_assessment_service
from app.services.resource_optimization.optimization_engine import optimization_engine
from app.services.resource_optimization.resource_allocation_service import resource_allocation_service
from app.services.resource_optimization.nugen_service import nugen_decision_service
from app.services.resource_optimization.scenario_simulation_service import scenario_simulation_service
from app.services.evacuation.road_closure_service import road_closure_service


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def admin_headers() -> Dict[str, str]:
    return {"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}


# ============================================================================
# 1. Resource Inventory Tests
# ============================================================================

def test_inventory_crud_and_status():
    """Tests creating, fetching, updating, and deleting an emergency resource."""
    test_code = "TEST-AMB-99"
    new_res = ResourceCreate(
        resource_id=test_code,
        category=CATEGORY_VEHICLE,
        resource_type=TYPE_AMBULANCE_ALS,
        name="Test ALS Unit 99",
        description="Dedicated test ambulance for unit tests",
        total_quantity=5,
        available_quantity=5,
        operational_status="AVAILABLE",
        latitude=18.5204,
        longitude=73.8567,
        base_address="PMC Central Yard",
        responsible_authority="PMC Health Dept",
        is_simulated=True,
    )

    created = resource_inventory_service.create_resource(new_res, actor="Test Operator")
    assert created.id > 0
    assert created.resource_id == test_code
    assert created.total_quantity == 5
    assert created.available_quantity == 5
    assert created.is_simulated is True

    # Fetch by code
    fetched = resource_inventory_service.get_resource_by_code(test_code)
    assert fetched is not None
    assert fetched.id == created.id

    # Update metadata
    updated = resource_inventory_service.update_resource(
        created.id,
        ResourceUpdate(name="Updated ALS Unit 99 Name"),
        actor="Test Operator",
    )
    assert updated.name == "Updated ALS Unit 99 Name"

    # Delete
    del_ok = resource_inventory_service.delete_resource(created.id)
    assert del_ok is True
    assert resource_inventory_service.get_resource_by_id(created.id) is None


def test_inventory_atomic_allocate_and_release():
    """Tests atomic quantity decrement/increment and prevents negative availability."""
    test_code = "TEST-BOAT-42"
    new_res = ResourceCreate(
        resource_id=test_code,
        category=CATEGORY_VEHICLE,
        resource_type=TYPE_RESCUE_BOAT,
        name="Test Rescue Boat 42",
        total_quantity=3,
        available_quantity=3,
        operational_status="AVAILABLE",
        latitude=18.5140,
        longitude=73.8450,
        responsible_authority="NDRF Team 4",
        is_simulated=True,
    )

    created = resource_inventory_service.create_resource(new_res, actor="Test Admin")

    try:
        # Allocate 2 units (1 remains available)
        after_alloc = resource_inventory_service.allocate_quantity(
            created.id,
            quantity=2,
            actor="Officer Sharma",
            notes="Dispatched to Deccan causeway",
        )
        assert after_alloc.available_quantity == 1
        assert after_alloc.allocated_quantity == 2
        assert after_alloc.operational_status == "AVAILABLE"

        # Allocate the remaining 1 unit -> status becomes ALLOCATED
        full_alloc = resource_inventory_service.allocate_quantity(
            created.id,
            quantity=1,
            actor="Officer Sharma",
            notes="Dispatched last boat",
        )
        assert full_alloc.available_quantity == 0
        assert full_alloc.allocated_quantity == 3
        assert full_alloc.operational_status == "ALLOCATED"

        # Over-allocation must fail
        with pytest.raises(ValueError) as exc:
            resource_inventory_service.allocate_quantity(
                created.id,
                quantity=1,  # 0 remains
                actor="Officer Sharma",
            )
        assert "Insufficient available quantity" in str(exc.value)

        # Release 1 unit
        after_release = resource_inventory_service.release_quantity(
            created.id,
            quantity=1,
            actor="Officer Sharma",
            notes="Stand down 1 boat",
        )
        assert after_release.available_quantity == 1
        assert after_release.allocated_quantity == 2

        # Release remaining 2 units -> status becomes AVAILABLE
        final_release = resource_inventory_service.release_quantity(
            created.id,
            quantity=2,
            actor="Officer Sharma",
            notes="Stand down all",
        )
        assert final_release.available_quantity == 3
        assert final_release.allocated_quantity == 0
        assert final_release.operational_status == "AVAILABLE"

    finally:
        resource_inventory_service.delete_resource(created.id)


# ============================================================================
# 2. Demand Estimation & Prioritization Tests
# ============================================================================

def test_emergency_demand_assessment_and_sectors():
    """Verifies that all 8 Pune operational sectors are evaluated with correct weights and priorities."""
    demand_resp = emergency_demand_service.generate_demand_assessments(is_simulation=True)

    assert demand_resp.total_sectors_assessed == 8
    assert len(demand_resp.sectors) == 8
    assert demand_resp.total_ambulances_demanded > 0
    assert demand_resp.total_rescue_teams_demanded > 0

    # Sinhagad Road corridor should have CRITICAL or HIGH priority due to low-lying elevation (<550m)
    sinhagad = next(s for s in demand_resp.sectors if s.sector_id == "PUNE_SEC_SINHAGAD")
    assert sinhagad.priority_level in (PRIORITY_CRITICAL, PRIORITY_HIGH)
    assert sinhagad.is_simulated is True
    assert sinhagad.required_rescue_teams >= 2

    # Deccan Gymkhana should have elevated demand
    deccan = next(s for s in demand_resp.sectors if s.sector_id == "PUNE_SEC_DECCAN")
    assert deccan.priority_level in (PRIORITY_CRITICAL, PRIORITY_HIGH)


def test_priority_ranking_scoring_and_ndma_sop():
    """Verifies transparent priority scoring breakdown and NDMA SOP recommendations."""
    rank_resp = priority_assessment_service.get_ranked_priority_areas()

    assert len(rank_resp.ranked_areas) == 8
    assert "Risk" in rank_resp.weight_formula and "Demand" in rank_resp.weight_formula

    # Must be ranked descending by priority_score
    scores = [a.priority_score for a in rank_resp.ranked_areas]
    assert scores == sorted(scores, reverse=True)

    top_area = rank_resp.ranked_areas[0]
    assert top_area.rank == 1
    assert "score_breakdown" in top_area.model_dump()
    assert top_area.recommended_tactical_action is not None


# ============================================================================
# 3. Google OR-Tools Optimization Tests
# ============================================================================

def test_ortools_optimization_with_inventory():
    """Tests mathematical optimization produces feasible/optimal assignments and respects capacities."""
    demands_resp = emergency_demand_service.generate_demand_assessments(is_simulation=True)
    resources_items, _, _, _ = resource_inventory_service.get_resources(limit=100)

    opt_req = OptimizationRunRequest(
        objective="MINIMIZE_RESPONSE_TIME",
        max_travel_time_sec=3600.0,
        avoid_closed_roads=True,
        enforce_capacity_limits=True,
    )

    opt_resp = optimization_engine.run_optimization(
        request=opt_req,
        demands=demands_resp.sectors,
        resources=resources_items,
    )

    assert opt_resp.solver_status in (OPT_STATUS_OPTIMAL, OPT_STATUS_FEASIBLE)
    assert opt_resp.execution_duration_ms > 0
    assert opt_resp.total_assigned_resources >= 0
    assert "INSUFFICIENT_VERIFIED_SHELTER_CAPACITY" in opt_resp.shelter_capacity_note

    # Validate each assignment adheres to constraints
    for assign in opt_resp.assignments:
        assert assign.assigned_quantity > 0
        assert assign.estimated_travel_time_sec <= 3600.0
        assert assign.route_is_feasible is True


def test_ortools_empty_inventory_handling():
    """Verifies optimization engine handles zero-inventory gracefully."""
    demands_resp = emergency_demand_service.generate_demand_assessments(is_simulation=True)

    opt_req = OptimizationRunRequest(
        objective="MINIMIZE_RESPONSE_TIME",
        max_travel_time_sec=3600.0,
        avoid_closed_roads=True,
        enforce_capacity_limits=True,
    )

    opt_resp = optimization_engine.run_optimization(
        request=opt_req,
        demands=demands_resp.sectors,
        resources=[],  # Empty inventory
    )

    assert opt_resp.solver_status == OPT_STATUS_NO_RESOURCES
    assert opt_resp.total_assigned_resources == 0
    assert opt_resp.demand_coverage_pct == 0.0
    assert len(opt_resp.unmet_demands) > 0


# ============================================================================
# 4. Nugen Decision Intelligence & SOP Advisory Tests
# ============================================================================

def test_nugen_status_and_fallback_reporting():
    """Confirms Nugen reports unavailable state gracefully without claiming live mock API."""
    status = nugen_decision_service.get_status()
    # In test environment, NUGEN_API_KEY is not set
    assert status.is_available is False
    assert status.active_provider == "RULE_BASED_DECISION_FALLBACK"
    assert "Credentials Not Configured" in status.status
    assert status.missing_configuration_notes is not None


def test_nugen_advisory_ndma_compliance():
    """Verifies that generated decision advisory includes NDMA SOP actions and regulatory citations."""
    advisory_req = DecisionAdvisoryRequest(
        include_shortage_analysis=True,
        include_sop_guidelines=True,
    )

    advisory = nugen_decision_service.generate_advisory(advisory_req)

    assert advisory.advisory_id.startswith("ADV-PUNE-")
    assert advisory.is_simulated_advisory is True
    assert len(advisory.critical_observations) > 0
    assert len(advisory.tactical_action_plan) > 0

    # Ensure actions cite official NDMA SOP sections
    action = advisory.tactical_action_plan[0]
    assert "NDMA" in action.regulatory_reference
    assert action.urgency is not None


# ============================================================================
# 5. What-If Scenario Simulation & In-Memory Isolation Tests
# ============================================================================

def test_scenario_simulation_isolation_guarantee():
    """Tests extreme what-if disaster simulation strictly in memory without mutating database."""
    # Count database records before simulation
    _, resources_before, _, _ = resource_inventory_service.get_resources(limit=100)
    closures_before = len(road_closure_service.get_active_closures())

    sim_req = ScenarioSimulationRequest(
        scenario_name="Monsoon Peak Cloudburst + Khadakwasla 50,000 cfs",
        rainfall_multiplier=2.0,
        dam_discharge_cfs=50000.0,
        resource_availability_factor=0.8,
        demand_surge_factor=1.5,
    )

    sim_resp = scenario_simulation_service.run_simulation(sim_req)

    # Validate simulation response
    assert sim_resp.is_simulated is True
    assert sim_resp.dam_discharge_cfs == 50000.0
    assert any("DISCHARGE >= 45,000 CFS" in b for b in sim_resp.dam_submergence_benchmarks_triggered)
    assert sim_resp.simulated_demand_total > sim_resp.baseline_demand_total
    assert len(sim_resp.delta_metrics) >= 4
    assert "CONFIRMED: This scenario simulation operated strictly in-memory" in sim_resp.isolation_guarantee

    # Verify zero database mutation
    _, resources_after, _, _ = resource_inventory_service.get_resources(limit=100)
    closures_after = len(road_closure_service.get_active_closures())

    assert resources_before == resources_after, "Simulation modified persistent resource records!"
    assert closures_before == closures_after, "Simulation modified persistent road closures!"


# ============================================================================
# 6. REST API Endpoints & Role/Security Authorization Tests
# ============================================================================

def test_resources_api_endpoints(test_client: TestClient, admin_headers: Dict[str, str]):
    """Tests resource list, creation with token, unauthorized block, and demo seeding."""
    # 1. Unauthenticated GET is allowed (public read)
    resp = test_client.get("/api/v1/resources")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data

    # 2. Write without auth token must fail (401 or 403)
    create_payload = {
        "resource_id": "API-AMB-01",
        "category": CATEGORY_VEHICLE,
        "resource_type": TYPE_AMBULANCE_ALS,
        "name": "API Test Ambulance",
        "total_quantity": 2,
        "available_quantity": 2,
        "operational_status": "AVAILABLE",
        "responsible_authority": "PMC",
        "is_simulated": True,
    }
    unauth_resp = test_client.post("/api/v1/resources", json=create_payload)
    assert unauth_resp.status_code in (401, 403)

    # 3. Write with valid admin authority succeeds (201)
    auth_resp = test_client.post("/api/v1/resources", json=create_payload, headers=admin_headers)
    assert auth_resp.status_code == 201
    created_id = auth_resp.json()["id"]

    try:
        # 4. Patch quantity with token
        patch_resp = test_client.patch(
            f"/api/v1/resources/{created_id}/quantity",
            json={"available_quantity": 1, "notes": "Dispatched 1 via API"},
            headers=admin_headers,
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["available_quantity"] == 1
    finally:
        # Clean up
        test_client.delete(f"/api/v1/resources/{created_id}", headers=admin_headers)


def test_optimization_and_scenarios_api(test_client: TestClient, admin_headers: Dict[str, str]):
    """Tests optimization execution, runs list, what-if scenarios, and Nugen status."""
    # Optimization trigger requires admin authority
    opt_payload = {
        "objective": "MINIMIZE_RESPONSE_TIME",
        "max_travel_time_sec": 3600.0,
        "avoid_closed_roads": True,
        "enforce_capacity_limits": True,
    }
    opt_resp = test_client.post("/api/v1/optimization/run", json=opt_payload, headers=admin_headers)
    assert opt_resp.status_code == 200
    opt_data = opt_resp.json()
    assert "run_id" in opt_data
    assert "solver_status" in opt_data

    # Scenarios API
    scen_payload = {
        "scenario_name": "API Test Drill",
        "rainfall_multiplier": 1.5,
        "dam_discharge_cfs": 25000.0,
        "resource_availability_factor": 0.9,
        "demand_surge_factor": 1.2,
    }
    scen_resp = test_client.post("/api/v1/scenarios/simulate", json=scen_payload)
    assert scen_resp.status_code == 200
    assert scen_resp.json()["is_simulated"] is True

    # Nugen status API
    nugen_resp = test_client.get("/api/v1/nugen/status")
    assert nugen_resp.status_code == 200
    assert nugen_resp.json()["active_provider"] == "RULE_BASED_DECISION_FALLBACK"

    # Demand and priorities API
    dem_resp = test_client.get("/api/v1/demand/assessments")
    assert dem_resp.status_code == 200
    assert dem_resp.json()["total_sectors_assessed"] == 8

    prio_resp = test_client.get("/api/v1/decision/priorities")
    assert prio_resp.status_code == 200
    assert len(prio_resp.json()["ranked_areas"]) == 8


# ============================================================================
# 7. Verification & Safety Correction Audit Tests
# ============================================================================

def test_inactive_resource_allocation_rejection():
    """Validates that unavailable or under-maintenance assets strictly cannot be allocated."""
    res_code = "TEST-UNAVAIL-01"
    res = resource_inventory_service.create_resource(
        ResourceCreate(
            resource_id=res_code,
            category=CATEGORY_VEHICLE,
            resource_type=TYPE_AMBULANCE_ALS,
            name="Damaged Ambulance",
            total_quantity=2,
            available_quantity=2,
            operational_status="UNAVAILABLE",
            responsible_authority="PMC Health",
            is_simulated=True,
        )
    )
    try:
        with pytest.raises(ValueError, match="cannot be allocated"):
            resource_inventory_service.allocate_quantity(res.id, 1)
    finally:
        resource_inventory_service.delete_resource(res.id)


def test_release_quantity_ceiling_constraint():
    """Validates that released units cannot exceed total quantity and prevents unallocated release."""
    res_code = "TEST-CEILING-01"
    res = resource_inventory_service.create_resource(
        ResourceCreate(
            resource_id=res_code,
            category=CATEGORY_VEHICLE,
            resource_type=TYPE_AMBULANCE_ALS,
            name="Ceiling Test Ambulance",
            total_quantity=3,
            available_quantity=3,
            operational_status="AVAILABLE",
            responsible_authority="PMC Health",
            is_simulated=True,
        )
    )
    try:
        # 1. Release when allocated is 0 must fail
        with pytest.raises(ValueError, match="no allocated units to release"):
            resource_inventory_service.release_quantity(res.id, 1)

        # 2. Allocate 2 units
        allocated = resource_inventory_service.allocate_quantity(res.id, 2)
        assert allocated.available_quantity == 1
        assert allocated.allocated_quantity == 2

        # 3. Release 2 units
        released = resource_inventory_service.release_quantity(res.id, 2)
        assert released.available_quantity == 3
        assert released.allocated_quantity == 0
        assert released.available_quantity <= res.total_quantity
    finally:
        resource_inventory_service.delete_resource(res.id)


def test_optimization_only_verified_resources():
    """Validates that only_verified_resources=True returns NO_RESOURCES when only simulated assets exist."""
    demands = emergency_demand_service.generate_demand_assessments(is_simulation=True)
    resources, _, _, _ = resource_inventory_service.get_resources(limit=50)

    req = OptimizationRunRequest(
        objective="MINIMIZE_RESPONSE_TIME",
        max_travel_time_sec=3600.0,
        avoid_closed_roads=True,
        only_verified_resources=True,
    )
    res = optimization_engine.run_optimization(
        request=req,
        demands=demands.sectors,
        resources=resources,
    )

    assert res.solver_status == OPT_STATUS_NO_RESOURCES
    assert res.total_assigned_resources == 0
    assert len(res.assignments) == 0
    assert res.verified_resources_assigned == 0
    assert len(res.unmet_demands) > 0


def test_demand_assessment_scientific_calibration():
    """Validates that demand assessment uses relative terrain indicators and avoids unvalidated <550m claim."""
    demands_resp = emergency_demand_service.generate_demand_assessments(is_simulation=True)
    assert demands_resp.total_sectors_assessed == 8

    for s in demands_resp.sectors:
        # Ensure no crude <550m DEM depression claim
        assert "<550m DEM" not in (s.missing_data_notes or "")
        # Ensure standardized municipal planning explanation
        assert "Standardized municipal planning units" in (s.missing_data_notes or "")
        assert s.risk_score >= 0.0 and s.risk_score <= 100.0
        assert s.demand_score >= 0.0 and s.demand_score <= 100.0


def test_scenario_simulation_with_simulated_road_closures():
    """Validates that scenario simulation passes extra closed roads to the optimization engine without DB mutation."""
    req = ScenarioSimulationRequest(
        scenario_name="Bhide Causeway Inundation Drill",
        rainfall_multiplier=2.0,
        dam_discharge_cfs=15000.0,
        resource_availability_factor=0.85,
        demand_surge_factor=1.2,
        additional_closed_edge_ids=["SIM_CUSTOM_BLOCKED_EDGE_1"],
    )
    res = scenario_simulation_service.run_simulation(req)

    assert res.is_simulated is True
    assert res.dam_discharge_cfs == 15000.0
    # Dam benchmark for 15,000 cfs must carry unverified operational reference label
    assert any("UNVERIFIED_OPERATIONAL_REFERENCE" in b for b in res.dam_submergence_benchmarks_triggered)
    # Impassable road count includes custom edge + dam simulated edge
    assert res.newly_impassable_roads_count >= 2
    assert "CONFIRMED: This scenario simulation operated strictly in-memory" in res.isolation_guarantee

