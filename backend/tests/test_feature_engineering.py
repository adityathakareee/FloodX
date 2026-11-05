"""Automated test suite for Hydrological Feature Engineering & Preprocessing formulas and services."""
import os
import pytest
import numpy as np
import pandas as pd

from app.core.database import SessionLocal
from app.services.features.rainfall_features import RainfallFeatureService, ROLLING_WINDOWS
from app.services.features.weather_features import WeatherFeatureService
from app.services.features.terrain_features import TerrainFeatureService
from app.services.features.geospatial_features import GeospatialFeatureService
from app.services.features.temporal_alignment import TemporalAlignmentService


def test_weather_vpd_formula():
    """Verifies Vapor Pressure Deficit (VPD) formula accuracy with physical limits."""
    # At 25°C and 100% RH, VPD must be 0
    vpd_sat = WeatherFeatureService.calculate_vpd_kpa(25.0, 100.0)
    assert pytest.approx(vpd_sat, abs=1e-3) == 0.0

    # At 30°C and 50% RH:
    # e_s = 0.61078 * exp(17.27 * 30 / 267.3) = 4.246 kPa
    # e_a = 4.246 * 0.5 = 2.123 kPa
    # VPD = 2.123 kPa
    vpd_dry = WeatherFeatureService.calculate_vpd_kpa(30.0, 50.0)
    assert 2.0 <= vpd_dry <= 2.3

    # Negative values must be clipped to 0
    vpd_over = WeatherFeatureService.calculate_vpd_kpa(20.0, 105.0)
    assert vpd_over == 0.0


def test_weather_wind_component_decomposition():
    """Verifies meteorological wind speed and direction decomposition into u/v vectors."""
    # Wind from North (0° / 360°) blows South: u = 0, v < 0
    u, v = WeatherFeatureService.calculate_wind_components(36.0, 0.0)
    # 36 km/h = 10 m/s. From North means v = -10 m/s
    assert pytest.approx(u, abs=0.1) == 0.0
    assert pytest.approx(v, abs=0.1) == -10.0

    # Wind from East (90°) blows West: u < 0, v = 0
    u_e, v_e = WeatherFeatureService.calculate_wind_components(36.0, 90.0)
    assert pytest.approx(u_e, abs=0.1) == -10.0
    assert pytest.approx(v_e, abs=0.1) == 0.0

    # Wind from West (270°) blows East: u > 0, v = 0
    u_w, v_w = WeatherFeatureService.calculate_wind_components(36.0, 270.0)
    assert pytest.approx(u_w, abs=0.1) == 10.0
    assert pytest.approx(v_w, abs=0.1) == 0.0


def test_cwprs_feature_generation_and_incomplete_tracking():
    """Verifies CWPRS rolling accumulation, intensity scaling, and incomplete window tracking."""
    db = SessionLocal()
    try:
        svc = RainfallFeatureService()
        result = svc.generate_cwprs_features(db)

        assert result["total_records"] == 24211
        assert os.path.exists(result["file_path_csv"])
        assert os.path.exists(result["file_path_parquet"])

        df = pd.read_parquet(result["file_path_parquet"])

        # Check all window columns exist
        for w_name, w_steps, dur_h in ROLLING_WINDOWS:
            assert f"rolling_sum_{w_name}_mm" in df.columns
            assert f"intensity_{w_name}_mmh" in df.columns
            assert f"window_status_{w_name}" in df.columns
            assert f"completeness_{w_name}_frac" in df.columns

        # Verify initial rows are flagged INCOMPLETE for long windows
        # (e.g. 24h window has 288 steps; row 0 has only 1 step)
        assert df["window_status_24h"].iloc[0] == "INCOMPLETE"
        assert df["completeness_24h_frac"].iloc[0] < 0.1

        # Verify later rows have COMPLETE status when telemetry is dense
        assert df["window_status_1h"].iloc[100] == "COMPLETE"

        # Verify intensity scaling consistency: intensity = sum / duration_hours
        sum_1h = df["rolling_sum_1h_mm"].iloc[100]
        inten_1h = df["intensity_1h_mmh"].iloc[100]
        assert pytest.approx(inten_1h, abs=1e-2) == sum_1h
    finally:
        db.close()


