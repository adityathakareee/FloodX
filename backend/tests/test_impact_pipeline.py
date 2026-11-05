"""Automated Test Suite for FLOOD-X Phase 5 Flood Impact Assessment & SAR Integration.

Validates:
1. Sentinel-1 SAR flood extent loading and polygon geometries.
2. PostGIS spatial overlay against Healthcare, Education, Bridges, and Roads.
3. Population exposure estimation with explicit demographic uncertainty bounds.
4. Hydraulic bridge submersion ratings (Baba Bhide 15k cfs vs SM Joshi).
5. REST API endpoints: /impact/latest, /impact/assess, /impact/scenarios, /impact/layers.
6. Mandatory scientific disclaimer: SAR detects extent only, never depth.
"""

import pytest
from fastapi.testclient import TestClient
from shapely.geometry import MultiPolygon

from app.services.impact.impact_assessment_service import (
    impact_assessment_service,
    BRIDGE_HYDRAULIC_REGISTRY,
)


class TestImpactAssessmentPipeline:
    """Unit and integration tests for the multi-sector impact engine."""

    def test_sar_flood_extent_loading(self):
        """Verifies Sentinel-1 SAR July 2024 reference footprint loads with valid polygons and unverified analog metadata."""
        poly, meta = impact_assessment_service.load_sar_flood_extent()
        assert isinstance(poly, MultiPolygon)
        assert len(poly.geoms) >= 1
        assert not poly.is_empty
        assert "Analog" in meta["sensor"]
        assert meta["verification_status"].startswith("UNVERIFIED_ILLUSTRATIVE_EXTENT")
        assert meta["backscatter_threshold_db"] is None
        assert meta["slope_cutoff_deg"] == 5.0
        assert meta["permanent_water_masked"] is True

    def test_multi_sector_impact_assessment(self):
        """Verifies full spatial overlay computes demographic exposure as DATA_INSUFFICIENT with null numerical figures."""
        res = impact_assessment_service.assess_impact(hazard_source="OBSERVED_SAR_EXTENT")
        assert res.assessment_id.startswith("impact-")
        assert res.pilot_region.startswith("Pune")
        assert res.population_exposure.data_status == "DATA_INSUFFICIENT"
        assert res.population_exposure.estimated_exposed_population is None
        assert res.population_exposure.lower_bound_estimate is None
        assert res.population_exposure.upper_bound_estimate is None
        assert "withheld" in res.population_exposure.estimation_uncertainty_caveat.lower()
        assert len(res.bridges_impact) == len(BRIDGE_HYDRAULIC_REGISTRY)
        assert res.road_network_impact.total_road_network_km > 0
        assert res.overall_severity in ["LOW", "MODERATE", "SEVERE", "CATASTROPHIC"]
        assert len(res.key_recommendations) >= 3

    def test_bridge_hydraulic_submersion_thresholds(self):
        """Verifies Baba Bhide causeway (15k cfs) submerges while elevated SM Joshi bridge remains safe."""
        # Low flow: 10,000 cfs -> Baba Bhide clear
        low_res = impact_assessment_service.assess_impact(
            hazard_source="SIMULATED_SCENARIO",
            simulated_discharge_cfs=10000.0
        )
        baba_low = next(b for b in low_res.bridges_impact if "Baba Bhide" in b.name)
        assert not baba_low.submerged

        # High discharge: 35,000 cfs (July 2024 Disaster) -> Baba Bhide submerged
        high_res = impact_assessment_service.assess_impact(
            hazard_source="SIMULATED_SCENARIO",
            simulated_discharge_cfs=35000.0
        )
        baba_high = next(b for b in high_res.bridges_impact if "Baba Bhide" in b.name)
        assert baba_high.submerged
        assert baba_high.inundation_risk == "SUBMERGED"

        # SM Joshi bridge should remain passable at 35,000 cfs (threshold is 48,000 cfs)
        sm_joshi = next(b for b in high_res.bridges_impact if "SM Joshi" in b.name)
        assert not sm_joshi.submerged

        # Phase 5.2 Scientific Classifications
        assert baba_high.threshold_classification == "UNVERIFIED_OPERATIONAL_REFERENCE"
        assert baba_high.is_simulated is True
        assert sm_joshi.threshold_classification == "ILLUSTRATIVE_SCENARIO"
        assert sm_joshi.is_simulated is True
        assert high_res.road_network_impact.hazard_evaluation_type == "PROXIMITY_SPATIAL_EVALUATION"
        assert high_res.road_network_impact.confirmed_closed_segments_count == 0
        assert high_res.road_network_impact.distinction_disclaimer is not None
        if len(high_res.healthcare_impact) > 0:
            assert high_res.healthcare_impact[0].exposure_nature == "PROXIMITY_BUFFER_EVALUATION"

    def test_simulated_scenario_scaling(self):
        """Verifies simulated hazard geometry expands with higher discharge and convective rainfall."""
        poly_normal, _ = impact_assessment_service.generate_simulated_flood_extent(
            discharge_cfs=5000.0,
            rain_rate_mmh=5.0
        )
        poly_extreme, _ = impact_assessment_service.generate_simulated_flood_extent(
            discharge_cfs=48000.0,
            rain_rate_mmh=50.0
        )
        assert poly_extreme.area > poly_normal.area

    def test_historical_scenarios_comparison(self):
        """Verifies historical disaster comparisons (July 2024, Aug 2019, Sept 2019)."""
        scenarios_resp = impact_assessment_service.get_historical_scenarios()
        assert scenarios_resp.baseline_scenario.scenario_id == "SCENARIO_BASELINE_NORMAL"
        assert len(scenarios_resp.historical_scenarios) == 3

        jul24 = next(s for s in scenarios_resp.historical_scenarios if s.scenario_id == "EVENT_JULY_2024_PEAK")
        assert jul24.khadakwasla_discharge_cfs == 35574.0
        assert jul24.estimated_exposed_population > 10000

        aug19 = next(s for s in scenarios_resp.historical_scenarios if s.scenario_id == "EVENT_AUGUST_2019_MEGA_FLOOD")
        assert aug19.khadakwasla_discharge_cfs == 45400.0

        sept19 = next(s for s in scenarios_resp.historical_scenarios if s.scenario_id == "EVENT_SEPT_2019_AMBIL_ODHA")
        assert sept19.rainfall_24h_mm == 106.0

    def test_sar_depth_disclaimer_mandatory(self):
        """Ensures that the mandatory scientific disclaimer regarding depth inference is present."""
        res = impact_assessment_service.assess_impact()
        assert "depth" in res.hazard_metadata.depth_inference_disclaimer.lower()
        assert "cannot" in res.hazard_metadata.depth_inference_disclaimer.lower()


