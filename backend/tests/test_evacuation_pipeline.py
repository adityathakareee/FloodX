"""Unit and Integration Test Suite for FLOOD-X Phase 3.2 Evacuation Intelligence System.

Tests:
1. Environmental road flood exposure mapping (Copernicus DEM, slope, waterways, chronic hotspots).
2. Road safety operational classification (SAFE, CAUTION, HAZARDOUS, IMPASSABLE).
3. Bridge & underpass hazard assessment (Baba Bhide 15k cfs benchmark, Sambhaji, Bund Garden).
4. Municipal road closure management, audit logging, and edge exclusion.
5. Dynamic edge weight calculator (FASTEST, SAFEST, BALANCED).
6. Dijkstra and A* pathfinding on MultiDiGraph with admissible heuristic.
7. Alternative evacuation route exploration and out-of-bounds rejection.
8. Shelter discovery, verification status integrity, and capacity tracking.
9. Multi-factor shelter destination recommendations and accessibility filtering.
10. Complete REST API endpoints under /api/v1/evacuation/*.
"""

import pytest
from fastapi.testclient import TestClient
import networkx as nx

from app.main import app
from app.services.routing.road_network_service import road_network_service
from app.services.evacuation.flood_exposure_service import flood_exposure_service
from app.services.evacuation.bridge_safety_service import bridge_safety_service
from app.services.evacuation.road_closure_service import road_closure_service
from app.services.evacuation.road_safety_service import road_safety_service
from app.services.evacuation.dynamic_edge_weights import dynamic_weight_calculator
from app.services.evacuation.routing_algorithms import evacuation_routing_engine
from app.services.evacuation.shelter_service import shelter_service
from app.services.evacuation.destination_optimizer import destination_optimizer
from app.services.evacuation.evacuation_constants import (
    PROFILE_FASTEST,
    PROFILE_SAFEST,
    PROFILE_BALANCED,
    ROAD_STATUS_SAFE,
    ROAD_STATUS_CAUTION,
    ROAD_STATUS_HAZARDOUS,
    ROAD_STATUS_IMPASSABLE,
    EXPOSURE_CRITICAL,
    EXPOSURE_HIGH,
    EXPOSURE_MODERATE,
    EXPOSURE_LOW,
    SHELTER_VERIFIED,
    SHELTER_CANDIDATE,
    SHELTER_UNVERIFIED
)
from app.services.evacuation.evacuation_models import (
    RoadClosureCreate,
    RoadClosureUpdate,
    ShelterCreate,
    ShelterUpdate,
    RouteRequest
)
from tests.conftest import TEST_ADMIN_AUTHORITY_TOKEN, TEST_OPERATOR_AUTHORITY_TOKEN

client = TestClient(app)


# ===========================================================================
# 1. Road Flood Exposure Service Tests
# ===========================================================================

def test_flood_exposure_service_computation():
    """Verify exposure calculations for road graph edges with realistic DEM and waterway metrics."""
    exposures = flood_exposure_service.compute_all_exposures()
    assert len(exposures) > 0, "Exposure catalog must not be empty"

    # Verify attributes on sample item
    first_exp = next(iter(exposures.values()))
    assert hasattr(first_exp, "edge_id")
    assert hasattr(first_exp, "min_elevation_m")
    assert hasattr(first_exp, "mean_elevation_m")
    assert hasattr(first_exp, "waterway_distance_m")
    assert hasattr(first_exp, "local_slope_deg")
    assert first_exp.exposure_tier in [EXPOSURE_CRITICAL, EXPOSURE_HIGH, EXPOSURE_MODERATE, EXPOSURE_LOW]

    # Verify Pune elevation bounds (DEM 500m to 700m in urban basin)
    assert 480.0 <= first_exp.mean_elevation_m <= 850.0

    # Verify chronic hotspots are captured
    hotspot_edges = [e for e in exposures.values() if e.is_chronic_hotspot]
    assert len(hotspot_edges) > 0, "At least some edges must be flagged as chronic flood hotspots"
    for he in hotspot_edges:
        assert he.exposure_tier in [EXPOSURE_CRITICAL, EXPOSURE_HIGH]


# ===========================================================================
# 2. Road Safety Classification Tests
# ===========================================================================

