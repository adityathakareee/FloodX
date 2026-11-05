"""Automated API test suite for Hydrological Feature REST endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_features_summary():
    """Tests GET /api/v1/features/summary."""
    response = client.get("/api/v1/features/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_feature_sets" in data
    assert data["total_feature_sets"] >= 6
    assert "categories" in data
    assert "RAINFALL" in data["categories"]
    assert "WEATHER" in data["categories"]
    assert "TERRAIN" in data["categories"]
    assert "GEOSPATIAL" in data["categories"]
    assert "INTEGRATED" in data["categories"]


def test_get_feature_datasets_list_and_filter():
    """Tests GET /api/v1/features/datasets with category filter."""
    response = client.get("/api/v1/features/datasets")
    assert response.status_code == 200
    datasets = response.json()
    assert len(datasets) >= 6

    # Test filtering by category
    resp_rain = client.get("/api/v1/features/datasets?category=RAINFALL")
    assert resp_rain.status_code == 200
    rain_sets = resp_rain.json()
    assert len(rain_sets) >= 2
    for s in rain_sets:
        assert s["category"] == "RAINFALL"


def test_get_feature_dataset_by_name():
    """Tests GET /api/v1/features/datasets/{name}."""
    name = "CWPRS_RAINFALL_ROLLING_FEATURES"
    response = client.get(f"/api/v1/features/datasets/{name}")
    assert response.status_code == 200
    data = response.json()
    assert data["feature_set_name"] == name
    assert data["total_records"] == 24211
    assert data["file_path_parquet"] is not None


def test_get_rainfall_features_summary():
    """Tests GET /api/v1/features/rainfall/summary."""
    response = client.get("/api/v1/features/rainfall/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AVAILABLE"
    assert "cwprs_rolling_features" in data
    assert "chirps_spatial_features" in data
    assert data["cwprs_rolling_features"]["total_records"] == 24211


def test_get_weather_features_summary():
    """Tests GET /api/v1/features/weather/summary."""
    response = client.get("/api/v1/features/weather/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_name"] == "OPEN_METEO_WEATHER_FEATURES"
    assert data["total_records"] == 456
    assert "derived_variables" in data


def test_get_terrain_features_summary():
    """Tests GET /api/v1/features/terrain/summary."""
    response = client.get("/api/v1/features/terrain/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_name"] == "COPERNICUS_TERRAIN_SAMPLED_FEATURES"
    assert data["total_sampled_locations"] > 0
    assert "methodology" in data


def test_get_geospatial_features_summary():
    """Tests GET /api/v1/features/geospatial/summary."""
    response = client.get("/api/v1/features/geospatial/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_name"] == "POSTGIS_INFRASTRUCTURE_PROXIMITY_FEATURES"
    assert data["total_evaluated_points"] > 0


def test_get_integrated_features_sample():
    """Tests GET /api/v1/features/integrated/sample."""
    response = client.get("/api/v1/features/integrated/sample?limit=12&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] == 288
    assert data["limit"] == 12
    assert len(data["records"]) == 12
    assert "EXCLUDED" in data["local_river_gauge_status"]

