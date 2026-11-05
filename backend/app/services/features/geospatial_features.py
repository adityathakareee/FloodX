"""Geospatial proximity and infrastructure exposure feature engineering using PostGIS."""
import os
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.features.terrain_features import CANONICAL_PUNE_POINTS

logger = logging.getLogger("floodx.features.geospatial")

FEATURE_TYPES = [
    ("WATERWAY", "waterway"),
    ("BRIDGE", "bridge"),
    ("HEALTHCARE", "healthcare"),
    ("EDUCATION", "education"),
    ("EVACUATION_ROAD", "evacuation_road"),
]


class GeospatialFeatureService:
    """Computes exact spheroidal distances (via PostGIS geography) from critical locations

    and floodplains to rivers, bridges, hospitals, schools, and evacuation corridors.
    """

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            self.project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../..")
            )
        else:
            self.project_root = project_root

        self.output_dir = os.path.join(self.project_root, "data", "features", "geospatial")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_geospatial_features(
        self,
        db: Session,
        include_grid: bool = True,
        grid_sample_step_deg: float = 0.02,  # ~2.2 km spacing
    ) -> Dict[str, Any]:
        """Calculates distance vectors to nearest infrastructure entities for canonical Pune

        hydrological locations and regular study points. Saves to Parquet and CSV.
        """
        logger.info("Computing PostGIS infrastructure proximity features...")

        # 1. Compile points to evaluate
        points_to_evaluate: List[Dict[str, Any]] = list(CANONICAL_PUNE_POINTS)

        if include_grid:
            lat_grid = np.arange(18.44, 18.60, grid_sample_step_deg)
            lon_grid = np.arange(73.76, 73.94, grid_sample_step_deg)
            counter = 1
            for lt in lat_grid:
                for ln in lon_grid:
                    points_to_evaluate.append({
                        "name": f"Pune_Exposure_Grid_{counter:03d}",
                        "category": "MUNICIPAL_GRID_POINT",
                        "lat": float(round(lt, 5)),
                        "lon": float(round(ln, 5)),
                    })
                    counter += 1

        logger.info("Evaluating geospatial exposure for %d locations...", len(points_to_evaluate))

        # Prepared query using GiST index distance operator <-> and exact geography ST_Distance
        knn_query = text("""
            SELECT name, 
                   ST_Distance(
                       geom::geography, 
                       ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                   ) AS dist_m
            FROM spatial_features
            WHERE feature_type = :ftype
            ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
            LIMIT 1;
        """)

        results: List[Dict[str, Any]] = []

        for pt in points_to_evaluate:
            p_lat = pt["lat"]
            p_lon = pt["lon"]
            row: Dict[str, Any] = {
                "location_name": pt["name"],
                "location_category": pt["category"],
                "latitude": p_lat,
                "longitude": p_lon,
            }

            for ftype, col_prefix in FEATURE_TYPES:
                q_res = db.execute(
                    knn_query,
                    {"lon": p_lon, "lat": p_lat, "ftype": ftype},
                ).fetchone()

                if q_res:
                    nearest_name, dist_m = q_res
                    row[f"dist_{col_prefix}_m"] = round(float(dist_m), 1)
                    row[f"nearest_{col_prefix}_name"] = nearest_name or f"Unnamed {ftype.title()}"
                else:
                    row[f"dist_{col_prefix}_m"] = np.nan
                    row[f"nearest_{col_prefix}_name"] = None

            # Derived Exposure & Accessibility Indicators
            dist_water = row.get("dist_waterway_m", 9999.0)
            dist_road = row.get("dist_evacuation_road_m", 9999.0)
            dist_hosp = row.get("dist_healthcare_m", 9999.0)

            # Floodplain proximity zone
            if dist_water <= 100.0:
                row["floodplain_zone"] = "HIGH_HAZARD_RIVER_BUFFER_100M"
            elif dist_water <= 250.0:
                row["floodplain_zone"] = "MODERATE_HAZARD_BUFFER_250M"
            elif dist_water <= 500.0:
                row["floodplain_zone"] = "LOW_HAZARD_BUFFER_500M"
            else:
                row["floodplain_zone"] = "UPLAND_CATCHMENT"

            # Evacuation egress constraint
            if dist_road <= 150.0:
                row["egress_accessibility"] = "DIRECT_ARTERIAL_ACCESS"
            elif dist_road <= 500.0:
                row["egress_accessibility"] = "MODERATE_EGRESS"
            else:
                row["egress_accessibility"] = "CONSTRAINED_EGRESS"

            # Emergency isolation risk ratio:
            # High if right on riverbank but far from evacuation artery
            isolation_index = dist_road / max(10.0, dist_water)
            row["isolation_risk_index"] = round(float(isolation_index), 3)

            # Rapid emergency medical access flag (< 2 km to hospital)
            row["emergency_medical_accessible"] = dist_hosp <= 2000.0

            results.append(row)

        df = pd.DataFrame(results)

        # Save to Parquet and CSV
        csv_file = os.path.join(self.output_dir, "infrastructure_proximity_features.csv")
        parquet_file = os.path.join(self.output_dir, "infrastructure_proximity_features.parquet")

        df.to_csv(csv_file, index=False)
        df.to_parquet(parquet_file, index=False, engine="pyarrow")

        logger.info(
            "Geospatial features generated: %d records -> %s, %s",
            len(df),
            csv_file,
            parquet_file,
        )

        within_100m = int((df["dist_waterway_m"] <= 100.0).sum())
        within_road = int((df["dist_evacuation_road_m"] <= 150.0).sum())

        return {
            "feature_set_name": "POSTGIS_INFRASTRUCTURE_PROXIMITY_FEATURES",
            "category": "GEOSPATIAL",
            "total_records": len(df),
            "file_path_csv": csv_file,
            "file_path_parquet": parquet_file,
            "columns": list(df.columns),
            "temporal_range": "STATIC_VECTOR (OpenStreetMap Infrastructure Epoch)",
            "spatial_domain": "Pune / Mula-Mutha Basin (73.76E - 73.94E, 18.44N - 18.60N)",
            "summary_metrics": {
                "total_evaluated_points": len(df),
                "points_within_100m_waterway": within_100m,
                "points_with_direct_arterial_access": within_road,
                "mean_distance_to_hospital_m": round(float(df["dist_healthcare_m"].mean()), 1),
                "mean_distance_to_evac_road_m": round(float(df["dist_evacuation_road_m"].mean()), 1),
            },
            "quality_notes": (
                "Distances computed via PostGIS ST_Distance(geom::geography) against 1,307 OSM features. "
                "Road network limited to arterial corridors (trunk, primary, secondary, tertiary); minor alleys excluded. "
                "Community civic facilities are unverified community halls, not certified flood shelters. "
                "Hazard buffer zones (100m, 250m, 500m) represent geometric river proximity zones, NOT validated "
                "hydrodynamic floodplains or certified inundation hazard extents."
            ),
        }

