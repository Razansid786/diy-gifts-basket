"""
tests/conftest.py
─────────────────
Shared test fixtures for the DIY Gift Basket test suite.

Provides:
* An in-process async test client (``httpx.AsyncClient``).
* A test database session that rolls back after each test.
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    """
    Async HTTP test client.

    Uses ``httpx.AsyncClient`` with ASGI transport so requests
    are handled in-process (no real HTTP server needed).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