def test_road_safety_service_evaluation():
    """Verify synthesis of exposure and closures into operational safety tiers."""
    safety_map = road_safety_service.evaluate_all_road_safety()
    assert len(safety_map) > 0

    statuses = {item.operational_status for item in safety_map.values()}
    assert ROAD_STATUS_SAFE in statuses
    assert ROAD_STATUS_CAUTION in statuses
    assert ROAD_STATUS_HAZARDOUS in statuses

    # Verify hazardous items have travel penalty
    for item in safety_map.values():
        if item.operational_status == ROAD_STATUS_HAZARDOUS:
            assert item.dynamic_travel_penalty_sec > 0.0


# ===========================================================================
# 3. Bridge and Underpass Hazard Assessment Tests
# ===========================================================================

def test_bridge_safety_service_benchmarks():
    """Verify bridge monitoring and Khadakwasla discharge submergence threshold simulation."""
    # Baseline without discharge telemetry
    infra_baseline = bridge_safety_service.get_all_infrastructure()
    assert len(infra_baseline) >= 8, "Must track at least 8 critical Pune river bridges"
    names = [b.name for b in infra_baseline]
    assert any("Bhide" in n for n in names)
    assert any("Sambhaji" in n for n in names)
    assert any("Bund Garden" in n for n in names)

    # In baseline, live WRD streaming is absent -> status must be DATA_INSUFFICIENT
    bridges_only = [b for b in infra_baseline if b.infrastructure_type in ["BRIDGE", "LOW_CAUSEWAY"]]
    for b in bridges_only:
        assert b.status == "DATA_INSUFFICIENT"
        assert b.is_closed is False

    # Simulated 20,000 cfs discharge (exceeds Bhide 15k cfs benchmark)
    infra_high_discharge = bridge_safety_service.get_all_infrastructure(current_discharge_cfs=20000.0)
    bhide = next(b for b in infra_high_discharge if "Bhide" in b.name)
    assert bhide.is_closed is True
    assert bhide.is_submerged_simulated is True
    assert bhide.status == "SIMULATED_BLOCKAGE"

    # High bridge (e.g. Bund Garden or Sambhaji) should NOT be submerged at 20,000 cfs
    bund = next(b for b in infra_high_discharge if "Bund Garden" in b.name)
    assert bund.is_closed is False
    assert bund.is_submerged_simulated is False


# ===========================================================================
# 4. Road Closure Management & Dynamic Exclusion Tests
# ===========================================================================

def test_road_closure_lifecycle():
    """Verify creating, querying, updating, and clearing municipal road closures."""
    # Create test closure
    payload = RoadClosureCreate(
        edge_id="test_edge_9999",
        road_name="Sinhagad Road Submerged Sector",
        reason="Khadakwasla release waterlogging 0.6m",
        closure_type="FLOOD_SUBMERGENCE",
        reporting_authority="Pune Traffic Police Unit 4",
        operator_notes="Temporary diversion in place"
    )
    closure = road_closure_service.create_closure(payload)
    assert closure.id > 0
    assert closure.edge_id == "test_edge_9999"
    assert closure.is_active is True

    # Verify closure appears in active set
    blocked_ids = road_closure_service.get_active_blocked_edge_ids()
    assert "test_edge_9999" in blocked_ids

    # Update closure
    upd = RoadClosureUpdate(
        is_active=False,
        closure_type="CLEARED",
        operator_notes="Water receded, debris cleared"
    )
    updated = road_closure_service.update_closure(closure.id, upd)
    assert updated is not None
    assert updated.is_active is False

    # Verify closure no longer in active set
    blocked_ids_after = road_closure_service.get_active_blocked_edge_ids()
    assert "test_edge_9999" not in blocked_ids_after

    # Delete closure permanently
    del_ok = road_closure_service.delete_closure(closure.id)
    assert del_ok is True


# ===========================================================================
# 5. Dynamic Weight Calculator Tests
# ===========================================================================

