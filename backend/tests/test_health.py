"""Tests for health check endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test that health endpoint returns healthy status."""
    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_check_returns_database_field(client: AsyncClient):
    """Test that health endpoint includes database status field."""
    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    # Just verify the database field is present (it may be healthy or report issues)
    assert "database" in data
    assert isinstance(data["database"], str)
