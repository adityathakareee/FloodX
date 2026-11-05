"""Base class and common infrastructure for FLOOD-X data ingestion services."""
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.data_source import DataSource
from app.models.ingestion import DataIngestionLog, DataQualityIssue

logger = logging.getLogger("floodx.ingestion")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaseIngestionService:
    """Base class providing transactional logging, source cataloging, and quality issue tracking."""

    source_name: str = "BASE_SOURCE"
    source_type: str = "UNKNOWN"
    provider: str = "UNKNOWN"
    description: str = ""
    data_format: str = "UNKNOWN"
    units: Optional[str] = None
    temporal_resolution: Optional[str] = None
    spatial_resolution: Optional[str] = None

    def get_or_create_source(self, db: Session, metadata_json: Optional[Dict[str, Any]] = None) -> DataSource:
        """Retrieves or registers the data source in data_sources."""
        stmt = select(DataSource).where(DataSource.source_name == self.source_name)
        source = db.execute(stmt).scalar_one_or_none()
        if source is None:
            source = DataSource(
                source_name=self.source_name,
                source_type=self.source_type,
                provider=self.provider,
                description=self.description,
                data_format=self.data_format,
                units=self.units,
                temporal_resolution=self.temporal_resolution,
                spatial_resolution=self.spatial_resolution,
                is_active=True,
                metadata_json=metadata_json or {},
            )
            db.add(source)
            db.commit()
            db.refresh(source)
            logger.info("Registered new DataSource: %s (id=%d)", self.source_name, source.id)
        elif metadata_json:
            # Update metadata if provided
            source.metadata_json = {**(source.metadata_json or {}), **metadata_json}
            db.commit()
        return source

    def start_log(self, db: Session, source_id: int, file_name: Optional[str], ingestion_type: str = "FILE_BATCH") -> DataIngestionLog:
        """Initializes a new DataIngestionLog record in RUNNING status."""
        log = DataIngestionLog(
            source_id=source_id,
            ingestion_type=ingestion_type,
            file_name=file_name,
            started_at=utc_now(),
            status="RUNNING",
            records_read=0,
            records_inserted=0,
            records_skipped=0,
            records_failed=0,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def finish_log(
        self,
        db: Session,
        log: DataIngestionLog,
        status: str,
        records_read: int,
        records_inserted: int,
        records_skipped: int,
        records_failed: int,
        error_message: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> DataIngestionLog:
        """Finalizes an ingestion log session with counts and completion timestamp."""
        log.completed_at = utc_now()
        log.status = status
        log.records_read = records_read
        log.records_inserted = records_inserted
        log.records_skipped = records_skipped
        log.records_failed = records_failed
        log.error_message = error_message
        if metadata_json:
            log.metadata_json = metadata_json
        db.commit()
        db.refresh(log)
        logger.info(
            "Finished IngestionLog [%s] for %s: read=%d, inserted=%d, skipped=%d, failed=%d, status=%s",
            log.file_name or "stream",
            self.source_name,
            records_read,
            records_inserted,
            records_skipped,
            records_failed,
            status,
        )
        return log

    def record_quality_issue(
        self,
        db: Session,
        source_id: int,
        issue_type: str,
        severity: str,
        description: str,
        affected_record_count: int = 0,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> DataQualityIssue:
        """Idempotently logs a data quality issue or limitation."""
        stmt = select(DataQualityIssue).where(
            DataQualityIssue.source_id == source_id,
            DataQualityIssue.issue_type == issue_type,
        )
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            existing.affected_record_count = affected_record_count
            existing.description = description
            existing.detected_at = utc_now()
            if metadata_json:
                existing.metadata_json = metadata_json
            db.commit()
            return existing

        issue = DataQualityIssue(
            source_id=source_id,
            issue_type=issue_type,
            severity=severity,
            description=description,
            affected_record_count=affected_record_count,
            detected_at=utc_now(),
            resolution_status="DOCUMENTED",
            metadata_json=metadata_json,
        )
        db.add(issue)
        db.commit()
        db.refresh(issue)
        return issue

