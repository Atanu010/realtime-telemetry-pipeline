"""Pytest fixtures for the FastAPI backend supporting in-process and external testing."""

import os
import sys
from pathlib import Path
import httpx
import pytest
import pytest_asyncio
from starlette.testclient import TestClient

# Ensure backend root is on sys.path
backend_root = Path(__file__).parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

import server

OPERATOR_KEY = os.environ.get("OPERATOR_KEY", "atanu-telemetry-2026")
AUTH_HEADERS = {"Authorization": f"Bearer {OPERATOR_KEY}"}
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API_URL = f"{BACKEND_URL}/api"

def api_url(path: str = "") -> str:
    return f"{API_URL}{path}"

@pytest.fixture(scope="session")
def backend_url() -> str:
    return BACKEND_URL

@pytest.fixture
def client():
    with TestClient(server.app, base_url="http://testserver/api", headers=AUTH_HEADERS) as c:
        yield c

@pytest_asyncio.fixture
async def aclient():
    transport = httpx.ASGITransport(app=server.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver/api", headers=AUTH_HEADERS, timeout=30.0) as c:
        yield c
