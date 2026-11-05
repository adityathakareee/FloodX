"""FLOOD-X Master Data Ingestion CLI Runner.

Executes and verifies Phase 1 Stage 2 data ingestion pipelines into PostgreSQL/PostGIS.
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
from app.services.ingestion.orchestrator import IngestionOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("floodx.cli.ingestion")


def main():
    parser = argparse.ArgumentParser(description="FLOOD-X Data Ingestion Pipeline Runner")
    parser.add_argument(
        "--source",
        choices=["all", "chirps", "cwprs", "open_meteo", "cwc", "osm", "elevation"],
        default="all",
        help="Specify source to ingest or 'all' for full pipeline",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run in fast mode (sample 1,000 rows for high-volume telemetry)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Only display current ingestion and database statistics",
    )
    args = parser.parse_args()

    # Check DB connectivity
    is_connected, latency, err = check_db_connection()
    if not is_connected:
        logger.error("Cannot connect to PostgreSQL/PostGIS database: %s", err)
        sys.exit(1)
    logger.info("Connected to database successfully (latency: %.2f ms)", latency)

    orchestrator = IngestionOrchestrator()
    db = SessionLocal()

    try:
        if args.status:
            logger.info("Retrieving database ingestion overview...")
            overview = orchestrator.get_overview(db)
            pprint(overview)
            return

        if args.source == "all":
            logger.info("Running all ingestion pipelines (fast_mode=%s)...", args.fast)
            res = orchestrator.run_all(db, fast_mode=args.fast)
            logger.info("Ingestion complete. Overview:")
            pprint(res["overview"])
        else:
            logger.info("Running pipeline for source: %s...", args.source)
            res = orchestrator.run_source(db, args.source)
            logger.info("Source run complete:")
            pprint(res)
            logger.info("Updated overview:")
            pprint(orchestrator.get_overview(db))

    finally:
        db.close()


if __name__ == "__main__":
    main()

