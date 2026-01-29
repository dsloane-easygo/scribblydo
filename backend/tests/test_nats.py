"""Tests for NATS client messaging."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.messaging.nats_client import NATSClientManager


class TestNATSClientManager:
    """Tests for NATSClientManager."""

    @pytest.fixture
    def nats_manager(self):
        """Create a fresh NATS client manager for each test."""
        return NATSClientManager()

    @pytest.mark.asyncio
    async def test_connect_success(self, nats_manager):
        """Test successful NATS connection."""
        with patch("app.messaging.nats_client.nats.connect") as mock_connect:
            mock_client = AsyncMock()
            mock_connect.return_value = mock_client

            await nats_manager.connect()

            assert nats_manager._connected is True
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_already_connected(self, nats_manager):
        """Test connect when already connected does nothing."""
        nats_manager._connected = True

        with patch("app.messaging.nats_client.nats.connect") as mock_connect:
            await nats_manager.connect()
            mock_connect.assert_not_called()

    @pytest.mark.asyncio
    async def test_connect_failure(self, nats_manager):
        """Test NATS connection failure raises exception."""
        with patch("app.messaging.nats_client.nats.connect") as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            with pytest.raises(Exception, match="Connection failed"):
                await nats_manager.connect()

            assert nats_manager._connected is False

    @pytest.mark.asyncio
    async def test_close(self, nats_manager):
        """Test closing NATS connection."""
        mock_client = AsyncMock()
        mock_client.drain = AsyncMock()
        mock_client.close = AsyncMock()

        nats_manager._client = mock_client
        nats_manager._connected = True

        await nats_manager.close()

        mock_client.drain.assert_called_once()
        mock_client.close.assert_called_once()
        assert nats_manager._connected is False

    @pytest.mark.asyncio
    async def test_close_not_connected(self, nats_manager):
        """Test closing when not connected does nothing."""
        nats_manager._connected = False
        await nats_manager.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_publish_not_connected(self, nats_manager):
        """Test publish when not connected logs warning."""
        nats_manager._connected = False

        # Should not raise, just logs warning
        await nats_manager.publish("test.subject", {"key": "value"})

    @pytest.mark.asyncio
    async def test_publish_success(self, nats_manager):
        """Test successful message publish."""
        mock_client = AsyncMock()
        mock_client.publish = AsyncMock()

        nats_manager._client = mock_client
        nats_manager._connected = True

        await nats_manager.publish("test.subject", {"key": "value"})

        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args
        assert call_args[0][0] == "test.subject"

    @pytest.mark.asyncio
    async def test_publish_failure(self, nats_manager):
        """Test publish failure is handled gracefully."""
        mock_client = AsyncMock()
        mock_client.publish = AsyncMock(side_effect=Exception("Publish failed"))

        nats_manager._client = mock_client
        nats_manager._connected = True

        # Should not raise, just logs error
        await nats_manager.publish("test.subject", {"key": "value"})

    @pytest.mark.asyncio
    async def test_subscribe(self, nats_manager):
        """Test subscribing to a subject."""
        mock_client = AsyncMock()
        mock_subscription = AsyncMock()
        mock_client.subscribe = AsyncMock(return_value=mock_subscription)

        nats_manager._client = mock_client
        nats_manager._connected = True

        handler = AsyncMock()
        await nats_manager.subscribe("test.subject", handler)

        assert "test.subject" in nats_manager._handlers
        assert handler in nats_manager._handlers["test.subject"]
        mock_client.subscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscribe_multiple_handlers(self, nats_manager):
        """Test multiple handlers for same subject."""
        mock_client = AsyncMock()
        mock_subscription = AsyncMock()
        mock_client.subscribe = AsyncMock(return_value=mock_subscription)

        nats_manager._client = mock_client
        nats_manager._connected = True

        handler1 = AsyncMock()
        handler2 = AsyncMock()
        await nats_manager.subscribe("test.subject", handler1)
        await nats_manager.subscribe("test.subject", handler2)

        assert len(nats_manager._handlers["test.subject"]) == 2
        # Only one subscription to NATS
        assert mock_client.subscribe.call_count == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_specific_handler(self, nats_manager):
        """Test unsubscribing a specific handler."""
        mock_client = AsyncMock()
        mock_subscription = AsyncMock()
        mock_subscription.unsubscribe = AsyncMock()
        mock_client.subscribe = AsyncMock(return_value=mock_subscription)

        nats_manager._client = mock_client
        nats_manager._connected = True

        handler1 = AsyncMock()
        handler2 = AsyncMock()
        await nats_manager.subscribe("test.subject", handler1)
        await nats_manager.subscribe("test.subject", handler2)

        await nats_manager.unsubscribe("test.subject", handler1)

        assert handler1 not in nats_manager._handlers["test.subject"]
        assert handler2 in nats_manager._handlers["test.subject"]

    @pytest.mark.asyncio
    async def test_unsubscribe_all_handlers(self, nats_manager):
        """Test unsubscribing all handlers removes subscription."""
        mock_client = AsyncMock()
        mock_subscription = AsyncMock()
        mock_subscription.unsubscribe = AsyncMock()
        mock_client.subscribe = AsyncMock(return_value=mock_subscription)

        nats_manager._client = mock_client
        nats_manager._connected = True

        handler = AsyncMock()
        await nats_manager.subscribe("test.subject", handler)
        await nats_manager.unsubscribe("test.subject")

        assert "test.subject" not in nats_manager._handlers
        mock_subscription.unsubscribe.assert_called_once()

    def test_whiteboard_subject(self, nats_manager):
        """Test whiteboard subject generation."""
        whiteboard_id = uuid4()
        subject = nats_manager.whiteboard_subject(whiteboard_id)
        assert subject == f"whiteboard.{whiteboard_id}"

    def test_user_subject(self, nats_manager):
        """Test user subject generation."""
        user_id = uuid4()
        subject = nats_manager.user_subject(user_id)
        assert subject == f"user.{user_id}"

    def test_notifications_subject(self, nats_manager):
        """Test notifications subject generation."""
        user_id = uuid4()
        subject = nats_manager.notifications_subject(user_id)
        assert subject == f"notifications.{user_id}"

    def test_chat_subject(self, nats_manager):
        """Test chat subject generation."""
        room_id = uuid4()
        subject = nats_manager.chat_subject(room_id)
        assert subject == f"chat.{room_id}"

    def test_presence_subject(self, nats_manager):
        """Test presence subject generation."""
        subject = nats_manager.presence_subject()
        assert subject == "presence.updates"

    @pytest.mark.asyncio
    async def test_publish_note_event(self, nats_manager):
        """Test publishing note event."""
        whiteboard_id = uuid4()

        with patch.object(nats_manager, "publish") as mock_publish:
            mock_publish.return_value = None
            await nats_manager.publish_note_event(
                whiteboard_id,
                "note_created",
                {"id": str(uuid4()), "title": "Test"},
                {"id": str(uuid4()), "username": "testuser"},
            )

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert call_args[0][0] == f"whiteboard.{whiteboard_id}"
            assert call_args[0][1]["type"] == "note_created"

    @pytest.mark.asyncio
    async def test_publish_whiteboard_event(self, nats_manager):
        """Test publishing whiteboard event."""
        whiteboard_id = uuid4()

        with patch.object(nats_manager, "publish") as mock_publish:
            mock_publish.return_value = None
            await nats_manager.publish_whiteboard_event(
                whiteboard_id,
                "whiteboard_updated",
                {"id": str(whiteboard_id), "name": "Test"},
                {"id": str(uuid4()), "username": "testuser"},
            )

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert call_args[0][1]["type"] == "whiteboard_updated"

    @pytest.mark.asyncio
    async def test_publish_notification(self, nats_manager):
        """Test publishing user notification."""
        user_id = uuid4()
        whiteboard_id = uuid4()

        with patch.object(nats_manager, "publish") as mock_publish:
            mock_publish.return_value = None
            await nats_manager.publish_notification(
                user_id,
                whiteboard_id,
                "share_added",
                "You have been added to a whiteboard",
            )

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert call_args[0][0] == f"notifications.{user_id}"
            assert call_args[0][1]["type"] == "notification"

    @pytest.mark.asyncio
    async def test_publish_presence_update(self, nats_manager):
        """Test publishing presence update."""
        online_users = [{"id": str(uuid4()), "username": "user1"}]

        with patch.object(nats_manager, "publish") as mock_publish:
            mock_publish.return_value = None
            await nats_manager.publish_presence_update(online_users)

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert call_args[0][0] == "presence.updates"
            assert call_args[0][1]["type"] == "presence_update"

    @pytest.mark.asyncio
    async def test_publish_chat_message(self, nats_manager):
        """Test publishing chat message."""
        room_id = uuid4()

        with patch.object(nats_manager, "publish") as mock_publish:
            mock_publish.return_value = None
            await nats_manager.publish_chat_message(
                room_id,
                {"content": "Hello!", "user_id": str(uuid4())},
            )

            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert call_args[0][0] == f"chat.{room_id}"
            assert call_args[0][1]["type"] == "new_message"

    @pytest.mark.asyncio
    async def test_error_callback(self, nats_manager):
        """Test error callback logs error."""
        # Should not raise
        await nats_manager._error_callback(Exception("Test error"))

    @pytest.mark.asyncio
    async def test_disconnected_callback(self, nats_manager):
        """Test disconnected callback logs warning."""
        # Should not raise
        await nats_manager._disconnected_callback()

    @pytest.mark.asyncio
    async def test_reconnected_callback(self, nats_manager):
        """Test reconnected callback logs info."""
        # Should not raise
        await nats_manager._reconnected_callback()
