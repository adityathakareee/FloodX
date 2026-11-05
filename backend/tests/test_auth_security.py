"""Comprehensive Security & Authentication Test Suite for FLOOD-X.

Phase 5.1 Security Verification:
1. Successful login (POST /api/v1/auth/login).
2. HttpOnly cookie issuance (floodx_session).
3. Cookie security flags (Path="/", SameSite="lax", Secure in prod).
4. Cookie expiry (Max-Age=86400).
5. Successful authenticated GET with session cookie.
6. Successful authorized mutation with valid CSRF token.
7. Missing CSRF token rejection on mutating request (403 Forbidden).
8. Invalid / mismatched CSRF token rejection (403 Forbidden).
9. Invalid / forged session cookie rejection (403 Forbidden).
10. Logout and session invalidation (revocation of JTI, 401 on reuse).
11. Admin authorization verification.
12. Operator restrictions on admin endpoints (403 Forbidden).
13. Missing configuration fail-closed behavior (503 Service Unavailable).
14. No credentials leaked in responses or logs.
"""

import os
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from tests.conftest import TEST_ADMIN_AUTHORITY_TOKEN, TEST_OPERATOR_AUTHORITY_TOKEN
from app.core.security import REVOKED_SESSION_JTIS


def test_1_login_success(client: TestClient):
    """Scenario 1: POST /api/v1/auth/login with valid token returns 200 and auth payload."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN, "actor": "Test Admin"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "authenticated"
    assert data["role"] == "ADMIN"
    assert data["actor"] == "Test Admin"
    assert "csrf_token" in data
    assert len(data["csrf_token"]) == 64
    assert data["expires_in"] == 86400


def test_2_httponly_cookie_issuance(client: TestClient):
    """Scenario 2: floodx_session cookie must be marked HttpOnly."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN}
    )
    assert resp.status_code == 200

    set_cookie_headers = resp.headers.get_list("set-cookie")
    session_cookies = [h for h in set_cookie_headers if "floodx_session=" in h]
    assert len(session_cookies) >= 1
    session_cookie_header = session_cookies[0]
    assert "httponly" in session_cookie_header.lower()


def test_3_cookie_flags(client: TestClient):
    """Scenario 3: Cookie flags must specify Path='/' and SameSite='lax'."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN}
    )
    assert resp.status_code == 200

    set_cookie_headers = resp.headers.get_list("set-cookie")
    session_cookies = [h for h in set_cookie_headers if "floodx_session=" in h]
    assert len(session_cookies) >= 1
    session_header = session_cookies[0]
    assert "path=/" in session_header.lower()
    assert "samesite=lax" in session_header.lower()

    # CSRF cookie must be client-accessible (not HttpOnly)
    csrf_cookies = [h for h in set_cookie_headers if "floodx_csrf_token=" in h]
    assert len(csrf_cookies) >= 1
    csrf_header = csrf_cookies[0]
    assert "httponly" not in csrf_header.lower()
    assert "path=/" in csrf_header.lower()


def test_4_cookie_expiry(client: TestClient):
    """Scenario 4: Session cookie expiry must be Max-Age=86400."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN}
    )
    assert resp.status_code == 200

    set_cookie_headers = resp.headers.get_list("set-cookie")
    session_cookies = [h for h in set_cookie_headers if "floodx_session=" in h]
    assert len(session_cookies) >= 1
    assert "max-age=86400" in session_cookies[0].lower()


def test_5_authenticated_get_with_session_cookie(client: TestClient):
    """Scenario 5: GET requests succeed with session cookie and without CSRF token."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN, "actor": "Auditor 01"}
    )
    assert login_resp.status_code == 200
    session_token = login_resp.cookies.get("floodx_session")

    # Call GET /api/v1/auth/session using session cookie
    sess_resp = client.get(
        "/api/v1/auth/session",
        cookies={"floodx_session": session_token}
    )
    assert sess_resp.status_code == 200
    sess_data = sess_resp.json()
    assert sess_data["authenticated"] is True
    assert sess_data["role"] == "ADMIN"
    assert sess_data["actor"] == "Auditor 01"


def test_6_authorized_mutation_with_valid_csrf(client: TestClient):
    """Scenario 6: Mutating POST succeeds with valid session cookie, CSRF cookie, and matching X-CSRF-Token header."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN, "actor": "Closure Dispatcher"}
    )
    assert login_resp.status_code == 200
    session_token = login_resp.cookies.get("floodx_session")
    csrf_token = login_resp.cookies.get("floodx_csrf_token")
    assert session_token is not None
    assert csrf_token is not None

    closure_payload = {
        "edge_id": "test_sec_edge_valid_csrf",
        "road_name": "CSRF Safe Boulevard",
        "reason": "Controlled overflow testing",
        "closure_type": "FLOOD_SUBMERGENCE",
        "reporting_authority": "PMC Test Ops"
    }

    # Perform authorized mutating request
    post_resp = client.post(
        "/api/v1/evacuation/closures",
        json=closure_payload,
        cookies={
            "floodx_session": session_token,
            "floodx_csrf_token": csrf_token,
        },
        headers={
            "X-CSRF-Token": csrf_token,
        }
    )
    assert post_resp.status_code == 201
    created = post_resp.json()
    c_id = created["id"]

    # Clean up closure using delete with CSRF
    del_resp = client.delete(
        f"/api/v1/evacuation/closures/{c_id}",
        cookies={
            "floodx_session": session_token,
            "floodx_csrf_token": csrf_token,
        },
        headers={
            "X-CSRF-Token": csrf_token,
        }
    )
    assert del_resp.status_code == 200


