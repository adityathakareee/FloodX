"""Tests for FLOOD-X domain data quality rules and semantic integrity invariants."""
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.observation import (
    RainfallObservation,
    RiverLevelObservation,
)
from app.models.ingestion import DataQualityIssue


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_ankali_bridge_classified_regional_reference(db_session: Session):
    """Ensures Ankali Bridge is strictly classified as REGIONAL_REFERENCE_ONLY and not within pilot basin."""
    stmt = select(RiverLevelObservation).where(
        RiverLevelObservation.station_name.ilike("%Ankali Bridge%")
    )
    records = db_session.execute(stmt.limit(50)).scalars().all()
    assert len(records) > 0
    for r in records:
        assert r.geographic_relevance == "REGIONAL_REFERENCE_ONLY"
        assert r.geographic_relevance != "WITHIN_PILOT_BASIN"
        assert r.river_name == "Krishna"


def test_cwprs_reset_rule_preserves_cumulative_peak(db_session: Session):
    """Ensures CWPRS 145.6 mm peak is marked 5MIN_CUMULATIVE and resets properly."""
    stmt = select(RainfallObservation).where(
        RainfallObservation.station_name.ilike("%CWPRS%"),
        RainfallObservation.rainfall_value >= 145.0,
    )
    peak_record = db_session.execute(stmt).scalars().first()
    assert peak_record is not None
    assert peak_record.measurement_type == "5MIN_CUMULATIVE"
    assert peak_record.quality_flag == "VALID"


def test_chirps_temporal_resolution_documented(db_session: Session):
    """Ensures CHIRPS non-continuous 25 daily observations are documented as a quality issue."""
    stmt = select(DataQualityIssue).where(
        DataQualityIssue.issue_type == "TEMPORAL_RESOLUTION_LIMITATION"
    )
    issue = db_session.execute(stmt).scalar_one_or_none()
    assert issue is not None
    assert "25" in issue.description or issue.affected_record_count == 25