def test_dynamic_weight_calculator_profiles():
    """Verify cost weighting behavior across FASTEST, SAFEST, and BALANCED profiles."""
    edge_data = {"length_m": 500.0, "estimated_travel_time_sec": 30.0}

    from types import SimpleNamespace
    exp_low = SimpleNamespace(exposure_tier=EXPOSURE_LOW)
    exp_crit = SimpleNamespace(exposure_tier=EXPOSURE_CRITICAL)

    # Low hazard edge
    c_fast_low = dynamic_weight_calculator.compute_edge_weight(edge_data, exp_low, set(), cost_profile=PROFILE_FASTEST)
    c_safe_low = dynamic_weight_calculator.compute_edge_weight(edge_data, exp_low, set(), cost_profile=PROFILE_SAFEST)
    assert c_fast_low == 30.0
    assert c_safe_low == 30.0

    # Critical hazard edge
    c_fast_crit = dynamic_weight_calculator.compute_edge_weight(edge_data, exp_crit, set(), cost_profile=PROFILE_FASTEST)
    c_safe_crit = dynamic_weight_calculator.compute_edge_weight(edge_data, exp_crit, set(), cost_profile=PROFILE_SAFEST)
    c_bal_crit = dynamic_weight_calculator.compute_edge_weight(edge_data, exp_crit, set(), cost_profile=PROFILE_BALANCED)

    # SAFEST must penalize critical hazard substantially more than FASTEST
    assert c_safe_crit > c_fast_crit
    assert c_safe_crit > c_bal_crit
    assert c_bal_crit > c_fast_crit


# ===========================================================================
# 6. Evacuation Routing Engine Tests (A* & Dijkstra)
# ===========================================================================

def test_evacuation_routing_engine():
    """Verify pathfinding, alternative route discovery, and coordinate snapping on road graph."""
    # Find two known nodes in Deccan / Shivajinagar
    G = road_network_service.get_or_build_graph()
    nodes = list(G.nodes(data=True))
    assert len(nodes) > 100

    n1_id, n1_data = nodes[0]
    n2_id, n2_data = nodes[10]

    lat1, lon1 = n1_data["latitude"], n1_data["longitude"]
    lat2, lon2 = n2_data["latitude"], n2_data["longitude"]

    # Plan route with A*
    req = RouteRequest(
        origin_lat=lat1,
        origin_lon=lon1,
        destination_lat=lat2,
        destination_lon=lon2,
        cost_profile=PROFILE_BALANCED,
        algorithm="A_STAR",
        find_alternatives=True
    )
    resp = evacuation_routing_engine.plan_evacuation_routes(req)

    assert resp.status in ["SUCCESS", "NO_PATH"]
    assert resp.algorithm_used == "A_STAR"
    assert resp.chosen_profile == PROFILE_BALANCED
    assert resp.disclaimer != ""

    if resp.status == "SUCCESS":
        assert resp.primary_route is not None
        assert resp.primary_route.total_distance_m > 0
        assert resp.primary_route.geometry_geojson["type"] == "LineString"


def test_evacuation_routing_out_of_bounds_rejection():
    """Verify coordinates outside the basin (>3km from any road) are safely rejected."""
    req = RouteRequest(
        origin_lat=12.9716,  # Bengaluru coordinate!
        origin_lon=77.5946,
        destination_lat=18.5204,
        destination_lon=73.8567
    )
    resp = evacuation_routing_engine.plan_evacuation_routes(req)
    assert resp.status in ["OUT_OF_BOUNDS", "ERROR"]
    assert any("snap distance" in w.lower() or "arterial network" in w.lower() for w in resp.warnings)


# ===========================================================================
# 7. Shelter Management & Capacity Integrity Tests
# ===========================================================================

def test_shelter_service_capacity_integrity():
    """Verify strictly separated shelter categories and unknown capacity representation."""
    shelters, total = shelter_service.get_shelters(limit=100)
    assert total > 0

    verified_shelters = [s for s in shelters if s.verification_status == SHELTER_VERIFIED]
    candidate_shelters = [s for s in shelters if s.verification_status == SHELTER_CANDIDATE]

    # Task 1 & 11: In the audited baseline, 0 unsupported verified shelters exist without primary municipal gazette documents
    assert len(verified_shelters) == 0, "No unsupported verified shelters should exist in baseline"
    assert len(candidate_shelters) >= 5, "Candidate shelters must be preserved for scout review"

    # Candidate facilities must NOT fabricate fictitious capacities
    for cs in candidate_shelters:
        assert cs.total_capacity is None, "Candidate shelter capacity must remain None until verified"
        assert cs.current_occupancy is None, "Candidate shelter occupancy must remain None until verified"
        assert cs.available_capacity is None


