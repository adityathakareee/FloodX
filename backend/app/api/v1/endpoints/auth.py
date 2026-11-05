"""FastAPI endpoints for Authority Authentication, HttpOnly Session Cookies & CSRF Protection.

FLOOD-X Phase 5.1 Security Hardening.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    AuthorityRole,
    AuthenticatedAuthority,
    authenticate_authority,
    require_admin_authority,
    get_configured_authority_secret,
    get_configured_operator_secret,
    constant_time_compare,
    generate_csrf_token,
    create_signed_session_token,
    revoke_session,
    revoke_session_jti,
    cleanup_expired_revocations,
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    SessionInfoResponse,
    CsrfTokenResponse,
    RevocationCleanupResponse,
)

logger = logging.getLogger("floodx.api.auth")
router = APIRouter(prefix="/auth", tags=["Authority Authentication & Sessions"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    response: Response
) -> LoginResponse:
    """Authenticates municipal authority credentials and establishes a secure HttpOnly session with CSRF protection."""
    admin_secret = get_configured_authority_secret()
    operator_secret = get_configured_operator_secret()

    # Fail closed if authority secrets are missing on the server
    if not admin_secret and not operator_secret:
        logger.error("Authentication rejected: authority secret is not configured in server environment.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable: authority secret configuration is missing."
        )

    provided = payload.token.strip()
    role: Optional[AuthorityRole] = None
    signing_secret: Optional[str] = None
    default_actor: str = "Disaster Management Administrator"

    if admin_secret and constant_time_compare(provided, admin_secret):
        role = AuthorityRole.ADMIN
        signing_secret = admin_secret
        default_actor = payload.actor.strip() if payload.actor and payload.actor.strip() else "Disaster Management Administrator"
    elif operator_secret and constant_time_compare(provided, operator_secret):
        role = AuthorityRole.OPERATOR
        signing_secret = operator_secret
        default_actor = payload.actor.strip() if payload.actor and payload.actor.strip() else "Field Operations Officer"

    if not role or not signing_secret:
        logger.warning("Authority login rejected: invalid credentials provided.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or expired authority credentials."
        )

    # 1. Generate cryptographically signed session token
    session_token = create_signed_session_token(
        actor=default_actor,
        role=role,
        secret_key=signing_secret,
        expires_in_sec=86400
    )

    # 2. Generate CSRF token
    csrf_token = generate_csrf_token()

    is_production = bool(getattr(settings, "ENVIRONMENT", "development").lower() == "production")

    # 3. Set HttpOnly session cookie (inaccessible to JavaScript)
    response.set_cookie(
        key="floodx_session",
        value=session_token,
        max_age=86400,
        httponly=True,
        samesite="lax",
        path="/",
        secure=is_production
    )

    # 4. Set client-accessible CSRF cookie
    response.set_cookie(
        key="floodx_csrf_token",
        value=csrf_token,
        max_age=86400,
        httponly=False,
        samesite="lax",
        path="/",
        secure=is_production
    )

    return LoginResponse(
        status="authenticated",
        actor=default_actor,
        role=role.value,
        csrf_token=csrf_token,
        expires_in=86400,
        token_type="session_cookie"
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    response: Response,
    authority: AuthenticatedAuthority = Depends(authenticate_authority),
    db: Optional[Session] = Depends(get_db)
) -> LogoutResponse:
    """Invalidates the active session persistently in the database and clears HttpOnly authentication and CSRF cookies."""
    # Revoke JTI persistently in PostgreSQL
    if authority.jti:
        exp_dt = None
        if authority.exp:
            exp_dt = datetime.fromtimestamp(authority.exp, timezone.utc)
        revoke_session(
            jti=authority.jti,
            actor=authority.actor,
            role=authority.role.value,
            expires_at=exp_dt,
            reason="LOGOUT",
            db=db
        )

    is_production = bool(getattr(settings, "ENVIRONMENT", "development").lower() == "production")

    # Invalidate cookies
    response.delete_cookie(key="floodx_session", path="/", secure=is_production, httponly=True, samesite="lax")
    response.delete_cookie(key="floodx_csrf_token", path="/", secure=is_production, httponly=False, samesite="lax")

    return LogoutResponse(
        status="logged_out",
        message="Session invalidated successfully."
    )


@router.post("/cleanup-revocations", response_model=RevocationCleanupResponse)
def cleanup_revocations_endpoint(
    authority: AuthenticatedAuthority = Depends(require_admin_authority),
    db: Optional[Session] = Depends(get_db)
) -> RevocationCleanupResponse:
    """Cleans up expired session revocation records from the database (Requires ADMIN token)."""
    cleaned = cleanup_expired_revocations(db=db)
    return RevocationCleanupResponse(
        status="success",
        cleaned_records=cleaned,
        timestamp_utc=datetime.now(timezone.utc).isoformat()
    )


@router.get("/session", response_model=SessionInfoResponse)
def get_current_session(
    authority: AuthenticatedAuthority = Depends(authenticate_authority)
) -> SessionInfoResponse:
    """Returns details of the currently authenticated authority principal."""
    return SessionInfoResponse(
        authenticated=True,
        actor=authority.actor,
        role=authority.role.value,
        token_type=authority.token_type
    )


@router.get("/csrf-token", response_model=CsrfTokenResponse)
def get_csrf_token(
    response: Response
) -> CsrfTokenResponse:
    """Issues a fresh CSRF token and sets the floodx_csrf_token cookie."""
    csrf_token = generate_csrf_token()
    is_production = bool(getattr(settings, "ENVIRONMENT", "development").lower() == "production")

    response.set_cookie(
        key="floodx_csrf_token",
        value=csrf_token,
        max_age=86400,
        httponly=False,
        samesite="lax",
        path="/",
        secure=is_production
    )

    return CsrfTokenResponse(
        csrf_token=csrf_token,
        header_name="X-CSRF-Token",
        cookie_name="floodx_csrf_token"
    )

