"""Data ingestion logging and data quality issue tracking models."""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from app.models.base import Base, utc_now


class DataIngestionLog(Base):
    """Tracks provenance, file ingestion sessions, batch counts, and error states."""
    __tablename__ = "data_ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    ingestion_type = Column(String(50), nullable=False)  # FILE_BATCH, STREAM, MANUAL_TRIGGER
    file_name = Column(String(255), nullable=True)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    records_read = Column(Integer, default=0, nullable=False)
    records_inserted = Column(Integer, default=0, nullable=False)
    records_skipped = Column(Integer, default=0, nullable=False)
    records_failed = Column(Integer, default=0, nullable=False)
    status = Column(String(30), default="RUNNING", nullable=False, index=True)  # RUNNING, COMPLETED, FAILED, PARTIAL
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    source = relationship("DataSource", back_populates="ingestion_logs")

    __table_args__ = (
        Index("ix_ingestion_status_time", "status", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<IngestionLog(id={self.id}, file='{self.file_name}', status='{self.status}', ins={self.records_inserted})>"


class DataQualityIssue(Base):
    """Catalogues documented data quality flags, anomalies, and semantic limitations."""
    __tablename__ = "data_quality_issues"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True, index=True)
    issue_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)  # INFO, WARNING, CRITICAL
    description = Column(Text, nullable=False)
    affected_record_count = Column(Integer, default=0, nullable=False)
    detected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    resolution_status = Column(String(30), default="DOCUMENTED", nullable=False, index=True)  # OPEN, ACKNOWLEDGED, RESOLVED, DOCUMENTED
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    source = relationship("DataSource", back_populates="quality_issues")

    __table_args__ = (
        Index("ix_quality_severity_type", "severity", "issue_type"),
    )

    def __repr__(self) -> str:
        return f"<QualityIssue(id={self.id}, type='{self.issue_type}', sev='{self.severity}', status='{self.resolution_status}')>"

