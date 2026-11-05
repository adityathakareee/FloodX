"""Structured logging configuration for FLOOD-X Backend."""

import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures structured root logging with formatted stdout output."""
    log_format = (
        "[%(asctime)s] [%(process)d] [%(levelname)s] "
        "[%(name)s:%(lineno)d] - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S %z"

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    # Suppress overly chatty third-party loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger("floodx")
    logger.info("Logging initialized with level: %s", settings.LOG_LEVEL.upper())
    return logger


logger = logging.getLogger("floodx")

