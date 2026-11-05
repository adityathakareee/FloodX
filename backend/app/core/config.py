"""Centralized application configuration for FLOOD-X Backend.

Loads environment variables with Pydantic Settings and validates defaults.
"""

from typing import List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application identity
    PROJECT_NAME: str = "FLOOD-X Intelligence Engine"
    PROJECT_TAGLINE: str = "PREDICT | PRIORITIZE | PROTECT"
    APP_VERSION: str = "0.1.0-phase0"
    ENVIRONMENT: str = "development"
    PILOT_REGION: str = "Pune / Mula-Mutha River Basin, Maharashtra, India"

    # Server configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # Database configuration (PostgreSQL + PostGIS)
    DATABASE_URL: str = (
        "postgresql+psycopg://floodx_admin:floodx_secret_change_in_prod@localhost:5432/floodx_db"
    )
    DB_POOL_PRE_PING: bool = True
    DB_POOL_TIMEOUT_SECONDS: int = 3
    DB_CONNECT_TIMEOUT_SECONDS: int = 3

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:19006",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    # Administrative Security & Authority Credentials (Phase 3.2 Security Hardening)
    # Loaded exclusively from environment variable; NO hardcoded fallback in production code
    FLOODX_AUTHORITY_TOKEN: Optional[str] = None
    FLOODX_OPERATOR_TOKEN: Optional[str] = None

    @field_validator("FLOODX_AUTHORITY_TOKEN", mode="before")
    @classmethod
    def resolve_authority_token(cls, v: Optional[str]) -> Optional[str]:
        import os
        token = v or os.getenv("FLOODX_AUTHORITY_TOKEN") or os.getenv("EVACUATION_AUTHORITY_TOKEN")
        return token.strip() if token and token.strip() else None

    @field_validator("FLOODX_OPERATOR_TOKEN", mode="before")
    @classmethod
    def resolve_operator_token(cls, v: Optional[str]) -> Optional[str]:
        import os
        token = v or os.getenv("FLOODX_OPERATOR_TOKEN")
        return token.strip() if token and token.strip() else None

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return v

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

