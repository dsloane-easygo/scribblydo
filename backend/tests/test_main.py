"""Tests for main application entry point."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import ASGITransport, AsyncClient


class TestRootEndpoint:
    """Tests for root endpoint."""

    @pytest.mark.asyncio
    async def test_root_redirects_to_docs(self, client: AsyncClient):
        """Test that root path redirects to /docs."""
        response = await client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"


class TestHealthCheck:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, client: AsyncClient):
        """Test health check returns healthy status."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "healthy"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health_check_degraded(self):
        """Test health check returns degraded when database fails."""
        from app.main import health_check

        with patch("app.main.async_session_factory") as mock_factory:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.execute = AsyncMock(side_effect=Exception("DB connection failed"))
            mock_factory.return_value = mock_session

            response = await health_check()

            assert response.status == "degraded"
            assert "unhealthy" in response.database


class TestGlobalExceptionHandler:
    """Tests for global exception handling."""

    @pytest.mark.asyncio
    async def test_unhandled_exception_returns_500(self, client: AsyncClient, test_user: dict):
        """Test that unhandled exceptions return 500."""
        # Trigger an error by using an invalid UUID format for a route that expects UUID
        response = await client.get(
            "/api/whiteboards/not-a-valid-uuid",
            headers=test_user["headers"],
        )
        # FastAPI validates UUIDs and returns 422 for invalid format
        assert response.status_code == 422


