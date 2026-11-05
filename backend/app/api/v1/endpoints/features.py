"""REST API endpoints for hydrological feature engineering catalog, summaries, and generation."""
import os
import logging
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.feature import FeatureDataset
from app.schemas.feature import (
    FeatureDatasetResponse,
    FeatureSummaryResponse,
    FeatureGenerationResponse,
)
from app.services.features.orchestrator import FeatureEngineeringOrchestrator

logger = logging.getLogger("floodx.api.features")
router = APIRouter(prefix="/features", tags=["Hydrological Features"])


@router.get("/summary", response_model=FeatureSummaryResponse)
def get_features_summary(db: Session = Depends(get_db)):
    """Retrieves an aggregated summary of all engineered hydrological feature datasets."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    stmt = select(FeatureDataset).order_by(FeatureDataset.id.asc())
    datasets = db.execute(stmt).scalars().all()

    categories: Dict[str, int] = {}
    total_records = 0
    for d in datasets:
        categories[d.category] = categories.get(d.category, 0) + 1
        total_records += d.total_records

    return FeatureSummaryResponse(
        total_feature_sets=len(datasets),
        categories=categories,
        total_records=total_records,
        feature_sets=[FeatureDatasetResponse.model_validate(d) for d in datasets],
    )


@router.get("/datasets", response_model=List[FeatureDatasetResponse])
def get_feature_datasets(
    category: Optional[str] = Query(None, description="Filter by category (RAINFALL, WEATHER, TERRAIN, GEOSPATIAL, INTEGRATED)"),
    db: Session = Depends(get_db),
):
    """Lists cataloged feature datasets with optional category filter."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    stmt = select(FeatureDataset).order_by(FeatureDataset.id.asc())
    if category:
        stmt = stmt.where(FeatureDataset.category == category.upper())

    datasets = db.execute(stmt).scalars().all()
    return [FeatureDatasetResponse.model_validate(d) for d in datasets]


