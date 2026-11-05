"""Tests for GIS & Spatial Infrastructure API endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_get_gis_summary(client: TestClient):
    response = client.get("/api/v1/gis/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_features"] == 1307
    assert data["layer_counts"]["EVACUATION_ROAD"] == 906
    assert data["layer_counts"]["HEALTHCARE"] == 185
    assert data["layer_counts"]["BRIDGE"] == 158
    assert data["layer_counts"]["EDUCATION"] == 30
    assert data["layer_counts"]["WATERWAY"] == 21
    assert data["layer_counts"]["COMMUNITY_CIVIC"] == 7


def test_get_gis_features_pagination(client: TestClient):
    response = client.get("/api/v1/gis/features?limit=15")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1307
    assert len(data["items"]) == 15

    item = data["items"][0]
    assert "feature_type" in item
    assert "geojson" in item
    assert item["geojson"] is not None
    assert "type" in item["geojson"]
    assert "coordinates" in item["geojson"]


def test_get_gis_features_filter_waterways(client: TestClient):
    response = client.get("/api/v1/gis/features?feature_type=WATERWAY")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 21
    for feat in data["items"]:
        assert feat["feature_type"] == "WATERWAY"
        assert feat["geojson"]["type"] in ["LineString", "MultiLineString"]

