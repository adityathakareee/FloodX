"""FLOOD-X Master Feature Engineering CLI Runner.

Executes and catalogs Phase 1 Stage 3 Hydrological Feature Engineering pipelines into PostgreSQL/PostGIS.
"""
import os
import sys
import argparse
import logging
from pprint import pprint

# Ensure backend directory is in python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.database import SessionLocal, check_db_connection
from app.models.feature import FeatureDataset
from app.services.features.orchestrator import FeatureEngineeringOrchestrator
from app.services.features.rainfall_features import RainfallFeatureService
from app.services.features.weather_features import WeatherFeatureService
from app.services.features.terrain_features import TerrainFeatureService
from app.services.features.geospatial_features import GeospatialFeatureService
from app.services.features.temporal_alignment import TemporalAlignmentService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("floodx.cli.features")


def main():
    parser = argparse.ArgumentParser(description="FLOOD-X Hydrological Feature Engineering Runner")
    parser.add_argument(
        "--pipeline",
        choices=["all", "rainfall", "weather", "terrain", "geospatial", "integrated"],
        default="all",
        help="Pipeline to run (default: all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all feature pipelines (alias for --pipeline all)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Only display cataloged feature datasets and metrics",
    )
    args = parser.parse_args()

    if args.all:
        args.pipeline = "all"

    # Check database connection
    is_connected, latency, err = check_db_connection()
    if not is_connected:
        logger.error("Cannot connect to PostgreSQL/PostGIS database: %s", err)
        sys.exit(1)
    logger.info("Connected to database successfully (latency: %.2f ms)", latency)

    db = SessionLocal()
    orchestrator = FeatureEngineeringOrchestrator(PROJECT_ROOT)

    try:
        if args.status:
            logger.info("Retrieving cataloged feature datasets from database...")
            datasets = db.query(FeatureDataset).order_by(FeatureDataset.id.asc()).all()
            if not datasets:
                print("\nNo feature datasets cataloged yet. Run 'python scripts/run_feature_engineering.py' to generate.\n")
            else:
                print(f"\n{'='*75}\nFLOOD-X CATALOGED FEATURE DATASETS ({len(datasets)} sets)\n{'='*75}")
                for ds in datasets:
                    print(f"ID: {ds.id} | Name: {ds.feature_set_name} | Cat: {ds.category}")
                    print(f"  Records: {ds.total_records:,} | Temporal: {ds.temporal_range}")
                    print(f"  Spatial: {ds.spatial_domain}")
                    print(f"  Parquet: {ds.file_path_parquet}")
                    print(f"  CSV:     {ds.file_path_csv}")
                    if ds.provenance_manifest:
                        pm = ds.provenance_manifest
                        print(f"  Parquet SHA256: {pm.get('parquet_sha256', '')[:16]}... ({pm.get('parquet_bytes', 0):,} bytes)")
                    print("-" * 75)
            return

        if args.pipeline == "all":
            result = orchestrator.run_all(db)
            print("\n" + "=" * 75)
            print("FEATURE ENGINEERING SUITE SUMMARY")
            print("=" * 75)
            print(f"Status:            {result['status']}")
            print(f"Duration:          {result['duration_seconds']} seconds")
            print(f"Total Datasets:    {result['total_datasets']}")
            print(f"Manifest:          {result['manifest_file']}")
            print("=" * 75)
            for ds in result["datasets"]:
                name = ds.get("feature_set_name", "UNKNOWN")
                recs = ds.get("total_records", 0)
                err = ds.get("error")
                if err:
                    print(f"[-] {name}: FAILED ({err})")
                else:
                    print(f"[OK] {name}: {recs:,} records generated")

        elif args.pipeline == "rainfall":
            svc = RainfallFeatureService(PROJECT_ROOT)
            cwprs = svc.generate_cwprs_features(db)
            orchestrator._catalog_dataset(db, cwprs)
            chirps = svc.generate_chirps_features()
            orchestrator._catalog_dataset(db, chirps)
            print(f"Generated CWPRS ({cwprs['total_records']} rows) and CHIRPS ({chirps['total_records']} rows)")

        elif args.pipeline == "weather":
            svc = WeatherFeatureService(PROJECT_ROOT)
            w = svc.generate_weather_features(db)
            orchestrator._catalog_dataset(db, w)
            print(f"Generated Weather features ({w['total_records']} rows)")

        elif args.pipeline == "terrain":
            svc = TerrainFeatureService(PROJECT_ROOT)
            t = svc.generate_terrain_features()
            orchestrator._catalog_dataset(db, t)
            print(f"Generated Terrain features ({t['total_records']} rows)")

        elif args.pipeline == "geospatial":
            svc = GeospatialFeatureService(PROJECT_ROOT)
            g = svc.generate_geospatial_features(db)
            orchestrator._catalog_dataset(db, g)
            print(f"Generated Geospatial proximity features ({g['total_records']} rows)")

        elif args.pipeline == "integrated":
            svc = TemporalAlignmentService(PROJECT_ROOT)
            integ = svc.generate_aligned_features(db)
            orchestrator._catalog_dataset(db, integ)
            print(f"Generated Integrated features ({integ['total_records']} rows)")

    finally:
        db.close()


if __name__ == "__main__":
    main()