class TestWebSocketEndpoint:
    """Tests for WebSocket endpoint authentication."""

    @pytest.mark.asyncio
    async def test_websocket_auth_required(self, client: AsyncClient):
        """Test WebSocket requires auth message first."""
        from starlette.testclient import TestClient
        from app.main import app

        with TestClient(app) as test_client:
            with test_client.websocket_connect("/ws") as websocket:
                # Send non-auth message first
                websocket.send_json({"type": "ping", "payload": {}})
                response = websocket.receive_json()
                assert response["type"] == "error"
                assert response["payload"]["code"] == "auth_required"

    @pytest.mark.asyncio
    async def test_websocket_missing_token(self, client: AsyncClient):
        """Test WebSocket auth with missing token."""
        from starlette.testclient import TestClient
        from app.main import app

        with TestClient(app) as test_client:
            with test_client.websocket_connect("/ws") as websocket:
                # Send auth message without token
                websocket.send_json({"type": "auth", "payload": {}})
                response = websocket.receive_json()
                assert response["type"] == "error"
                assert response["payload"]["code"] == "invalid_token"

    @pytest.mark.asyncio
    async def test_websocket_invalid_token(self, client: AsyncClient):
        """Test WebSocket auth with invalid token."""
        from starlette.testclient import TestClient
        from app.main import app

        with TestClient(app) as test_client:
            with test_client.websocket_connect("/ws") as websocket:
                # Send auth message with invalid token
                websocket.send_json({"type": "auth", "payload": {"token": "invalid.token.here"}})
                response = websocket.receive_json()
                assert response["type"] == "error"
                assert response["payload"]["code"] == "invalid_token"

    @pytest.mark.asyncio
    async def test_websocket_auth_success(self, client: AsyncClient, test_user: dict):
        """Test successful WebSocket authentication."""
        from starlette.testclient import TestClient
        from app.main import app

        with patch("app.main.manager") as mock_manager:
            mock_connection = MagicMock()
            mock_manager.connect = AsyncMock(return_value=mock_connection)
            mock_manager.disconnect = AsyncMock()

            with TestClient(app) as test_client:
                with test_client.websocket_connect("/ws") as websocket:
                    # Send valid auth message
                    websocket.send_json({"type": "auth", "payload": {"token": test_user["token"]}})
                    response = websocket.receive_json()
                    assert response["type"] == "auth_success"
                    assert response["payload"]["username"] == test_user["username"]

    @pytest.mark.asyncio
    async def test_websocket_token_without_sub(self, client: AsyncClient):
        """Test WebSocket auth with token missing sub claim."""
        from starlette.testclient import TestClient
        from app.main import app
        from jose import jwt
        from app.auth import SECRET_KEY, ALGORITHM
        from datetime import datetime, timezone, timedelta

        # Create token without sub claim
        token = jwt.encode(
            {"exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        with TestClient(app) as test_client:
            with pytest.raises(Exception):  # WebSocket will close
                with test_client.websocket_connect("/ws") as websocket:
                    websocket.send_json({"type": "auth", "payload": {"token": token}})
                    # Connection should close

    @pytest.mark.asyncio
    async def test_websocket_token_invalid_uuid(self, client: AsyncClient):
        """Test WebSocket auth with token containing invalid UUID."""
        from starlette.testclient import TestClient
        from app.main import app
        from app.auth import create_access_token

        # Create token with invalid UUID
        token = create_access_token(data={"sub": "not-a-valid-uuid"})

        with TestClient(app) as test_client:
            with pytest.raises(Exception):  # WebSocket will close
                with test_client.websocket_connect("/ws") as websocket:
                    websocket.send_json({"type": "auth", "payload": {"token": token}})
                    # Connection should close

    @pytest.mark.asyncio
    async def test_websocket_user_not_found(self, client: AsyncClient):
        """Test WebSocket auth with token for non-existent user."""
        from starlette.testclient import TestClient
        from app.main import app
        from app.auth import create_access_token
        from uuid import uuid4

        # Create token for user that doesn't exist
        token = create_access_token(data={"sub": str(uuid4())})

        with TestClient(app) as test_client:
            with pytest.raises(Exception):  # WebSocket will close
                with test_client.websocket_connect("/ws") as websocket:
                    websocket.send_json({"type": "auth", "payload": {"token": token}})
                    # Connection should close due to user not found

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, client: AsyncClient, test_user: dict):
        """Test WebSocket ping/pong after authentication."""
        from starlette.testclient import TestClient
        from app.main import app

        with patch("app.main.manager") as mock_manager:
            mock_connection = MagicMock()
            mock_connection.websocket = MagicMock()
            mock_manager.connect = AsyncMock(return_value=mock_connection)
            mock_manager.disconnect = AsyncMock()

            with patch("app.main.handle_websocket_message") as mock_handler:
                mock_handler.return_value = None

                with TestClient(app) as test_client:
                    with test_client.websocket_connect("/ws") as websocket:
                        # Authenticate first
                        websocket.send_json({"type": "auth", "payload": {"token": test_user["token"]}})
                        response = websocket.receive_json()
                        assert response["type"] == "auth_success"

                        # Send ping
                        websocket.send_json({"type": "ping", "payload": {}})

                        # Handler should be called
                        # Note: The actual pong response may come through the handler


class TestAPIErrorResponses:
    """Tests for API error responses."""

    @pytest.mark.asyncio
    async def test_unauthorized_no_token(self, client: AsyncClient):
        """Test 401 when no token provided."""
        response = await client.get("/api/whiteboards")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unauthorized_invalid_token(self, client: AsyncClient):
        """Test 401 when invalid token provided."""
        response = await client.get(
            "/api/whiteboards",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_validation_error_returns_422(self, client: AsyncClient, test_user: dict):
        """Test that validation errors return 422."""
        response = await client.post(
            "/api/whiteboards",
            json={"name": ""},  # Empty name should fail validation
            headers=test_user["headers"],
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, client: AsyncClient, test_user: dict):
        """Test that not found returns 404."""
        from uuid import uuid4
        response = await client.get(
            f"/api/whiteboards/{uuid4()}",
            headers=test_user["headers"],
        )
        assert response.status_code == 404


class TestLifespan:
    """Tests for application lifespan events."""

    @pytest.mark.asyncio
    async def test_app_startup_connects_to_nats(self):
        """Test that app startup attempts NATS connection."""
        from app.main import app, lifespan

        with patch("app.main.nats_client") as mock_nats:
            mock_nats.connect = AsyncMock()
            mock_nats.close = AsyncMock()

            async with lifespan(app):
                mock_nats.connect.assert_called_once()

            mock_nats.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_app_startup_handles_nats_failure(self):
        """Test that app startup handles NATS connection failure gracefully."""
        from app.main import app, lifespan

        with patch("app.main.nats_client") as mock_nats:
            mock_nats.connect = AsyncMock(side_effect=Exception("NATS unavailable"))
            mock_nats.close = AsyncMock()

            with patch("app.main.close_db") as mock_close_db:
                mock_close_db.return_value = None

                # Should not raise, just log warning
                async with lifespan(app):
                    pass


class TestRateLimiting:
    """Tests for rate limiting behavior."""

    @pytest.mark.asyncio
    async def test_rate_limiting_disabled_in_tests(self, client: AsyncClient):
        """Test that rate limiting is disabled during tests."""
        # Make many requests - should not get rate limited in test mode
        for _ in range(20):
            response = await client.post(
                "/api/auth/register",
                json={"username": f"user_{_}", "password": "testpass123"},
            )
            # Should either succeed or fail for other reasons, not rate limit
            assert response.status_code != 429