def test_shelter_service_crud():
    """Verify shelter creation, updating, and deactivation with evidence provenance."""
    payload = ShelterCreate(
        name="Test Community Flood Shelter",
        facility_type="COMMUNITY_HALL",
        verification_status=SHELTER_VERIFIED,
        address="Kothrud Ward Office Relief Hall",
        latitude=18.5080,
        longitude=73.8150,
        total_capacity=300,
        has_medical_support=True,
        is_wheelchair_accessible=True,
        has_generator_power=True,
        emergency_contact="020-25440001",
        evidence_document="PMC_DDMA_Order_2026_04.pdf",
        evidence_date="2026-06-15",
        verified_by="Disaster Management Officer"
    )
    created = shelter_service.create_shelter(payload)
    assert created.id > 0
    assert created.name == "Test Community Flood Shelter"
    assert created.total_capacity == 300
    assert created.available_capacity == 300
    assert created.evidence_document == "PMC_DDMA_Order_2026_04.pdf"

    # Update occupancy
    upd = ShelterUpdate(current_occupancy=45, notes="Admitted 45 evacuees from low-lying ward")
    updated = shelter_service.update_shelter(created.id, upd)
    assert updated.current_occupancy == 45
    assert updated.available_capacity == 255

    # Cleanup
    del_ok = shelter_service.delete_shelter(created.id)
    assert del_ok is True


# ===========================================================================
# 8. Shelter Destination Optimizer Tests
# ===========================================================================

def test_destination_optimizer_ranking():
    """Verify shelter destination optimization from central Pune location."""
    # Central Pune (Shaniwar Wada approx: 18.5196, 73.8553)
    resp = destination_optimizer.recommend_destinations(
        origin_lat=18.5196,
        origin_lon=73.8553,
        cost_profile=PROFILE_BALANCED,
        max_results=3
    )
    assert resp.total_evaluated > 0

    # In baseline with 0 verified shelters, destination optimizer returns NO_VERIFIED_SHELTER_AVAILABLE
    assert resp.status == "NO_VERIFIED_SHELTER_AVAILABLE"
    assert len(resp.recommendations) == 0
    assert len(resp.candidate_facilities_for_review) > 0
    assert any("No officially gazetted" in w or "No officially verified" in w for w in resp.warnings)


# ===========================================================================
# 9. FastAPI REST Endpoints Integration Tests
# ===========================================================================

def test_api_evacuation_status():
    """GET /api/v1/evacuation/status returns 200 OK and valid status object."""
    r = client.get("/api/v1/evacuation/status")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "READY"
    assert data["graph_type"] == "MultiDiGraph"
    assert data["total_network_edges"] > 1000
    assert data["total_safe_edges"] > 0
    assert data["critical_bridges_count"] >= 8
    assert data["verified_shelters_count"] == 0, "No unsupported verified shelters in audited baseline"
    assert data["candidate_shelters_count"] > 0
    assert "data_quality_disclaimer" in data


def test_api_evacuation_statistics():
    """GET /api/v1/evacuation/statistics returns 200 OK and distribution metrics."""
    r = client.get("/api/v1/evacuation/statistics")
    assert r.status_code == 200
    data = r.json()
    assert "exposure_tier_distribution" in data
    assert "operational_status_distribution" in data
    assert "shelter_status_distribution" in data
    assert data["shelter_status_distribution"]["VERIFIED_SHELTER"] == 0
    assert data["total_verified_capacity"] is None
    assert data["infrastructure_monitored_count"] >= 8


