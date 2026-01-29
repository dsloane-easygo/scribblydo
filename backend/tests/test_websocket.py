"""Tests for WebSocket handlers and connection manager."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from app.websocket.connection_manager import ConnectionManager, UserConnection
from app.websocket.handlers import (
    handle_websocket_message,
    handle_join_whiteboard,
    handle_leave_whiteboard,
    handle_cursor_move,
    handle_note_position,
    handle_ping,
)


class TestUserConnection:
    """Tests for UserConnection dataclass."""

    def test_user_connection_creation(self):
        """Test creating a UserConnection."""
        ws = MagicMock()
        user_id = uuid4()
        conn = UserConnection(
            websocket=ws,
            user_id=user_id,
            username="testuser",
        )
        assert conn.user_id == user_id
        assert conn.username == "testuser"
        assert conn.current_whiteboard_id is None
        assert conn.cursor_x == 0.0
        assert conn.cursor_y == 0.0

    def test_user_connection_hash(self):
        """Test UserConnection hash is based on websocket."""
        ws1 = MagicMock()
        ws2 = MagicMock()
        conn1 = UserConnection(websocket=ws1, user_id=uuid4(), username="user1")
        conn2 = UserConnection(websocket=ws2, user_id=uuid4(), username="user2")

        # Different websockets should have different hashes
        assert hash(conn1) != hash(conn2)

        # Same websocket should have same hash
        conn3 = UserConnection(websocket=ws1, user_id=uuid4(), username="user3")
        assert hash(conn1) == hash(conn3)

    def test_user_connection_equality(self):
        """Test UserConnection equality."""
        ws = MagicMock()
        conn1 = UserConnection(websocket=ws, user_id=uuid4(), username="user1")
        conn2 = UserConnection(websocket=ws, user_id=uuid4(), username="user2")

        # Same websocket means equal
        assert conn1 == conn2

        # Different type
        assert conn1 != "not a connection"


class TestConnectionManager:
    """Tests for ConnectionManager."""

    @pytest_asyncio.fixture
    async def manager(self):
        """Create a fresh connection manager for each test."""
        return ConnectionManager()

    @pytest_asyncio.fixture
    async def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """Test connecting a user."""
        user_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(mock_websocket, user_id, "testuser")

        assert conn.user_id == user_id
        assert conn.username == "testuser"
        assert user_id in manager._connections
        assert conn in manager._connections[user_id]

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test disconnecting a user."""
        user_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(mock_websocket, user_id, "testuser")
            await manager.disconnect(conn)

        assert user_id not in manager._connections

    @pytest.mark.asyncio
    async def test_join_whiteboard(self, manager, mock_websocket):
        """Test joining a whiteboard."""
        user_id = uuid4()
        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.whiteboard_subject = MagicMock(return_value=f"whiteboard.{whiteboard_id}")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(mock_websocket, user_id, "testuser")
            await manager.join_whiteboard(conn, whiteboard_id)

        assert conn.current_whiteboard_id == whiteboard_id
        assert whiteboard_id in manager._whiteboard_viewers
        assert conn in manager._whiteboard_viewers[whiteboard_id]

    @pytest.mark.asyncio
    async def test_leave_whiteboard(self, manager, mock_websocket):
        """Test leaving a whiteboard."""
        user_id = uuid4()
        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.whiteboard_subject = MagicMock(return_value=f"whiteboard.{whiteboard_id}")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(mock_websocket, user_id, "testuser")
            await manager.join_whiteboard(conn, whiteboard_id)
            await manager.leave_whiteboard(conn)

        assert conn.current_whiteboard_id is None
        # Empty whiteboard viewer set should be removed
        assert whiteboard_id not in manager._whiteboard_viewers or conn not in manager._whiteboard_viewers.get(whiteboard_id, set())

    @pytest.mark.asyncio
    async def test_update_cursor(self, manager, mock_websocket):
        """Test updating cursor position."""
        user_id = uuid4()
        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.whiteboard_subject = MagicMock(return_value=f"whiteboard.{whiteboard_id}")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(mock_websocket, user_id, "testuser")
            await manager.join_whiteboard(conn, whiteboard_id)
            await manager.update_cursor(conn, 100.5, 200.5)

        assert conn.cursor_x == 100.5
        assert conn.cursor_y == 200.5

    @pytest.mark.asyncio
    async def test_broadcast_to_whiteboard(self, manager):
        """Test broadcasting to whiteboard viewers."""
        ws1 = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json = AsyncMock()

        user1_id = uuid4()
        user2_id = uuid4()
        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.whiteboard_subject = MagicMock(return_value=f"whiteboard.{whiteboard_id}")
            mock_nats.publish_presence_update = AsyncMock()

            conn1 = await manager.connect(ws1, user1_id, "user1")
            conn2 = await manager.connect(ws2, user2_id, "user2")
            await manager.join_whiteboard(conn1, whiteboard_id)
            await manager.join_whiteboard(conn2, whiteboard_id)

            # Broadcast excluding conn1
            message = {"type": "test", "payload": {}}
            await manager.broadcast_to_whiteboard(whiteboard_id, message, exclude=conn1)

        # Only ws2 should receive the message
        ws2.send_json.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_user(self, manager):
        """Test broadcasting to all connections of a user."""
        ws1 = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json = AsyncMock()

        user_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.publish_presence_update = AsyncMock()

            # Same user with two connections
            conn1 = await manager.connect(ws1, user_id, "testuser")
            conn2 = await manager.connect(ws2, user_id, "testuser")

            message = {"type": "test", "payload": {}}
            await manager.broadcast_to_user(user_id, message)

        ws1.send_json.assert_called_with(message)
        ws2.send_json.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, manager):
        """Test broadcasting to all connected users."""
        ws1 = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json = AsyncMock()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.publish_presence_update = AsyncMock()

            conn1 = await manager.connect(ws1, uuid4(), "user1")
            conn2 = await manager.connect(ws2, uuid4(), "user2")

            message = {"type": "test", "payload": {}}
            await manager.broadcast_to_all(message)

        ws1.send_json.assert_called_with(message)
        ws2.send_json.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_get_online_users(self, manager, mock_websocket):
        """Test getting list of online users."""
        user_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.publish_presence_update = AsyncMock()

            await manager.connect(mock_websocket, user_id, "testuser")

            users = await manager.get_online_users()

        assert len(users) == 1
        assert users[0]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_whiteboard_viewers(self, manager, mock_websocket):
        """Test getting whiteboard viewers."""
        user_id = uuid4()
        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.whiteboard_subject = MagicMock(return_value=f"whiteboard.{whiteboard_id}")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(mock_websocket, user_id, "testuser")
            await manager.join_whiteboard(conn, whiteboard_id)
            await manager.update_cursor(conn, 50.0, 75.0)

            viewers = await manager.get_whiteboard_viewers(whiteboard_id)

        assert len(viewers) == 1
        assert viewers[0]["username"] == "testuser"
        assert viewers[0]["cursor_x"] == 50.0
        assert viewers[0]["cursor_y"] == 75.0

    @pytest.mark.asyncio
    async def test_get_users_not_viewing_whiteboard(self, manager):
        """Test getting users not viewing a whiteboard."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        user1_id = uuid4()
        user2_id = uuid4()
        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.whiteboard_subject = MagicMock(return_value=f"whiteboard.{whiteboard_id}")
            mock_nats.publish_presence_update = AsyncMock()

            conn1 = await manager.connect(ws1, user1_id, "user1")
            conn2 = await manager.connect(ws2, user2_id, "user2")
            await manager.join_whiteboard(conn1, whiteboard_id)

            not_viewing = manager.get_users_not_viewing_whiteboard(whiteboard_id)

        assert user2_id in not_viewing
        assert user1_id not in not_viewing

    @pytest.mark.asyncio
    async def test_is_user_viewing_whiteboard(self, manager, mock_websocket):
        """Test checking if user is viewing whiteboard."""
        user_id = uuid4()
        whiteboard_id = uuid4()
        other_whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.whiteboard_subject = MagicMock(return_value=f"whiteboard.{whiteboard_id}")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(mock_websocket, user_id, "testuser")
            await manager.join_whiteboard(conn, whiteboard_id)

            assert manager.is_user_viewing_whiteboard(user_id, whiteboard_id) is True
            assert manager.is_user_viewing_whiteboard(user_id, other_whiteboard_id) is False


class TestConnectionManagerEdgeCases:
    """Additional edge case tests for ConnectionManager."""

    @pytest_asyncio.fixture
    async def manager(self):
        """Create a fresh connection manager for each test."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_setup_user_subscriptions_failure(self, manager):
        """Test that subscription setup handles failures gracefully."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        user_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock(side_effect=Exception("NATS error"))
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.publish_presence_update = AsyncMock()

            # Should not raise, just log warning
            conn = await manager.connect(ws, user_id, "testuser")
            assert conn is not None

    @pytest.mark.asyncio
    async def test_subscribe_to_whiteboard_failure(self, manager):
        """Test that whiteboard subscription handles failures gracefully."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        user_id = uuid4()
        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.whiteboard_subject = MagicMock(return_value=f"whiteboard.{whiteboard_id}")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(ws, user_id, "testuser")

            # Make subscribe fail for whiteboard
            mock_nats.subscribe = AsyncMock(side_effect=Exception("NATS error"))

            # Should not raise
            await manager.join_whiteboard(conn, whiteboard_id)
            assert conn.current_whiteboard_id == whiteboard_id

    @pytest.mark.asyncio
    async def test_broadcast_presence_update_nats_failure(self, manager):
        """Test presence update handles NATS failure gracefully."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        user_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.publish_presence_update = AsyncMock(side_effect=Exception("NATS error"))

            # Should not raise
            conn = await manager.connect(ws, user_id, "testuser")
            assert conn is not None

    @pytest.mark.asyncio
    async def test_send_to_connection_failure(self, manager):
        """Test that send to connection handles failures gracefully."""
        ws = AsyncMock()
        ws.send_json = AsyncMock(side_effect=Exception("WebSocket error"))
        user_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(ws, user_id, "testuser")

            # Should not raise
            await manager.broadcast_to_user(user_id, {"type": "test"})

    @pytest.mark.asyncio
    async def test_leave_whiteboard_not_in_whiteboard(self, manager):
        """Test leaving whiteboard when not viewing any."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        user_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(ws, user_id, "testuser")

            # Should not raise
            await manager.leave_whiteboard(conn)
            assert conn.current_whiteboard_id is None

    @pytest.mark.asyncio
    async def test_disconnect_while_viewing_whiteboard(self, manager):
        """Test disconnecting while viewing a whiteboard."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        user_id = uuid4()
        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.whiteboard_subject = MagicMock(return_value=f"whiteboard.{whiteboard_id}")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(ws, user_id, "testuser")
            await manager.join_whiteboard(conn, whiteboard_id)
            await manager.disconnect(conn)

            assert user_id not in manager._connections
            assert whiteboard_id not in manager._whiteboard_viewers or len(manager._whiteboard_viewers.get(whiteboard_id, set())) == 0

    @pytest.mark.asyncio
    async def test_update_cursor_not_in_whiteboard(self, manager):
        """Test updating cursor when not in a whiteboard."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        user_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.subscribe = AsyncMock()
            mock_nats.notifications_subject = MagicMock(return_value="notifications.test")
            mock_nats.presence_subject = MagicMock(return_value="presence.updates")
            mock_nats.publish_presence_update = AsyncMock()

            conn = await manager.connect(ws, user_id, "testuser")

            # Should update position but not broadcast
            await manager.update_cursor(conn, 100.0, 200.0)
            assert conn.cursor_x == 100.0
            assert conn.cursor_y == 200.0