def test_chirps_spatial_daily_features():
    """Verifies CHIRPS spatial statistics, 25 peak dates, and concentration metrics."""
    svc = RainfallFeatureService()
    result = svc.generate_chirps_features()

    assert result["total_records"] == 25
    df = pd.read_parquet(result["file_path_parquet"])

    assert "mean_mm_day" in df.columns
    assert "p90_to_mean_ratio" in df.columns
    assert "spatial_concentration_index" in df.columns
    assert "imd_severity_category" in df.columns

    # Peak July 25, 2024 cloudburst must be categorized as EXTREMELY_HEAVY_RAINFALL
    peak_row = df[df["date"] == "2024-07-25"].iloc[0]
    assert peak_row["max_mm_day"] >= 340.0
    assert peak_row["imd_severity_category"] == "EXTREMELY_HEAVY_RAINFALL"
    assert peak_row["is_cloudburst_epoch"] is True or peak_row["is_cloudburst_epoch"] == 1


def test_terrain_relative_elevation_and_depression_index():
    """Verifies terrain focal analysis, relative elevation (Z - Z_min), and depression classification."""
    svc = TerrainFeatureService()
    result = svc.generate_terrain_features()

    assert result["total_records"] > 0
    df = pd.read_parquet(result["file_path_parquet"])

    assert "elevation_masl" in df.columns
    assert "local_min_elevation_masl" in df.columns
    assert "relative_elevation_m" in df.columns
    assert "is_topographic_depression" in df.columns
    assert "depression_severity_index" in df.columns

    # Relative elevation must be >= 0 everywhere (since Z >= Z_min_local)
    assert (df["relative_elevation_m"] >= -0.01).all()

    # Depression zones must strictly satisfy relative_h <= 5.0 and slope <= 3.0
    dep_rows = df[df["is_topographic_depression"]]
    for _, r in dep_rows.iterrows():
        assert r["relative_elevation_m"] <= 5.0
        assert r["slope_deg"] <= 3.0


def test_postgis_geospatial_proximity_features():
    """Verifies PostGIS ST_Distance calculations to critical infrastructure."""
    db = SessionLocal()
    try:
        svc = GeospatialFeatureService()
        result = svc.generate_geospatial_features(db)

        assert result["total_records"] > 0
        df = pd.read_parquet(result["file_path_parquet"])

        for col in ["dist_waterway_m", "dist_bridge_m", "dist_healthcare_m", "dist_evacuation_road_m"]:
            assert col in df.columns
            # Distances must be non-negative
            assert (df[col].dropna() >= 0.0).all()

        # Sangam confluence must be within 500m of waterway corridor
        sangam = df[df["location_name"].str.contains("Sangam")].iloc[0]
        assert sangam["dist_waterway_m"] <= 500.0
        assert "BUFFER" in sangam["floodplain_zone"]

        # Ensure high hazard river buffer points exist
        high_hazard_points = df[df["floodplain_zone"] == "HIGH_HAZARD_RIVER_BUFFER_100M"]
        assert len(high_hazard_points) > 0
    finally:
        db.close()


def test_master_integrated_flood_sequence_alignment():
    """Verifies Master Integrated Feature Table for July 20-31, 2024 (288 hourly intervals)."""
    db = SessionLocal()
    try:
        svc = TemporalAlignmentService()
        result = svc.generate_aligned_features(db)

        assert result["total_records"] == 288
        df = pd.read_parquet(result["file_path_parquet"])

        # Check continuous 288 hours
        assert len(df) == 288
        assert df["cwprs_rolling_24h_mm"].max() > 0.0

        # Verify Sangli exclusion invariant
        assert (df["local_river_gauge_available"] == False).all()
        assert "CWC Ankali Bridge is in Sangli" in df["river_gauge_exclusion_reason"].iloc[0]

        # Verify CHIRPS satellite data is present on July 25, 2024
        july25_hours = df[df["date_str"] == "2024-07-25"]
        assert (july25_hours["has_chirps_daily"] == True).all()
        assert (july25_hours["chirps_basin_max_mm_day"] >= 340.0).all()

        # Verify CHIRPS is False on non-covered dates (e.g. July 20, 2024)
        july20_hours = df[df["date_str"] == "2024-07-20"]
        assert (july20_hours["has_chirps_daily"] == False).all()
    finally:
        db.close()
