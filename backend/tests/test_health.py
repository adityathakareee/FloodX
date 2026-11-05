"""Tests for /api/v1/health endpoint."""

from unittest.mock import patch
from fastapi.testclient import TestClient


def test_health_endpoint_structure(client: TestClient):
    """Test that /api/v1/health returns valid schema structure."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "app_name" in data
    assert "app_version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert "database" in data

    db_info = data["database"]
    assert "status" in db_info
    assert db_info["status"] in ["connected", "disconnected", "error"]
    assert "database_engine" in db_info


def test_health_degraded_when_database_disconnected(client: TestClient):
    """Test that health endpoint handles disconnected database gracefully with 'degraded' status."""
    with patch("app.api.v1.endpoints.health.check_db_connection") as mock_check:
        mock_check.return_value = (False, 1.25, "Could not connect to server: Connection refused")

        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"]["status"] == "disconnected"
        assert "Connection refused" in data["database"]["error"]


def test_health_healthy_when_database_connected(client: TestClient):
    """Test that health endpoint returns 'healthy' when database responds successfully."""
    with patch("app.api.v1.endpoints.health.check_db_connection") as mock_check:
        mock_check.return_value = (True, 2.34, None)

        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"]["status"] == "connected"
        assert data["database"]["latency_ms"] == 2.34
        assert data["database"]["error"] is None