class TestImpactAPIEndpoints:
    """REST API endpoint tests for /api/v1/impact."""

    def test_get_latest_impact_endpoint(self, client: TestClient):
        """Tests GET /api/v1/impact/latest."""
        resp = client.get("/api/v1/impact/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert "assessment_id" in data
        assert "population_exposure" in data
        assert "bridges_impact" in data
        assert "road_network_impact" in data
        assert len(data["bridges_impact"]) >= 5

    def test_post_assess_scenario_endpoint(self, client: TestClient):
        """Tests POST /api/v1/impact/assess."""
        payload = {
            "hazard_source": "SIMULATED_SCENARIO",
            "simulated_discharge_cfs": 40000.0,
            "rain_rate_mmh": 30.0,
            "scenario_name": "Test Simulation Run"
        }
        resp = client.post("/api/v1/impact/assess", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_name"] == "Test Simulation Run"
        assert data["overall_severity"] in ["SEVERE", "CATASTROPHIC", "MODERATE"]

    def test_get_scenarios_endpoint(self, client: TestClient):
        """Tests GET /api/v1/impact/scenarios."""
        resp = client.get("/api/v1/impact/scenarios")
        assert resp.status_code == 200
        data = resp.json()
        assert "baseline_scenario" in data
        assert "historical_scenarios" in data
        assert len(data["historical_scenarios"]) == 3

    def test_get_layers_endpoint(self, client: TestClient):
        """Tests GET /api/v1/impact/layers."""
        resp = client.get("/api/v1/impact/layers")
        assert resp.status_code == 200
        data = resp.json()
        assert "flood_extent_geojson" in data
        assert "critical_bridges_geojson" in data
        assert "exposed_infrastructure_geojson" in data
        assert data["flood_extent_geojson"]["type"] == "FeatureCollection"

