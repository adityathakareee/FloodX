"""Pytest configuration and shared test fixtures for FLOOD-X Backend."""

import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Configure isolated test authority tokens for test suite execution
TEST_ADMIN_AUTHORITY_TOKEN = "test-sec-admin-token-9876543210"
TEST_OPERATOR_AUTHORITY_TOKEN = "test-sec-operator-token-1234567890"

os.environ["FLOODX_AUTHORITY_TOKEN"] = TEST_ADMIN_AUTHORITY_TOKEN
os.environ["FLOODX_OPERATOR_TOKEN"] = TEST_OPERATOR_AUTHORITY_TOKEN

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Provides a synchronous FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_client_cookies(client: TestClient):
    """Ensures client cookies are cleared before and after each test to prevent session leakage."""
    client.cookies.clear()
    yield
    client.cookies.clear()



@pytest.fixture
def admin_headers() -> dict:
    """Returns headers with valid administrator authority credential."""
    return {"X-Authority-Token": TEST_ADMIN_AUTHORITY_TOKEN}


@pytest.fixture
def operator_headers() -> dict:
    """Returns headers with valid operator (non-admin) authority credential."""
    return {"X-Authority-Token": TEST_OPERATOR_AUTHORITY_TOKEN}