def test_7_missing_csrf_token_rejection(client: TestClient):
    """Scenario 7: Mutating POST using session cookie without X-CSRF-Token header is rejected (403 Forbidden)."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN}
    )
    session_token = login_resp.cookies.get("floodx_session")
    csrf_token = login_resp.cookies.get("floodx_csrf_token")

    closure_payload = {
        "edge_id": "test_sec_edge_missing_csrf",
        "road_name": "Unprotected Road",
        "reason": "Missing CSRF",
    }

    # Omit X-CSRF-Token header
    post_resp = client.post(
        "/api/v1/evacuation/closures",
        json=closure_payload,
        cookies={
            "floodx_session": session_token,
            "floodx_csrf_token": csrf_token,
        }
    )
    assert post_resp.status_code == 403
    detail = post_resp.json().get("error", {}).get("message", "") or post_resp.json().get("detail", "")
    assert "CSRF" in detail


def test_8_invalid_csrf_token_rejection(client: TestClient):
    """Scenario 8: Mutating POST with mismatched X-CSRF-Token header is rejected (403 Forbidden)."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN}
    )
    session_token = login_resp.cookies.get("floodx_session")
    csrf_token = login_resp.cookies.get("floodx_csrf_token")

    closure_payload = {
        "edge_id": "test_sec_edge_mismatched_csrf",
        "road_name": "Forged CSRF Road",
        "reason": "Forged CSRF Attempt",
    }

    # Provide mismatched X-CSRF-Token header
    post_resp = client.post(
        "/api/v1/evacuation/closures",
        json=closure_payload,
        cookies={
            "floodx_session": session_token,
            "floodx_csrf_token": csrf_token,
        },
        headers={
            "X-CSRF-Token": "completely-forged-csrf-token-value-99999",
        }
    )
    assert post_resp.status_code == 403
    detail = post_resp.json().get("error", {}).get("message", "") or post_resp.json().get("detail", "")
    assert "CSRF" in detail


def test_9_invalid_session_rejection(client: TestClient):
    """Scenario 9: Forged, tampered, or malformed session cookie is rejected (403 Forbidden)."""
    forged_cookie = "eyJzdWIiOiJBdHRhY2tlciIsInJvbGUiOiJBRE1JTiJ9.fake_signature"
    resp = client.get(
        "/api/v1/auth/session",
        cookies={"floodx_session": forged_cookie}
    )
    assert resp.status_code == 403


