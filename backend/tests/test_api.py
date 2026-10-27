from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_version() -> None:
    """Test /version endpoint returns application details."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert "TimAI" in data["name"]
        assert "version" in data


@pytest.mark.asyncio
async def test_health_check_healthy() -> None:
    """Test /health endpoint when DB and Redis are connected."""
    with (
        patch("app.main.check_db_connection", new_callable=AsyncMock) as mock_db,
        patch("app.main.check_redis_connection", new_callable=AsyncMock) as mock_redis,
    ):
        mock_db.return_value = True
        mock_redis.return_value = True

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["database"] == "connected"
            assert data["redis"] == "connected"


@pytest.mark.asyncio
async def test_health_check_degraded() -> None:
    """Test /health endpoint when Redis is down."""
    with (
        patch("app.main.check_db_connection", new_callable=AsyncMock) as mock_db,
        patch("app.main.check_redis_connection", new_callable=AsyncMock) as mock_redis,
    ):
        mock_db.return_value = True
        mock_redis.return_value = False

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["redis"] == "disconnected"
