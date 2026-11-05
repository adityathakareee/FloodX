"""Security and Role-Based Authorization Module for FLOOD-X.

Provides secure token verification, cryptographically signed HttpOnly session cookies,
server-side CSRF token generation and validation, constant-time comparison,
server-side role resolution, fail-closed configuration enforcement, and audit actor attribution.
"""

import os
import json
import base64
import time
from datetime import datetime, timezone, timedelta
import hmac
import hashlib
import secrets
import uuid
import logging
from enum import Enum
from typing import Optional, Set
from fastapi import Header, Cookie, HTTPException, status, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger("floodx.security")

# In-memory L1 cache of revoked session JTIs (authoritative ground-truth is persisted in PostgreSQL)
REVOKED_SESSION_JTIS: Set[str] = set()


class AuthorityRole(str, Enum):
    """Server-side authorization roles for FLOOD-X municipal operations."""
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class AuthenticatedAuthority(BaseModel):
    """Authenticated principal with server-established role, actor attribution, and session JTI."""
    actor: str
    role: AuthorityRole
    token_type: str = "authority_token"
    jti: Optional[str] = None
    exp: Optional[int] = None


def get_configured_authority_secret() -> Optional[str]:
    """Retrieves the administrator authority secret from protected environment variables.
    
    Fails closed by returning None if no secret is configured.
    """
    token = os.getenv("FLOODX_AUTHORITY_TOKEN") or os.getenv("EVACUATION_AUTHORITY_TOKEN") or settings.FLOODX_AUTHORITY_TOKEN
    if token and token.strip():
        return token.strip()
    return None


def get_configured_operator_secret() -> Optional[str]:
    """Retrieves the operator/viewer authority secret from protected environment variables.
    
    Fails closed by returning None if no secret is configured.
    """
    token = os.getenv("FLOODX_OPERATOR_TOKEN") or settings.FLOODX_OPERATOR_TOKEN
    if token and token.strip():
        return token.strip()
    return None


def constant_time_compare(val1: Optional[str], val2: Optional[str]) -> bool:
    """Performs constant-time comparison to prevent timing side-channel attacks."""
    if not val1 or not val2:
        return False
    return hmac.compare_digest(val1.encode("utf-8"), val2.encode("utf-8"))


def generate_csrf_token() -> str:
    """Generates a cryptographically strong 32-byte hex CSRF token."""
    return secrets.token_hex(32)


