"""SQLAlchemy declarative base and shared model mixins for FLOOD-X."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime
from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Standard timestamp mixin for future entity models."""
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    """Abstract base model with primary integer ID and timestamps."""
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
