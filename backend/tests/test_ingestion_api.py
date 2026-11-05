"""Tests for Ingestion API endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_get_ingestion_overview(client: TestClient):
    response = client.get("/api/v1/ingestion/overview")
    assert response.status_code == 200
    data = response.json()
    assert "counts" in data
    assert "breakdowns" in data
    assert data["counts"]["data_sources"] >= 6
    assert data["counts"]["rainfall_observations"] > 0
    assert data["counts"]["weather_observations"] > 0
    assert data["counts"]["river_level_observations"] > 0
    assert data["counts"]["spatial_features"] > 0


def test_get_data_sources(client: TestClient):
    response = client.get("/api/v1/ingestion/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 6
    names = [s["source_name"] for s in sources]
    assert "CHIRPS_V3_RAINFALL" in names
    assert "CWPRS_KHADAKWASLA" in names
    assert "OPEN_METEO" in names
    assert "CWC_TELEMETRY" in names
    assert "OPENSTREETMAP_PUNE" in names
    assert "COPERNICUS_GLO90_DEM" in names


def test_get_ingestion_logs(client: TestClient):
    response = client.get("/api/v1/ingestion/logs?limit=10")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) > 0
    assert all("status" in log for log in logs)
    assert any(log["status"] == "COMPLETED" for log in logs)

