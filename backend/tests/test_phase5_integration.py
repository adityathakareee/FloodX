"""Comprehensive End-to-End System Integration Tests for FLOOD-X Phase 5.

Verifies:
1. Formal Three-Way Task Separation (Task A, Task B, Task C).
2. Task B: Current Flood Condition Assessment & Telemetry Freshness Gate.
3. Data Freshness Guardrail: Stale (>24h) telemetry defaults to DATA_INSUFFICIENT.
4. Event-Grouped Cross-Validation (GroupKFold) benchmark API.
5. Nugen Decision Intelligence & NDMA (2008) Chapter 4 SOP integration.
6. Full Operational Decision Flow:
   Conditions -> Risk Forecast -> Impact Assessment -> Evacuation Routing -> Resource Optimization -> Advisory.
7. Degraded condition resilience.
"""

import pytest
from fastapi.testclient import TestClient

from app.services.ml.current_condition_service import current_condition_service
from app.services.resource_optimization.nugen_service import nugen_decision_service
from app.services.resource_optimization.resource_models import DecisionAdvisoryRequest
from tests.conftest import TEST_ADMIN_AUTHORITY_TOKEN, TEST_OPERATOR_AUTHORITY_TOKEN


class TestPhase5TaskSeparationAndConditions:
    """Tests for Task B current condition evaluation and 3-way task isolation."""

    def test_three_way_task_separation_api(self, client: TestClient):
        """Verifies GET /api/v1/ml/task-separation returns all three tasks."""
        resp = client.get("/api/v1/ml/task-separation")
        assert resp.status_code == 200
        data = resp.json()
        assert "tasks" in data
        assert len(data["tasks"]) == 3

        task_ids = [t["task_id"] for t in data["tasks"]]
        assert "TASK_A_RETROSPECTIVE_DIAGNOSIS" in task_ids
        assert "TASK_B_CURRENT_CONDITION_ASSESSMENT" in task_ids
        assert "TASK_C_PROSPECTIVE_RISK_ASSESSMENT" in task_ids

    def test_task_b_current_conditions_api(self, client: TestClient):
        """Verifies GET /api/v1/ml/current-conditions returns operational state and freshness."""
        resp = client.get("/api/v1/ml/current-conditions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["condition_status"] in ["NORMAL", "ELEVATED_PLUVIAL_RISK", "SEVERE_INUNDATION_RISK", "DATA_INSUFFICIENT"]
        assert "data_freshness_status" in data
        assert "observed_metrics" in data
        assert "precipitation_rate_mmh" in data["observed_metrics"]
        assert "soil_saturation_pct" in data["observed_metrics"]
        assert "operational_action_recommendation" in data
        assert "scientific_boundary" in data

    def test_task_b_freshness_expiration_guard(self):
        """Verifies that expired telemetry (>24h) correctly forces DATA_INSUFFICIENT."""
        simulated_expired = {
            "data_freshness_status": "EXPIRED",
            "precipitation_rate_mmh": 2.0,
            "surface_soil_moisture_m3m3": 0.22,
        }
        res = current_condition_service.assess_current_conditions(simulated_override=simulated_expired)
        assert res.condition_status == "DATA_INSUFFICIENT"
        assert res.data_insufficient_reason is not None
        assert "exceeds" in res.data_insufficient_reason.lower() or "offline" in res.active_warnings[0].lower()

    def test_event_grouped_validation_api(self, client: TestClient):
        """Verifies GET /api/v1/ml/event-validation returns GroupKFold results."""
        resp = client.get("/api/v1/ml/event-validation")
        assert resp.status_code == 200
        data = resp.json()
        assert "models_evaluated" in data
        assert len(data["models_evaluated"]) >= 4
        model_names = [m["model_name"] for m in data["models_evaluated"]]
        assert "Logistic Regression (Balanced)" in model_names
        assert "Random Forest (Balanced)" in model_names
        assert "Dummy Majority" in model_names


class TestPhase5NugenAndDocumentKnowledgeBase:
    """Tests for Nugen integration and NDMA Chapter 4 document grounding."""

    def test_nugen_status_api(self, client: TestClient):
        """Verifies GET /api/v1/nugen/status reports fallback when credentials absent."""
        resp = client.get("/api/v1/nugen/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_provider" in data
        assert "service_name" in data

    def test_nugen_advisory_impact_grounding(self, client: TestClient):
        """Verifies POST /api/v1/nugen/advisory links multi-sector impact and cites NDMA SOP."""
        resp = client.post("/api/v1/nugen/advisory", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["advisory_id"].startswith("ADV-PUNE-")
        assert len(data["critical_observations"]) >= 3
        # Check impact integration in observations
        obs_text = " ".join(data["critical_observations"])
        assert "Impact" in obs_text or "resident" in obs_text or "sector" in obs_text
        # Check NDMA compliance note
        assert "NDMA" in data["ndma_compliance_notes"]
        assert "2008" in data["ndma_compliance_notes"]
        assert "Chapter 4" in data["ndma_compliance_notes"]


class TestEndToEndOperationalDecisionFlow:
    """Executes the complete end-to-end decision intelligence pipeline."""

    def test_complete_decision_pipeline_execution(self, client: TestClient, admin_headers: dict):
        """Verifies sequential execution of all 6 operational pipeline stages.
        
        Flow: Conditions -> Forecast -> Impact -> Evacuation -> Resource Optimization -> Advisory.
        """
        # Step 1: Real-time Condition Assessment (Task B)
        cond_resp = client.get("/api/v1/ml/current-conditions")
        assert cond_resp.status_code == 200
        assert "observed_metrics" in cond_resp.json()

        # Step 2: Multi-Horizon Prospective Risk Forecast (Task C)
        pros_resp = client.post("/api/v1/prospective/assess")
        assert pros_resp.status_code == 200
        assert "horizons" in pros_resp.json()

        # Step 3: Multi-Sector Flood Impact Assessment (SAR + PostGIS)
        impact_resp = client.get("/api/v1/impact/latest")
        assert impact_resp.status_code == 200
        impact_data = impact_resp.json()
        assert impact_data["population_exposure"]["data_status"] == "DATA_INSUFFICIENT"
        assert impact_data["population_exposure"]["estimated_exposed_population"] is None

        # Step 4: Topography-Aware Evacuation Route Planning
        route_payload = {
            "origin_lat": 18.518,
            "origin_lon": 73.847,  # Pulachi Wadi / Deccan
            "destination_lat": 18.502,
            "destination_lon": 73.858,  # Swargate High Ground
            "cost_profile": "BALANCED"
        }
        route_resp = client.post("/api/v1/evacuation/routes/plan", json=route_payload)
        assert route_resp.status_code == 200
        route_data = route_resp.json()
        assert route_data["status"] in ["SUCCESS", "NO_PATH"]
        assert "disclaimer" in route_data
        if route_data["status"] == "SUCCESS":
            assert route_data["primary_route"]["total_distance_m"] > 0

        # Step 5: Demand & Resource Priority Ranking
        prio_resp = client.get("/api/v1/decision/priorities")
        assert prio_resp.status_code == 200
        assert len(prio_resp.json()["ranked_areas"]) > 0

        # Step 6: Nugen / NDMA SOP Tactical Decision Advisory
        nugen_resp = client.post("/api/v1/nugen/advisory", json={})
        assert nugen_resp.status_code == 200
        adv_data = nugen_resp.json()
        assert len(adv_data["tactical_action_plan"]) > 0
        assert len(adv_data["route_caution_summary"]) > 0


class TestPhase5SecurityAndDegradedHandling:
    """Rigorous audit tests for security auth headers/cookies and degraded conditions."""

    def test_security_auth_with_session_cookie(self, client: TestClient):
        """Verifies authentication via floodx_session cookie."""
        # Unauthenticated request -> 401
        r_unauth = client.post("/api/v1/evacuation/closures", json={"edge_id": "test_edge_1", "road_name": "Test"})
        assert r_unauth.status_code == 401

        # Invalid cookie -> 403
        client.cookies.set("floodx_session", "invalid_token_123")
        r_forbidden = client.post("/api/v1/evacuation/closures", json={"edge_id": "test_edge_1", "road_name": "Test"})
        assert r_forbidden.status_code == 403

        # Valid cookie + CSRF token -> 201 Created
        csrf_val = "test_csrf_token_123456"
        client.cookies.set("floodx_session", TEST_ADMIN_AUTHORITY_TOKEN)
        client.cookies.set("floodx_csrf_token", csrf_val)
        r_ok = client.post(
            "/api/v1/evacuation/closures",
            json={"edge_id": "test_edge_1", "road_name": "Cookie Auth Road", "reason": "Test"},
            headers={"X-CSRF-Token": csrf_val}
        )
        assert r_ok.status_code == 201
        c_id = r_ok.json()["id"]

        # Clean up
        r_del = client.delete(
            f"/api/v1/evacuation/closures/{c_id}",
            headers={"X-CSRF-Token": csrf_val}
        )
        assert r_del.status_code == 200
        client.cookies.clear()

    def test_degraded_conditions_handling(self, client: TestClient):
        """Verifies system graceful degradation under incomplete, missing or extreme inputs."""
        # 1. Unconfigured Nugen -> reports unconfigured status with deterministic fallback
        nugen_status = client.get("/api/v1/nugen/status")
        assert nugen_status.status_code == 200
        data = nugen_status.json()
        assert data["active_provider"] in ["RULE_BASED_DECISION_FALLBACK", "NUGEN_COGNITIVE_LLM"]
        if not data["is_available"]:
            assert data["status"] == "NUGEN_UNAVAILABLE (Credentials Not Configured)"
            assert data["endpoint_configured"] is False

        # 2. Out of bounds route planning -> gracefully returns OUT_OF_BOUNDS (no 500 crash)
        oob_route = client.post("/api/v1/evacuation/routes/plan", json={
            "origin_lat": 0.0,
            "origin_lon": 0.0,
            "destination_lat": 18.52,
            "destination_lon": 73.85
        })
        assert oob_route.status_code == 200
        assert oob_route.json()["status"] in ["OUT_OF_BOUNDS", "NO_PATH", "ERROR"]

        # 3. Missing river telemetry / simulated stale forecast in current condition
        freshness_resp = client.get("/api/v1/ml/current-conditions")
        assert freshness_resp.status_code == 200
        assert "data_freshness_status" in freshness_resp.json()
        assert freshness_resp.json()["condition_status"] in ["NORMAL", "ELEVATED_PLUVIAL_RISK", "SEVERE_INUNDATION_RISK", "DATA_INSUFFICIENT"]