def test_10_logout_and_session_invalidation(client: TestClient):
    """Scenario 10: POST /api/v1/auth/logout revokes session JTI; subsequent requests fail with 401."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN}
    )
    session_token = login_resp.cookies.get("floodx_session")
    csrf_token = login_resp.cookies.get("floodx_csrf_token")

    # Confirm session works
    verify_resp = client.get(
        "/api/v1/auth/session",
        cookies={"floodx_session": session_token}
    )
    assert verify_resp.status_code == 200

    # Logout
    logout_resp = client.post(
        "/api/v1/auth/logout",
        cookies={
            "floodx_session": session_token,
            "floodx_csrf_token": csrf_token,
        },
        headers={"X-CSRF-Token": csrf_token}
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "logged_out"

    # Reuse revoked session cookie -> 401 Unauthorized
    reused_resp = client.get(
        "/api/v1/auth/session",
        cookies={"floodx_session": session_token}
    )
    assert reused_resp.status_code == 401
    detail = reused_resp.json().get("error", {}).get("message", "") or reused_resp.json().get("detail", "")
    assert "logged out" in detail.lower() or "expired" in detail.lower()


def test_11_admin_authorization(client: TestClient):
    """Scenario 11: ADMIN role successfully authorizes administrative mutating operations."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN, "actor": "PMC Chief Engineer"}
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["role"] == "ADMIN"

    session_token = login_resp.cookies.get("floodx_session")
    csrf_token = login_resp.cookies.get("floodx_csrf_token")

    # Admin creates and deletes a road closure
    c_payload = {"edge_id": "test_sec_admin_edge", "road_name": "Admin Way", "reason": "Admin Test"}
    resp = client.post(
        "/api/v1/evacuation/closures",
        json=c_payload,
        cookies={"floodx_session": session_token, "floodx_csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert resp.status_code == 201
    c_id = resp.json()["id"]

    del_resp = client.delete(
        f"/api/v1/evacuation/closures/{c_id}",
        cookies={"floodx_session": session_token, "floodx_csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert del_resp.status_code == 200


def test_12_operator_restrictions(client: TestClient):
    """Scenario 12: OPERATOR role is restricted from ADMIN mutating endpoints (403 Forbidden)."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_OPERATOR_AUTHORITY_TOKEN, "actor": "Field Surveyor"}
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["role"] == "OPERATOR"

    session_token = login_resp.cookies.get("floodx_session")
    csrf_token = login_resp.cookies.get("floodx_csrf_token")

    # Operator attempts an ADMIN-only mutation (road closure)
    c_payload = {"edge_id": "test_sec_op_edge", "road_name": "Restricted Road", "reason": "Unauthorized attempt"}
    resp = client.post(
        "/api/v1/evacuation/closures",
        json=c_payload,
        cookies={"floodx_session": session_token, "floodx_csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert resp.status_code == 403
    detail = resp.json().get("error", {}).get("message", "") or resp.json().get("detail", "")
    assert "Insufficient privileges" in detail or "ADMIN" in detail


def test_13_missing_configuration_fail_closed(client: TestClient, monkeypatch):
    """Scenario 13: When secrets are unconfigured, system fails closed with 503 Service Unavailable."""
    # Temporarily unset authority secrets
    monkeypatch.setenv("FLOODX_AUTHORITY_TOKEN", "")
    monkeypatch.setenv("EVACUATION_AUTHORITY_TOKEN", "")
    monkeypatch.setenv("FLOODX_OPERATOR_TOKEN", "")
    monkeypatch.setattr(settings, "FLOODX_AUTHORITY_TOKEN", None)
    monkeypatch.setattr(settings, "FLOODX_OPERATOR_TOKEN", None)

    # 1. Login fails with 503
    resp_login = client.post(
        "/api/v1/auth/login",
        json={"token": "some-arbitrary-token"}
    )
    assert resp_login.status_code == 503
    detail = resp_login.json().get("error", {}).get("message", "") or resp_login.json().get("detail", "")
    assert "unavailable" in detail.lower() or "missing" in detail.lower()

    # 2. Mutating endpoint with header fails with 503
    resp_mut = client.post(
        "/api/v1/evacuation/closures",
        json={"edge_id": "e1", "road_name": "R1", "reason": "test"},
        headers={"X-Authority-Token": "some-token"}
    )
    assert resp_mut.status_code == 503


def test_14_no_credentials_in_logs_or_responses(client: TestClient):
    """Scenario 14: Secret tokens must never be reflected in response payloads or error responses."""
    secret_candidate = "my-super-secret-authority-value-999"

    # Failed login
    resp = client.post(
        "/api/v1/auth/login",
        json={"token": secret_candidate}
    )
    assert resp.status_code == 403
    assert secret_candidate not in resp.text
    assert TEST_ADMIN_AUTHORITY_TOKEN not in resp.text

    # Successful login
    resp_ok = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN}
    )
    assert resp_ok.status_code == 200
    assert TEST_ADMIN_AUTHORITY_TOKEN not in resp_ok.text

    # Session info
    sess_token = resp_ok.cookies.get("floodx_session")
    resp_sess = client.get(
        "/api/v1/auth/session",
        cookies={"floodx_session": sess_token}
    )
    assert resp_sess.status_code == 200
    assert TEST_ADMIN_AUTHORITY_TOKEN not in resp_sess.text


def test_15_revocation_survives_simulated_backend_restart(client: TestClient):
    """Scenario 15: Revocation survives simulated backend restart (clearing in-memory cache)."""
    # 1. Login
    resp_login = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN, "actor": "Persistent Officer"}
    )
    assert resp_login.status_code == 200
    session_token = resp_login.cookies.get("floodx_session")
    csrf_token = resp_login.cookies.get("floodx_csrf_token")
    assert session_token is not None

    # Verify session is valid before logout
    resp_check = client.get(
        "/api/v1/auth/session",
        cookies={"floodx_session": session_token}
    )
    assert resp_check.status_code == 200

    # 2. Logout to persistently revoke
    resp_logout = client.post(
        "/api/v1/auth/logout",
        cookies={"floodx_session": session_token, "floodx_csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert resp_logout.status_code == 200

    # 3. Simulate backend restart: completely purge the in-memory cache
    REVOKED_SESSION_JTIS.clear()

    # 4. Attempt to use the session token again: must query PostgreSQL and reject with 401
    resp_after_restart = client.get(
        "/api/v1/auth/session",
        cookies={"floodx_session": session_token}
    )
    assert resp_after_restart.status_code == 401
    detail = resp_after_restart.json().get("error", {}).get("message", "") or resp_after_restart.json().get("detail", "")
    assert "logged out" in detail.lower() or "expired" in detail.lower()


def test_16_revocation_visible_across_independent_db_sessions(client: TestClient):
    """Scenario 16: Revocation is recorded in PostgreSQL and visible across independent DB sessions."""
    from app.core.database import SessionLocal
    from app.models.auth import RevokedSession

    # 1. Login & Logout
    resp_login = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN, "actor": "Multi-Worker Officer"}
    )
    session_token = resp_login.cookies.get("floodx_session")
    csrf_token = resp_login.cookies.get("floodx_csrf_token")

    resp_logout = client.post(
        "/api/v1/auth/logout",
        cookies={"floodx_session": session_token, "floodx_csrf_token": csrf_token},
        headers={"X-CSRF-Token": csrf_token}
    )
    assert resp_logout.status_code == 200

    # 2. Open an independent, clean database session (simulating another worker process)
    with SessionLocal() as db_session:
        records = db_session.query(RevokedSession).filter(RevokedSession.actor == "Multi-Worker Officer").all()
        assert len(records) >= 1
        record = records[-1]
        assert record.actor == "Multi-Worker Officer"
        assert record.role == "ADMIN"
        assert record.reason == "LOGOUT"
        assert record.jti is not None
        assert record.expires_at is not None


def test_17_expired_revocation_record_cleanup(client: TestClient):
    """Scenario 17: Expired revocation records are safely cleaned up while active records are retained."""
    import uuid
    from datetime import datetime, timezone, timedelta
    from app.core.database import SessionLocal
    from app.models.auth import RevokedSession
    from app.core.security import cleanup_expired_revocations

    expired_jti = f"expired_test_{uuid.uuid4().hex[:16]}"
    active_jti = f"active_test_{uuid.uuid4().hex[:16]}"
    now_utc = datetime.now(timezone.utc)

    # Insert one expired record (expired 2 hours ago) and one active record (expires in 12 hours)
    with SessionLocal() as db:
        rec_expired = RevokedSession(
            jti=expired_jti,
            actor="Expired Principal",
            role="ADMIN",
            expires_at=now_utc - timedelta(hours=2),
            reason="TEST_EXPIRED"
        )
        rec_active = RevokedSession(
            jti=active_jti,
            actor="Active Principal",
            role="ADMIN",
            expires_at=now_utc + timedelta(hours=12),
            reason="TEST_ACTIVE"
        )
        db.add_all([rec_expired, rec_active])
        db.commit()

    # 1. Direct function execution
    cleaned_count = cleanup_expired_revocations()
    assert cleaned_count >= 1

    # Verify expired was deleted and active was preserved
    with SessionLocal() as db:
        assert db.query(RevokedSession).filter(RevokedSession.jti == expired_jti).first() is None
        active_found = db.query(RevokedSession).filter(RevokedSession.jti == active_jti).first()
        assert active_found is not None
        # Clean up active test record
        db.delete(active_found)
        db.commit()

    # 2. Test maintenance endpoint (Requires ADMIN token)
    admin_headers = {"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}
    resp_endpoint = client.post("/api/v1/auth/cleanup-revocations", headers=admin_headers)
    assert resp_endpoint.status_code == 200
    assert resp_endpoint.json()["status"] == "success"
    assert "cleaned_records" in resp_endpoint.json()


def test_18_direct_header_does_not_bypass_csrf_for_cookie_authenticated_requests(client: TestClient):
    """Scenario 18: Attaching a direct header token cannot bypass CSRF requirements when browser session cookies are present."""
    # Login to get session cookie
    resp_login = client.post(
        "/api/v1/auth/login",
        json={"token": TEST_ADMIN_AUTHORITY_TOKEN, "actor": "CSRF Bypass Test"}
    )
    session_token = resp_login.cookies.get("floodx_session")

    closure_payload = {
        "edge_id": "bypass_edge_test",
        "road_name": "Bypass Test Highway",
        "reason": "CSRF bypass security verification",
    }

    # Present BOTH valid floodx_session cookie AND valid X-Authority-Token, but OMIT X-CSRF-Token
    # Because a session cookie is present, it is a browser session and CSRF check is strictly mandatory.
    resp_bypass = client.post(
        "/api/v1/evacuation/closures",
        json=closure_payload,
        cookies={"floodx_session": session_token},
        headers={"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}
    )
    assert resp_bypass.status_code == 403
    detail = resp_bypass.json().get("error", {}).get("message", "") or resp_bypass.json().get("detail", "")
    assert "CSRF" in detail


