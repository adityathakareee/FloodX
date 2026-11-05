"""Tests for Environmental Data API endpoints (Rainfall, Weather, River Levels)."""
import pytest
from fastapi.testclient import TestClient


def test_get_rainfall_observations(client: TestClient):
    response = client.get("/api/v1/environment/rainfall?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] > 0
    assert len(data["items"]) <= 10

    item = data["items"][0]
    assert "rainfall_value" in item
    assert "rainfall_unit" in item
    assert "measurement_type" in item
    assert "quality_flag" in item


def test_get_rainfall_filtered_chirps(client: TestClient):
    response = client.get("/api/v1/environment/rainfall?measurement_type=DAILY_ACCUMULATION&limit=30")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 25
    for item in data["items"]:
        assert item["measurement_type"] == "DAILY_ACCUMULATION"
        assert item["station_name"] == "CHIRPS_V3_PUNE_BASIN_AGGREGATE"


def test_get_rainfall_summary(client: TestClient):
    response = client.get("/api/v1/environment/rainfall/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["cwprs_24h_cumulative_peak_mm"] == 145.6
    assert data["chirps_basin_daily_peak_mm"] == 162.69


def test_get_weather_observations(client: TestClient):
    response = client.get("/api/v1/environment/weather?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 456
    assert len(data["items"]) <= 10

    # Test filtering by OBSERVED vs FORECAST
    obs_resp = client.get("/api/v1/environment/weather?data_category=OBSERVED")
    assert obs_resp.status_code == 200
    assert obs_resp.json()["total"] == 288

    fc_resp = client.get("/api/v1/environment/weather?data_category=FORECAST")
    assert fc_resp.status_code == 200
    assert fc_resp.json()["total"] == 168


def test_get_river_level_observations(client: TestClient):
    response = client.get("/api/v1/environment/river-levels?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 32655

    # Verify that geographic relevance is strictly REGIONAL_REFERENCE_ONLY
    for item in data["items"]:
        assert item["geographic_relevance"] == "REGIONAL_REFERENCE_ONLY"
        assert item["river_name"] == "Krishna"
        assert "Ankali Bridge" in item["station_name"]
