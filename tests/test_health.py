"""
tests/test_health.py
────────────────────
Smoke tests to verify the application starts and basic endpoints work.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """The /health endpoint should return 200 with status 'healthy'."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data


@pytest.mark.asyncio
async def test_openapi_docs_available(client: AsyncClient):
    """The OpenAPI schema should be accessible at /openapi.json."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    # Verify key API paths exist
    assert "/api/v1/auth/register" in data["paths"]
    assert "/api/v1/products/" in data["paths"]
    assert "/api/v1/baskets/" in data["paths"]
    assert "/api/v1/cart/" in data["paths"]
    assert "/api/v1/orders/checkout" in data["paths"]


@pytest.mark.asyncio
async def test_guest_session_generation(client: AsyncClient):
    """POST /api/v1/auth/guest should return a unique session ID."""
    response = await client.post("/api/v1/auth/guest")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["session_id"].startswith("guest_")
