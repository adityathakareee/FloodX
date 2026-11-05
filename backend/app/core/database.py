"""Database session and connection management for FLOOD-X.

Supports PostgreSQL + PostGIS with graceful fallback and connection verification.
"""

import time
import logging
from typing import Generator, Tuple, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger("floodx.database")

# Declarative Base for future SQLAlchemy ORM models
Base = declarative_base()

# Configure SQLAlchemy engine with aggressive connect_timeout to avoid hanging if DB is down
try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        pool_timeout=settings.DB_POOL_TIMEOUT_SECONDS,
        connect_args={
            "connect_timeout": settings.DB_CONNECT_TIMEOUT_SECONDS,
        },
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning("Failed to initialize SQLAlchemy engine at startup: %s", str(e))
    engine = None
    SessionLocal = None


def check_db_connection() -> Tuple[bool, Optional[float], Optional[str]]:
    """Checks the database connection and returns (is_connected, latency_ms, error_msg).

    Never raises an uncaught exception.
    """
    if engine is None:
        return False, None, "Database engine failed to initialize"

    start_time = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return True, latency_ms, None
    except SQLAlchemyError as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        # Extract a clean, safe error message without leaking sensitive credentials
        error_msg = str(exc.orig) if hasattr(exc, "orig") and exc.orig else str(exc)
        # Truncate very long traceback messages
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        logger.debug("Database healthcheck query failed: %s", error_msg)
        return False, latency_ms, error_msg
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        error_msg = f"Unexpected connection error: {str(exc)}"
        if len(error_msg) > 200:
            error_msg = error_msg[:200] + "..."
        logger.debug("Database healthcheck encountered error: %s", error_msg)
        return False, latency_ms, error_msg


def get_db() -> Generator[Optional[Session], None, None]:
    """FastAPI dependency for yielding database sessions.

    Yields None safely if the database is unavailable, preventing 500 crashes
    on endpoints that can operate in degraded mode.
    """
    if SessionLocal is None:
        yield None
        return

    db: Optional[Session] = None
    try:
        db = SessionLocal()
        yield db
    except SQLAlchemyError as exc:
        logger.error("Database session error: %s", str(exc))
        yield None
    finally:
        if db is not None:
            db.close()

