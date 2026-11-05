"""Tests for Data Quality & Audit API endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_get_data_quality_summary(client: TestClient):
    response = client.get("/api/v1/data-quality/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_issues"] >= 6
    assert "HIGH" in data["by_severity"]
    assert "MEDIUM" in data["by_severity"]
    assert "LOW" in data["by_severity"]
    assert len(data["issues"]) >= 6


def test_get_data_quality_issues_filter(client: TestClient):
    response = client.get("/api/v1/data-quality/issues?severity=HIGH")
    assert response.status_code == 200
    issues = response.json()
    assert len(issues) >= 1
    for issue in issues:
        assert issue["severity"] == "HIGH"
        assert issue["issue_type"] == "GEOGRAPHIC_DISPLACEMENT"
        assert "Ankali Bridge" in issue["description"]