@router.get("/datasets/{name}", response_model=FeatureDatasetResponse)
def get_feature_dataset_by_name(name: str, db: Session = Depends(get_db)):
    """Retrieves metadata and provenance for a specific feature dataset."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    stmt = select(FeatureDataset).where(FeatureDataset.feature_set_name == name)
    dataset = db.execute(stmt).scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Feature dataset '{name}' not found")

    return FeatureDatasetResponse.model_validate(dataset)


@router.get("/rainfall/summary")
def get_rainfall_features_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns detailed summary of CWPRS rolling accumulation windows and CHIRPS spatial stats."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    cwprs = db.execute(
        select(FeatureDataset).where(FeatureDataset.feature_set_name == "CWPRS_RAINFALL_ROLLING_FEATURES")
    ).scalar_one_or_none()

    chirps = db.execute(
        select(FeatureDataset).where(FeatureDataset.feature_set_name == "CHIRPS_DAILY_SPATIAL_FEATURES")
    ).scalar_one_or_none()

    return {
        "status": "AVAILABLE",
        "station": "Khadakwasla Dam (CWPRS)",
        "coordinates": {"lat": 18.4419, "lon": 73.7661},
        "cwprs_rolling_features": {
            "total_records": cwprs.total_records if cwprs else 0,
            "temporal_range": cwprs.temporal_range if cwprs else None,
            "windows": ["15m", "30m", "1h", "3h", "6h", "12h", "24h"],
            "metrics": cwprs.provenance_manifest.get("summary_metrics", {}) if cwprs and cwprs.provenance_manifest else {},
            "quality_notes": cwprs.quality_notes if cwprs else None,
        },
        "chirps_spatial_features": {
            "total_peak_dates": chirps.total_records if chirps else 0,
            "temporal_range": chirps.temporal_range if chirps else None,
            "metrics": chirps.provenance_manifest.get("summary_metrics", {}) if chirps and chirps.provenance_manifest else {},
            "quality_notes": chirps.quality_notes if chirps else None,
        },
    }


@router.get("/weather/summary")
def get_weather_features_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns meteorological metrics: Vapor Pressure Deficit (VPD), soil saturation index, and rolling precip."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    dataset = db.execute(
        select(FeatureDataset).where(FeatureDataset.feature_set_name == "OPEN_METEO_WEATHER_FEATURES")
    ).scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Weather feature dataset not yet generated")

    return {
        "dataset_name": dataset.feature_set_name,
        "total_records": dataset.total_records,
        "temporal_range": dataset.temporal_range,
        "spatial_domain": dataset.spatial_domain,
        "metrics": dataset.provenance_manifest.get("summary_metrics", {}) if dataset.provenance_manifest else {},
        "derived_variables": [
            "vpd_kpa (Vapor Pressure Deficit)",
            "wind_u_ms / wind_v_ms (Velocity vectors)",
            "soil_saturation_index (Volumetric moisture / 0.45 capacity)",
            "rolling_precip_{3h,6h,12h,24h}_mm",
            "runoff_risk_proxy",
        ],
        "quality_notes": dataset.quality_notes,
    }


@router.get("/terrain/summary")
def get_terrain_features_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns Copernicus GLO-90 DSM terrain statistics, depression zones, and roughness indices."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    dataset = db.execute(
        select(FeatureDataset).where(FeatureDataset.feature_set_name == "COPERNICUS_TERRAIN_SAMPLED_FEATURES")
    ).scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Terrain feature dataset not yet generated")

    return {
        "dataset_name": dataset.feature_set_name,
        "total_sampled_locations": dataset.total_records,
        "metrics": dataset.provenance_manifest.get("summary_metrics", {}) if dataset.provenance_manifest else {},
        "methodology": {
            "source_model": "Copernicus GLO-90 DSM (~90m resolution)",
            "focal_window": "5x5 (~450m neighborhood)",
            "depression_definition": "relative_elevation <= 5.0m AND slope <= 3.0 deg",
            "dsm_surface_bias": "Captures urban canopy and building rooftop elevation rather than bare-earth terrain.",
        },
        "quality_notes": dataset.quality_notes,
    }


@router.get("/geospatial/summary")
def get_geospatial_features_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns proximity statistics to rivers, bridges, hospitals, schools, and evacuation corridors."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    dataset = db.execute(
        select(FeatureDataset).where(FeatureDataset.feature_set_name == "POSTGIS_INFRASTRUCTURE_PROXIMITY_FEATURES")
    ).scalar_one_or_none()

    if not dataset:
        raise HTTPException(status_code=404, detail="Geospatial feature dataset not yet generated")

    return {
        "dataset_name": dataset.feature_set_name,
        "total_evaluated_points": dataset.total_records,
        "metrics": dataset.provenance_manifest.get("summary_metrics", {}) if dataset.provenance_manifest else {},
        "infrastructure_layers": [
            "WATERWAY (Mula, Mutha, Pavana)",
            "BRIDGE (Crossings)",
            "HEALTHCARE (Hospitals/Clinics)",
            "EDUCATION (Schools/Colleges)",
            "EVACUATION_ROAD (Arterial Network)",
        ],
        "quality_notes": dataset.quality_notes,
    }


@router.get("/integrated/sample")
def get_integrated_features_sample(
    limit: int = Query(24, ge=1, le=100, description="Number of hourly records to sample"),
    offset: int = Query(0, ge=0, description="Offset from beginning of July 2024 sequence"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Returns sampled hourly records from the July 2024 flood sequence Master Feature Table."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    dataset = db.execute(
        select(FeatureDataset).where(FeatureDataset.feature_set_name == "MULA_MUTHA_JULY2024_ALIGNED_FEATURES")
    ).scalar_one_or_none()

    if not dataset or not dataset.file_path_parquet or not os.path.exists(dataset.file_path_parquet):
        raise HTTPException(status_code=404, detail="Master integrated feature table not available")

    df = pd.read_parquet(dataset.file_path_parquet)
    total_records = len(df)
    subset = df.iloc[offset : offset + limit].copy()

    # Format timestamps for JSON serialization
    if "observation_time" in subset.columns:
        subset["observation_time"] = subset["observation_time"].astype(str)

    # Replace NaNs with None for valid JSON
    records = subset.replace({np.nan: None}).to_dict(orient="records")

    return {
        "total_records": total_records,
        "limit": limit,
        "offset": offset,
        "temporal_range": dataset.temporal_range,
        "local_river_gauge_status": "EXCLUDED (CWC Sangli gauge 205.3 km away is not local)",
        "records": records,
    }


@router.post("/generate", response_model=FeatureGenerationResponse)
def trigger_feature_generation(db: Session = Depends(get_db)):
    """Triggers the full Hydrological Feature Engineering Suite and updates database catalog."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database session unavailable")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    orchestrator = FeatureEngineeringOrchestrator(project_root)

    result = orchestrator.run_all(db)

    return FeatureGenerationResponse(
        status=result["status"],
        duration_seconds=result["duration_seconds"],
        total_datasets=result["total_datasets"],
        manifest_file=result.get("manifest_file"),
        datasets=result["datasets"],
    )