def create_signed_session_token(actor: str, role: AuthorityRole, secret_key: str, expires_in_sec: int = 86400) -> str:
    """Creates an HMAC-SHA256 signed session token encapsulating principal, role, and expiration."""
    now = int(time.time())
    jti = uuid.uuid4().hex
    payload = {
        "sub": actor,
        "role": role.value,
        "iat": now,
        "exp": now + expires_in_sec,
        "jti": jti,
    }
    payload_json = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("utf-8").rstrip("=")
    sig = hmac.new(secret_key.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def is_session_revoked(jti: Optional[str], db: Optional[Session] = None) -> bool:
    """Checks if a session JTI is revoked persistently in PostgreSQL.
    
    Shares revocation state across all backend workers and persists across server restarts.
    """
    if not jti:
        return False

    # Check fast in-memory L1 cache first
    if jti in REVOKED_SESSION_JTIS:
        return True

    # Query PostgreSQL revoked_sessions table
    close_session_on_finish = False
    if db is None:
        try:
            from app.core.database import SessionLocal
            if SessionLocal is not None:
                db = SessionLocal()
                close_session_on_finish = True
        except Exception as e:
            logger.warning("Could not establish DB session to verify revocation: %s", e)
            db = None

    if db is not None:
        try:
            from app.models.auth import RevokedSession
            exists = db.query(RevokedSession.id).filter(RevokedSession.jti == jti).first()
            if exists:
                REVOKED_SESSION_JTIS.add(jti)
                return True
        except Exception as e:
            logger.warning("Error querying revoked_sessions: %s", e)
        finally:
            if close_session_on_finish:
                db.close()

    return False


def revoke_session(
    jti: Optional[str],
    actor: str = "Authenticated Authority",
    role: str = "ADMIN",
    expires_at: Optional[datetime] = None,
    reason: str = "LOGOUT",
    db: Optional[Session] = None,
) -> bool:
    """Persistently revokes a session JTI in PostgreSQL and invalidates in-memory cache."""
    if not jti:
        return False

    REVOKED_SESSION_JTIS.add(jti)

    close_session_on_finish = False
    if db is None:
        try:
            from app.core.database import SessionLocal
            if SessionLocal is not None:
                db = SessionLocal()
                close_session_on_finish = True
        except Exception as e:
            logger.warning("Could not establish DB session to persist revocation: %s", e)
            db = None

    if db is not None:
        try:
            from app.models.auth import RevokedSession
            if expires_at is None:
                expires_at = datetime.now(timezone.utc) + timedelta(days=1)
            elif expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            existing = db.query(RevokedSession).filter(RevokedSession.jti == jti).first()
            if not existing:
                record = RevokedSession(
                    jti=jti,
                    actor=actor,
                    role=role,
                    expires_at=expires_at,
                    reason=reason
                )
                db.add(record)
                db.commit()
            return True
        except Exception as e:
            logger.error("Failed to persist session revocation: %s", e)
            db.rollback()
            return False
        finally:
            if close_session_on_finish:
                db.close()

    return False


def cleanup_expired_revocations(db: Optional[Session] = None) -> int:
    """Safely cleans up persistent revocation records where expires_at < NOW()."""
    close_session_on_finish = False
    if db is None:
        try:
            from app.core.database import SessionLocal
            if SessionLocal is not None:
                db = SessionLocal()
                close_session_on_finish = True
        except Exception:
            db = None

    deleted_count = 0
    if db is not None:
        try:
            from app.models.auth import RevokedSession
            now_dt = datetime.now(timezone.utc)
            deleted_count = db.query(RevokedSession).filter(RevokedSession.expires_at < now_dt).delete()
            db.commit()
            logger.info("Cleaned up %d expired revocation records.", deleted_count)
        except Exception as e:
            logger.error("Failed to clean up expired revocations: %s", e)
            db.rollback()
        finally:
            if close_session_on_finish:
                db.close()
    return deleted_count


def revoke_session_jti(jti: Optional[str]) -> None:
    """Marks a session JTI as revoked (convenience backward compatibility wrapper)."""
    if jti:
        revoke_session(jti=jti)


def decode_and_verify_session_token(
    token_str: str,
    admin_secret: Optional[str],
    operator_secret: Optional[str],
    db: Optional[Session] = None
) -> Optional[AuthenticatedAuthority]:
    """Validates signature, expiration, and persistent revocation status of a signed session token."""
    if not token_str or "." not in token_str:
        return None
    try:
        parts = token_str.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts[0], parts[1]

        matched_secret = None
        matched_role = None

        if admin_secret:
            expected_sig_admin = hmac.new(admin_secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
            if constant_time_compare(sig, expected_sig_admin):
                matched_secret = admin_secret
                matched_role = AuthorityRole.ADMIN

        if not matched_secret and operator_secret:
            expected_sig_op = hmac.new(operator_secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
            if constant_time_compare(sig, expected_sig_op):
                matched_secret = operator_secret
                matched_role = AuthorityRole.OPERATOR

        if not matched_secret or not matched_role:
            return None

        # Decode base64 payload
        padded = payload_b64 + "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_bytes = base64.urlsafe_b64decode(padded)
        payload = json.loads(payload_bytes.decode("utf-8"))

        now = int(time.time())
        exp_ts = payload.get("exp", 0)
        if exp_ts < now:
            logger.warning("Authority session token expired.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please log in again."
            )

        jti = payload.get("jti")
        if jti and is_session_revoked(jti, db=db):
            logger.warning("Revoked authority session token presented.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been logged out."
            )

        return AuthenticatedAuthority(
            actor=payload.get("sub", "Authenticated Authority"),
            role=matched_role,
            token_type="session_cookie",
            jti=jti,
            exp=exp_ts
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Error verifying session token: %s", e)
        return None


def authenticate_authority(
    request: Request,
    x_authority_token: Optional[str] = Header(None, alias="X-Authority-Token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
    floodx_session: Optional[str] = Cookie(None, alias="floodx_session"),
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
    floodx_csrf_token: Optional[str] = Cookie(None, alias="floodx_csrf_token"),
    db: Optional[Session] = Depends(get_db),
) -> AuthenticatedAuthority:
    """Authenticates the incoming request against configured credentials.
    
    Supports:
    1. Direct header token: X-Authority-Token or Authorization: Bearer
    2. HttpOnly session cookie: floodx_session (signed session token)
    
    Security Controls:
    - Persistent database-backed session revocation check across workers and server restarts.
    - Enforces server-side CSRF protection for cookie-authenticated mutating requests (POST, PUT, PATCH, DELETE).
    - If a session cookie is present, direct headers cannot bypass CSRF or role verification.
    - Constant-time signature and token comparison.
    - Fails closed with 503 if server secrets are not configured.
    - Returns 401 if unauthenticated.
    - Returns 403 if token is invalid, rotated, or CSRF check fails.
    - Never logs credentials.
    """
    admin_secret = get_configured_authority_secret()
    operator_secret = get_configured_operator_secret()

    provided_header_token: Optional[str] = None
    if x_authority_token:
        provided_header_token = x_authority_token.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        provided_header_token = authorization[7:].strip()

    has_credentials = bool(provided_header_token or floodx_session)
    if not has_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid authority token via X-Authority-Token header, Bearer token, or floodx_session cookie."
        )

    if not admin_secret and not operator_secret:
        logger.error("Authority authentication failed closed: server authority secret is not configured in environment.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable: authority secret configuration is missing."
        )

    # 1. Check session cookie first if present (used by web browser dashboard)
    # Important: If a browser session cookie is attached, direct headers cannot bypass CSRF enforcement on mutating methods.
    if floodx_session:
        session_val = floodx_session.strip()

        # Check signed session token with persistent database revocation validation
        authority = decode_and_verify_session_token(session_val, admin_secret, operator_secret, db=db)

        # Check raw secret in cookie (backward compatibility fallback)
        if not authority:
            if admin_secret and constant_time_compare(session_val, admin_secret):
                authority = AuthenticatedAuthority(
                    actor="Disaster Management Administrator",
                    role=AuthorityRole.ADMIN,
                    token_type="session_cookie"
                )
            elif operator_secret and constant_time_compare(session_val, operator_secret):
                authority = AuthenticatedAuthority(
                    actor="Field Operations Officer",
                    role=AuthorityRole.OPERATOR,
                    token_type="session_cookie"
                )

        if not authority:
            logger.warning("Authority session cookie rejected: invalid or forged signature.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Invalid or expired authority credentials."
            )

        # Enforce CSRF protection for cookie-authenticated mutating requests (POST, PUT, PATCH, DELETE)
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            if not x_csrf_token or not floodx_csrf_token:
                logger.warning("CSRF validation rejected: missing X-CSRF-Token header or floodx_csrf_token cookie.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: CSRF token missing or invalid."
                )
            if not constant_time_compare(x_csrf_token.strip(), floodx_csrf_token.strip()):
                logger.warning("CSRF validation rejected: X-CSRF-Token header does not match floodx_csrf_token cookie.")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: CSRF token missing or invalid."
                )

        return authority

    # 2. Check direct header token (used by CLI, test fixtures, external pipelines without browser cookies)
    if provided_header_token:
        if admin_secret and constant_time_compare(provided_header_token, admin_secret):
            return AuthenticatedAuthority(
                actor="Disaster Management Administrator",
                role=AuthorityRole.ADMIN,
                token_type="header_token"
            )
        if operator_secret and constant_time_compare(provided_header_token, operator_secret):
            return AuthenticatedAuthority(
                actor="Field Operations Officer",
                role=AuthorityRole.OPERATOR,
                token_type="header_token"
            )
        # Invalid header token -> 403 Forbidden
        logger.warning("Authority authentication rejected: invalid header token provided.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or expired authority credentials."
        )

    # Unauthenticated fallback
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required."
    )


    # Unauthenticated fallback
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required."
    )


def require_admin_authority(
    authority: AuthenticatedAuthority = Depends(authenticate_authority)
) -> AuthenticatedAuthority:
    """Enforces that the authenticated principal possesses the server-established ADMIN role.
    
    Rejects non-admin authenticated users with 403 Forbidden.
    """
    if authority.role != AuthorityRole.ADMIN:
        logger.warning(
            "Authorization rejected: actor '%s' with role '%s' attempted admin action.",
            authority.actor,
            authority.role.value
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Insufficient privileges. Required role: {AuthorityRole.ADMIN.value}."
        )
    return authority