class TestWebSocketHandlers:
    """Tests for WebSocket message handlers."""

    @pytest_asyncio.fixture
    async def mock_connection(self):
        """Create a mock UserConnection."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        return UserConnection(
            websocket=ws,
            user_id=uuid4(),
            username="testuser",
        )

    @pytest.mark.asyncio
    async def test_handle_websocket_message_ping(self, mock_connection):
        """Test handling ping message."""
        await handle_websocket_message(mock_connection, {"type": "ping", "payload": {}})
        mock_connection.websocket.send_json.assert_called_with({"type": "pong", "payload": {}})

    @pytest.mark.asyncio
    async def test_handle_websocket_message_unknown_type(self, mock_connection):
        """Test handling unknown message type."""
        await handle_websocket_message(mock_connection, {"type": "unknown", "payload": {}})
        mock_connection.websocket.send_json.assert_called()
        call_args = mock_connection.websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["payload"]["code"] == "unknown_message_type"

    @pytest.mark.asyncio
    async def test_handle_ping(self, mock_connection):
        """Test ping handler."""
        await handle_ping(mock_connection, {})
        mock_connection.websocket.send_json.assert_called_with({"type": "pong", "payload": {}})

    @pytest.mark.asyncio
    async def test_handle_leave_whiteboard(self, mock_connection):
        """Test leave whiteboard handler."""
        with patch("app.websocket.handlers.manager") as mock_manager:
            mock_manager.leave_whiteboard = AsyncMock()
            await handle_leave_whiteboard(mock_connection, {})

            mock_manager.leave_whiteboard.assert_called_once_with(mock_connection)
            mock_connection.websocket.send_json.assert_called_with({
                "type": "whiteboard_left",
                "payload": {},
            })

    @pytest.mark.asyncio
    async def test_handle_join_whiteboard_missing_id(self, mock_connection):
        """Test join whiteboard with missing ID."""
        await handle_join_whiteboard(mock_connection, {})
        call_args = mock_connection.websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["payload"]["code"] == "missing_whiteboard_id"

    @pytest.mark.asyncio
    async def test_handle_join_whiteboard_invalid_uuid(self, mock_connection):
        """Test join whiteboard with invalid UUID."""
        await handle_join_whiteboard(mock_connection, {"whiteboard_id": "not-a-uuid"})
        call_args = mock_connection.websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["payload"]["code"] == "invalid_whiteboard_id"

    @pytest.mark.asyncio
    async def test_handle_join_whiteboard_access_denied(self, mock_connection):
        """Test join whiteboard with access denied."""
        whiteboard_id = uuid4()

        with patch("app.database.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            with patch("app.permissions.has_whiteboard_read_access", new_callable=AsyncMock, return_value=False):
                await handle_join_whiteboard(mock_connection, {"whiteboard_id": str(whiteboard_id)})

        call_args = mock_connection.websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["payload"]["code"] == "access_denied"

    @pytest.mark.asyncio
    async def test_handle_join_whiteboard_success(self, mock_connection):
        """Test successful whiteboard join."""
        whiteboard_id = uuid4()

        with patch("app.database.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value.__aenter__.return_value = mock_session

            with patch("app.permissions.has_whiteboard_read_access", new_callable=AsyncMock, return_value=True):
                with patch("app.websocket.handlers.manager") as mock_manager:
                    mock_manager.join_whiteboard = AsyncMock()
                    mock_manager.get_whiteboard_viewers = AsyncMock(return_value=[])

                    await handle_join_whiteboard(mock_connection, {"whiteboard_id": str(whiteboard_id)})

                    mock_manager.join_whiteboard.assert_called_once()

        call_args = mock_connection.websocket.send_json.call_args[0][0]
        assert call_args["type"] == "whiteboard_joined"
        assert call_args["payload"]["whiteboard_id"] == str(whiteboard_id)

    @pytest.mark.asyncio
    async def test_handle_cursor_move(self, mock_connection):
        """Test cursor move handler."""
        with patch("app.websocket.handlers.manager") as mock_manager:
            mock_manager.update_cursor = AsyncMock()
            await handle_cursor_move(mock_connection, {"x": 100.5, "y": 200.5})
            mock_manager.update_cursor.assert_called_once_with(mock_connection, 100.5, 200.5)

    @pytest.mark.asyncio
    async def test_handle_cursor_move_defaults(self, mock_connection):
        """Test cursor move with missing coordinates uses defaults."""
        with patch("app.websocket.handlers.manager") as mock_manager:
            mock_manager.update_cursor = AsyncMock()
            await handle_cursor_move(mock_connection, {})
            mock_manager.update_cursor.assert_called_once_with(mock_connection, 0.0, 0.0)

    @pytest.mark.asyncio
    async def test_handle_cursor_move_invalid_type(self, mock_connection):
        """Test cursor move with invalid type silently ignores."""
        with patch("app.websocket.handlers.manager") as mock_manager:
            mock_manager.update_cursor = AsyncMock()
            await handle_cursor_move(mock_connection, {"x": "invalid", "y": "invalid"})
            # Should not call update_cursor for invalid data
            mock_manager.update_cursor.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_note_position_valid(self, mock_connection):
        """Test note position handler with valid data."""
        mock_connection.current_whiteboard_id = uuid4()

        with patch("app.websocket.handlers.manager") as mock_manager:
            mock_manager.broadcast_to_whiteboard = AsyncMock()
            await handle_note_position(mock_connection, {
                "note_id": str(uuid4()),
                "x_position": 100.0,
                "y_position": 200.0,
            })
            mock_manager.broadcast_to_whiteboard.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_note_position_missing_data(self, mock_connection):
        """Test note position handler with missing data silently ignores."""
        mock_connection.current_whiteboard_id = uuid4()

        with patch("app.websocket.handlers.manager") as mock_manager:
            mock_manager.broadcast_to_whiteboard = AsyncMock()
            await handle_note_position(mock_connection, {"note_id": str(uuid4())})
            mock_manager.broadcast_to_whiteboard.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_note_position_no_whiteboard(self, mock_connection):
        """Test note position handler when not in a whiteboard."""
        mock_connection.current_whiteboard_id = None

        with patch("app.websocket.handlers.manager") as mock_manager:
            mock_manager.broadcast_to_whiteboard = AsyncMock()
            await handle_note_position(mock_connection, {
                "note_id": str(uuid4()),
                "x_position": 100.0,
                "y_position": 200.0,
            })
            mock_manager.broadcast_to_whiteboard.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_note_position_invalid_coordinates(self, mock_connection):
        """Test note position handler with invalid coordinates silently ignores."""
        mock_connection.current_whiteboard_id = uuid4()

        with patch("app.websocket.handlers.manager") as mock_manager:
            mock_manager.broadcast_to_whiteboard = AsyncMock()
            await handle_note_position(mock_connection, {
                "note_id": str(uuid4()),
                "x_position": "invalid",
                "y_position": "invalid",
            })
            mock_manager.broadcast_to_whiteboard.assert_not_called()
