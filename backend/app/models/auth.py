"""SQLAlchemy model for persistent authority session revocation in FLOOD-X.

Provides database-backed session invalidation that survives backend restarts,
shares state across multiple worker processes, and allows automatic cleanup of expired records.
"""

from sqlalchemy import Column, String, DateTime, Index
from app.models.base import BaseModel, utc_now


class RevokedSession(BaseModel):
    """Stores persistently revoked session identifiers (JTIs).
    
    Security & Privacy Design:
    - Never stores raw session tokens or credentials.
    - Stores only the unique cryptographically random JTI (UUID hex).
    - Indexed by JTI for O(1) revocation lookups.
    - Indexed by expires_at for efficient cleanup of stale revocation records.
    """
    __tablename__ = "revoked_sessions"

    jti = Column(String(64), unique=True, index=True, nullable=False)
    actor = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    reason = Column(String(128), nullable=False, default="LOGOUT")

    __table_args__ = (
        Index("ix_revoked_sessions_jti_expires", "jti", "expires_at"),
    )

