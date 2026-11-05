"""Pydantic schemas for FLOOD-X Authority Session & CSRF Authentication."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Payload to establish an authenticated authority session."""
    token: str = Field(..., description="Authority secret token")
    actor: Optional[str] = Field(None, description="Optional actor identifier or title")


class LoginResponse(BaseModel):
    """Response containing established session metadata and CSRF token."""
    status: str = "authenticated"
    actor: str
    role: str
    csrf_token: str
    expires_in: int = 86400
    token_type: str = "session_cookie"


class LogoutResponse(BaseModel):
    """Confirmation of server-side session revocation."""
    status: str = "logged_out"
    message: str = "Session invalidated successfully."


class SessionInfoResponse(BaseModel):
    """Information regarding current authenticated principal."""
    authenticated: bool
    actor: str
    role: str
    token_type: str


class CsrfTokenResponse(BaseModel):
    """Client-accessible CSRF token payload."""
    csrf_token: str
    header_name: str = "X-CSRF-Token"
    cookie_name: str = "floodx_csrf_token"


class RevocationCleanupResponse(BaseModel):
    """Response returned upon cleanup of expired persistent revocation records."""
    status: str = "success"
    cleaned_records: int
    timestamp_utc: str


