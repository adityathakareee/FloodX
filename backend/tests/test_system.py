"""Tests for /api/v1/system/info and root discovery endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test that GET / returns root discovery metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "tagline" in data
    assert "docs" in data
    assert "health" in data
    assert "system_info" in data


def test_system_info_endpoint(client: TestClient):
    """Test that GET /api/v1/system/info returns complete module catalogue."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200

    data = response.json()
    assert data["project_name"] == "FLOOD-X Intelligence Engine"
    assert data["project_tagline"] == "PREDICT | PRIORITIZE | PROTECT"
    assert data["api_version"] == "v1"
    assert data["current_phase"] == "Phase 0: Project Foundation & System Architecture"

    # Verify Pune pilot geography
    assert "pilot_region" in data
    pilot = data["pilot_region"]
    assert "Pune" in pilot["name"]
    assert "Mula-Mutha" in pilot["name"]
    assert pilot["state"] == "Maharashtra, India"
    assert "Mula River" in pilot["rivers"]
    assert "Mutha River" in pilot["rivers"]

    # Verify modules list
    assert "modules" in data
    modules = data["modules"]
    assert len(modules) >= 10

    # Ensure Phase 0 modules are marked foundation_ready and operational
    phase0_modules = [m for m in modules if m["target_phase"] == 0]
    assert len(phase0_modules) == 2
    for m in phase0_modules:
        assert m["status"] == "foundation_ready"
        assert m["is_operational"] is True

    # Ensure future phase modules (Phase 1 to 5) are strictly marked planned and NOT operational
    future_modules = [m for m in modules if m["target_phase"] > 0]
    for m in future_modules:
        assert m["status"] == "planned"
        assert m["is_operational"] is False