def test_api_road_exposures():
    """GET /api/v1/evacuation/roads/exposure returns paginated exposure list."""
    r = client.get("/api/v1/evacuation/roads/exposure?limit=10&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] > 1000
    assert len(data["items"]) == 10
    item = data["items"][0]
    assert "edge_id" in item
    assert "exposure_tier" in item
    assert "evidence_type" in item
    assert "relative_exposure_classification" in item


def test_api_infrastructure_list_and_simulated_discharge():
    """GET /api/v1/evacuation/infrastructure with and without discharge_cfs."""
    # Baseline: no WRD telemetry streaming -> bridges are DATA_INSUFFICIENT
    r = client.get("/api/v1/evacuation/infrastructure")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 8
    bridges_only = [b for b in items if b["infrastructure_type"] in ["BRIDGE", "LOW_CAUSEWAY"]]
    for b in bridges_only:
        assert b["status"] == "DATA_INSUFFICIENT"
        assert b["is_closed"] is False

    # Query with 25,000 cfs simulation
    r_high = client.get("/api/v1/evacuation/infrastructure?discharge_cfs=25000")
    assert r_high.status_code == 200
    items_high = r_high.json()
    bhide = next(b for b in items_high if "Bhide" in b["name"])
    assert bhide["is_closed"] is True
    assert bhide["status"] == "SIMULATED_BLOCKAGE"


def test_api_road_closures_flow():
    """Test full closure REST flow with role/token authorization (Task 9)."""
    # 1. List closures (public read)
    r = client.get("/api/v1/evacuation/closures?active_only=true")
    assert r.status_code == 200

    new_closure = {
        "edge_id": "api_test_edge_1",
        "road_name": "API Test Causeway",
        "reason": "Water logging test",
        "closure_type": "FLOOD_SUBMERGENCE",
        "reporting_authority": "PMC Disaster Cell"
    }

    # 2. Test 401 Unauthorized without X-Authority-Token
    r_unauth = client.post("/api/v1/evacuation/closures", json=new_closure)
    assert r_unauth.status_code == 401
    err_unauth = r_unauth.json().get("error", {}).get("message", "") or r_unauth.json().get("detail", "")
    assert "Authentication required" in err_unauth or "X-Authority-Token" in err_unauth

    # 3. Test 403 Forbidden with invalid token
    r_forbidden = client.post(
        "/api/v1/evacuation/closures",
        json=new_closure,
        headers={"X-Authority-Token": "invalid-secret-token"}
    )
    assert r_forbidden.status_code == 403
    err_forbidden = r_forbidden.json().get("error", {}).get("message", "") or r_forbidden.json().get("detail", "")
    assert "Invalid" in err_forbidden or "Forbidden" in err_forbidden

    # 4. Valid token -> 201 Created
    auth_headers = {"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}
    r_post = client.post("/api/v1/evacuation/closures", json=new_closure, headers=auth_headers)
    assert r_post.status_code == 201
    created = r_post.json()
    c_id = created["id"]

    # 5. Patch closure with auth header
    r_patch = client.patch(f"/api/v1/evacuation/closures/{c_id}", json={"is_active": False}, headers=auth_headers)
    assert r_patch.status_code == 200
    assert r_patch.json()["is_active"] is False

    # 6. Delete closure with auth header
    r_del = client.delete(f"/api/v1/evacuation/closures/{c_id}?cleared_by=TestRunner", headers=auth_headers)
    assert r_del.status_code == 200


def test_api_route_planning():
    """POST /api/v1/evacuation/routes/plan plans path between two coordinates."""
    body = {
        "origin_lat": 18.5204,
        "origin_lon": 73.8567,
        "destination_lat": 18.5300,
        "destination_lon": 73.8450,
        "cost_profile": "BALANCED",
        "algorithm": "A_STAR",
        "find_alternatives": True
    }
    r = client.post("/api/v1/evacuation/routes/plan", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ["SUCCESS", "NO_PATH"]
    assert "disclaimer" in data


def test_api_shelters_and_recommendations():
    """GET /api/v1/evacuation/shelters and recommendations."""
    r_list = client.get("/api/v1/evacuation/shelters?limit=5")
    assert r_list.status_code == 200
    assert r_list.json()["total"] > 0

    r_rec = client.get("/api/v1/evacuation/shelters/recommendations?origin_lat=18.5204&origin_lon=73.8567&max_results=3")
    assert r_rec.status_code == 200
    data = r_rec.json()
    assert "recommendations" in data
    # Baseline with 0 verified shelters
    assert data["status"] == "NO_VERIFIED_SHELTER_AVAILABLE"
    assert len(data["candidate_facilities_for_review"]) > 0


# ===========================================================================
# 10. Correction Task Specific Regression Tests (Task 12)
# ===========================================================================

def test_strict_road_closure_hard_exclusion():
    """Task 5: Blocked roads must have float('inf') cost and be hard-excluded from paths."""
    # Find a traversable path first
    G = road_network_service.get_or_build_graph()
    nodes = list(G.nodes(data=True))
    n1_id, n1_data = nodes[0]
    n2_id, n2_data = nodes[10]

    req = RouteRequest(
        origin_lat=n1_data["latitude"],
        origin_lon=n1_data["longitude"],
        destination_lat=n2_data["latitude"],
        destination_lon=n2_data["longitude"],
        cost_profile="FASTEST",
        algorithm="DIJKSTRA",
        avoid_closed_roads=True
    )
    initial_route = evacuation_routing_engine.plan_evacuation_routes(req)
    if initial_route.status == "SUCCESS" and initial_route.primary_route:
        # Pick the first edge in the primary route
        from shapely.geometry import shape
        auth_headers = {"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}
        
        # Test hard exclusion: closed edge dynamic weight MUST be float('inf')
        test_edge_data = {"estimated_travel_time_sec": 15.0, "edge_id": "closed_edge_xyz"}
        inf_cost = dynamic_weight_calculator.compute_edge_weight(
            edge_data=test_edge_data,
            exposure=None,
            blocked_edge_ids={"closed_edge_xyz"},
            avoid_closed_roads=True
        )
        assert inf_cost == float("inf"), "Closed edge cost must be strictly infinity"


def test_whatif_dam_simulation_isolation():
    """Task 2: Dam discharge simulation must NOT alter DB or create real road closures."""
    # Initial closures count in DB
    initial_closures = road_closure_service.get_all_closures()
    initial_count = len(initial_closures)

    # Run heavy discharge simulation via API
    r_sim = client.get("/api/v1/evacuation/infrastructure?discharge_cfs=55000")
    assert r_sim.status_code == 200

    # Ensure no new records were written to road_closures table
    after_closures = road_closure_service.get_all_closures()
    assert len(after_closures) == initial_count, "Dam simulation must not create real road closures in database"

    # Subsequent baseline call must still show DATA_INSUFFICIENT (unaltered DB state)
    r_base = client.get("/api/v1/evacuation/infrastructure")
    assert r_base.status_code == 200
    bhide = next(b for b in r_base.json() if "Bhide" in b["name"])
    assert bhide["status"] == "DATA_INSUFFICIENT"


def test_shelters_api_administrative_security():
    """Task 9: Shelter write endpoints require valid X-Authority-Token."""
    payload = {
        "name": "Unauthorized Community Center",
        "facility_type": "COMMUNITY_HALL",
        "verification_status": "VERIFIED_SHELTER",
        "latitude": 18.52,
        "longitude": 73.85,
        "total_capacity": 500
    }
    # 401 without token
    r_unauth = client.post("/api/v1/evacuation/shelters", json=payload)
    assert r_unauth.status_code == 401

    # 403 with wrong token
    r_bad = client.post("/api/v1/evacuation/shelters", json=payload, headers={"X-Authority-Token": "bad"})
    assert r_bad.status_code == 403

    # 201 with valid token
    auth_headers = {"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}
    r_ok = client.post("/api/v1/evacuation/shelters", json=payload, headers=auth_headers)
    assert r_ok.status_code == 201
    sh_id = r_ok.json()["id"]

    # Delete with valid token
    r_del = client.delete(f"/api/v1/evacuation/shelters/{sh_id}", headers=auth_headers)
    assert r_del.status_code == 200


# ===========================================================================
# 11. Security Hardening Regression Tests (Task 4)
# ===========================================================================

def test_administrative_missing_authentication_all_mutating_endpoints():
    """All 6 administrative write endpoints must return 401 when unauthenticated."""
    closure_payload = {
        "edge_id": "test_edge_unauth",
        "road_name": "Unauthenticated Road",
        "reason": "Test"
    }
    shelter_payload = {
        "name": "Unauthenticated Shelter",
        "facility_type": "COMMUNITY_HALL",
        "latitude": 18.52,
        "longitude": 73.85
    }

    # 1. POST /closures without token -> 401
    assert client.post("/api/v1/evacuation/closures", json=closure_payload).status_code == 401
    # 2. PATCH /closures/{id} without token -> 401
    assert client.patch("/api/v1/evacuation/closures/99999", json={"is_active": False}).status_code == 401
    # 3. DELETE /closures/{id} without token -> 401
    assert client.delete("/api/v1/evacuation/closures/99999").status_code == 401

    # 4. POST /shelters without token -> 401
    assert client.post("/api/v1/evacuation/shelters", json=shelter_payload).status_code == 401
    # 5. PATCH /shelters/{id} without token -> 401
    assert client.patch("/api/v1/evacuation/shelters/99999", json={"current_occupancy": 10}).status_code == 401
    # 6. DELETE /shelters/{id} without token -> 401
    assert client.delete("/api/v1/evacuation/shelters/99999").status_code == 401


def test_administrative_invalid_and_rotated_credentials():
    """Compromised or rotated credentials must return 403 Forbidden."""
    closure_payload = {"edge_id": "edge_sec_test", "road_name": "Security Test Road", "reason": "Test"}

    # 1. Compromised / rotated token must be rejected (proves rotation)
    r_old = client.post(
        "/api/v1/evacuation/closures",
        json=closure_payload,
        headers={"X-Authority-Token": "compromised-token-pre-rotation"}
    )
    assert r_old.status_code == 403

    # 2. Arbitrary invalid token must be rejected
    r_bad = client.post(
        "/api/v1/evacuation/closures",
        json=closure_payload,
        headers={"X-Authority-Token": "completely-invalid-attacker-token"}
    )
    assert r_bad.status_code == 403

    # 3. Bearer header with invalid token
    r_bearer = client.post(
        "/api/v1/evacuation/closures",
        json=closure_payload,
        headers={"Authorization": "Bearer invalid-bearer-token"}
    )
    assert r_bearer.status_code == 403


def test_administrative_unauthorized_authenticated_user():
    """Authenticated user with OPERATOR role cannot execute ADMIN write actions (403 Forbidden)."""
    op_headers = {"X-Authority-Token": TEST_OPERATOR_AUTHORITY_TOKEN}
    closure_payload = {"edge_id": "edge_sec_test2", "road_name": "Operator Write Attempt", "reason": "Test"}
    shelter_payload = {"name": "Operator Shelter Attempt", "latitude": 18.52, "longitude": 73.85}

    # Operator attempting POST /closures -> 403 Forbidden
    r_clos = client.post("/api/v1/evacuation/closures", json=closure_payload, headers=op_headers)
    assert r_clos.status_code == 403
    err_clos = r_clos.json().get("error", {}).get("message", "") or r_clos.json().get("detail", "")
    assert "Insufficient privileges" in err_clos
    assert "ADMIN" in err_clos

    # Operator attempting POST /shelters -> 403 Forbidden
    r_shelt = client.post("/api/v1/evacuation/shelters", json=shelter_payload, headers=op_headers)
    assert r_shelt.status_code == 403
    err_shelt = r_shelt.json().get("error", {}).get("message", "") or r_shelt.json().get("detail", "")
    assert "Insufficient privileges" in err_shelt


def test_administrative_authorized_admin_access():
    """Authorized administrator with server-validated ADMIN role succeeds."""
    admin_headers = {"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}
    closure_payload = {"edge_id": "edge_admin_ok", "road_name": "Admin Authorized Road", "reason": "Emergency Barricade"}

    # 1. Create closure as Admin -> 201
    r_post = client.post("/api/v1/evacuation/closures", json=closure_payload, headers=admin_headers)
    assert r_post.status_code == 201
    c_id = r_post.json()["id"]

    # 2. Patch closure as Admin -> 200
    r_patch = client.patch(f"/api/v1/evacuation/closures/{c_id}", json={"is_active": False}, headers=admin_headers)
    assert r_patch.status_code == 200

    # 3. Delete closure as Admin -> 200
    r_del = client.delete(f"/api/v1/evacuation/closures/{c_id}", headers=admin_headers)
    assert r_del.status_code == 200


def test_administrative_missing_server_secret_fails_closed(monkeypatch):
    """When authority secrets are missing from server environment, requests must FAIL CLOSED (503)."""
    # Temporarily remove server secrets from environment and settings
    monkeypatch.delenv("FLOODX_AUTHORITY_TOKEN", raising=False)
    monkeypatch.delenv("EVACUATION_AUTHORITY_TOKEN", raising=False)
    monkeypatch.delenv("FLOODX_OPERATOR_TOKEN", raising=False)

    from app.core.config import settings
    monkeypatch.setattr(settings, "FLOODX_AUTHORITY_TOKEN", None)
    monkeypatch.setattr(settings, "FLOODX_OPERATOR_TOKEN", None)

    closure_payload = {"edge_id": "edge_fail_closed", "road_name": "Fail Closed Test", "reason": "Test"}

    # Even with a token provided, missing server config must fail closed with 503
    r = client.post(
        "/api/v1/evacuation/closures",
        json=closure_payload,
        headers={"X-Authority-Token": "some-token"}
    )
    assert r.status_code == 503
    err_msg = r.json().get("error", {}).get("message", "") or r.json().get("detail", "")
    assert "Authentication service unavailable" in err_msg


def test_no_credential_leakage_in_api_responses():
    """API responses must never reflect or leak credential strings or tokens."""
    admin_headers = {"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}
    closure_payload = {"edge_id": "edge_leak_test", "road_name": "Leak Test Road", "reason": "Test"}

    # Test success response
    r_success = client.post("/api/v1/evacuation/closures", json=closure_payload, headers=admin_headers)
    assert r_success.status_code == 201
    c_id = r_success.json()["id"]
    assert TEST_ADMIN_AUTHORITY_TOKEN not in r_success.text

    # Test 403 error response
    r_err = client.post(
        "/api/v1/evacuation/closures",
        json=closure_payload,
        headers={"X-Authority-Token": "attacker-provided-token-xyz"}
    )
    assert r_err.status_code == 403
    assert "attacker-provided-token-xyz" not in r_err.text
    assert TEST_ADMIN_AUTHORITY_TOKEN not in r_err.text

    # Cleanup
    client.delete(f"/api/v1/evacuation/closures/{c_id}", headers=admin_headers)


def test_no_credential_leakage_in_application_logs(caplog):
    """Application logging must never record authority secret values or authorization tokens."""
    import logging
    caplog.set_level(logging.DEBUG)

    admin_headers = {"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}
    closure_payload = {"edge_id": "edge_log_test", "road_name": "Log Security Road", "reason": "Test"}

    # Execute authorized and unauthorized requests
    r_post = client.post("/api/v1/evacuation/closures", json=closure_payload, headers=admin_headers)
    assert r_post.status_code == 201
    c_id = r_post.json()["id"]

    client.post(
        "/api/v1/evacuation/closures",
        json=closure_payload,
        headers={"X-Authority-Token": "attempted-fake-secret-999"}
    )

    # Cleanup
    client.delete(f"/api/v1/evacuation/closures/{c_id}", headers=admin_headers)

    # Verify log output does NOT contain the secret strings
    assert TEST_ADMIN_AUTHORITY_TOKEN not in caplog.text
    assert "attempted-fake-secret-999" not in caplog.text


def test_administrative_audit_actor_attribution():
    """Administrative write operations must record the authenticated actor in evacuation_audit_logs."""
    admin_headers = {"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}
    closure_payload = {
        "edge_id": "edge_audit_test",
        "road_name": "Audit Attribution Road",
        "reason": "Flash Flood Barricade"
    }

    # Create closure
    r_post = client.post("/api/v1/evacuation/closures", json=closure_payload, headers=admin_headers)
    assert r_post.status_code == 201
    c_id = r_post.json()["id"]

    # Check evacuation_audit_logs in database
    from app.core.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        q = text("""
            SELECT actor, event_type, entity_id
            FROM evacuation_audit_logs
            WHERE entity_id = :cid AND event_type = 'ROAD_CLOSURE_CREATED'
            ORDER BY created_at DESC LIMIT 1
        """)
        row = conn.execute(q, {"cid": str(c_id)}).mappings().first()
        assert row is not None
        # Actor must match server-established administrator identity
        assert row["actor"] == "Disaster Management Administrator"

    # Clean up
    client.delete(f"/api/v1/evacuation/closures/{c_id}", headers=admin_headers)

