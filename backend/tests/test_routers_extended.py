"""Extended tests for router modules to improve coverage."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


class TestWhiteboardBroadcasts:
    """Tests for whiteboard broadcast functions."""

    @pytest.mark.asyncio
    async def test_broadcast_whiteboard_event_success(self):
        """Test successful whiteboard event broadcast."""
        from app.routers.whiteboards import broadcast_whiteboard_event

        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish_whiteboard_event = AsyncMock()

            await broadcast_whiteboard_event(
                whiteboard_id,
                "whiteboard_updated",
                {"id": str(whiteboard_id), "name": "Test"},
                {"id": str(uuid4()), "username": "testuser"},
            )

            mock_nats.publish_whiteboard_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_whiteboard_event_failure(self):
        """Test whiteboard event broadcast handles failures gracefully."""
        from app.routers.whiteboards import broadcast_whiteboard_event

        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish_whiteboard_event = AsyncMock(side_effect=Exception("NATS error"))

            # Should not raise, just log warning
            await broadcast_whiteboard_event(
                whiteboard_id,
                "whiteboard_updated",
                {"id": str(whiteboard_id), "name": "Test"},
                {"id": str(uuid4()), "username": "testuser"},
            )

    @pytest.mark.asyncio
    async def test_broadcast_global_whiteboard_event_success(self):
        """Test successful global whiteboard event broadcast."""
        from app.routers.whiteboards import broadcast_global_whiteboard_event

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish = AsyncMock()

            await broadcast_global_whiteboard_event(
                "whiteboard_created",
                {"id": str(uuid4()), "name": "Test"},
                {"id": str(uuid4()), "username": "testuser"},
            )

            mock_nats.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_global_whiteboard_event_failure(self):
        """Test global whiteboard event broadcast handles failures gracefully."""
        from app.routers.whiteboards import broadcast_global_whiteboard_event

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish = AsyncMock(side_effect=Exception("NATS error"))

            # Should not raise, just log warning
            await broadcast_global_whiteboard_event(
                "whiteboard_created",
                {"id": str(uuid4()), "name": "Test"},
                {"id": str(uuid4()), "username": "testuser"},
            )


class TestNoteBroadcasts:
    """Tests for note broadcast functions."""

    @pytest.mark.asyncio
    async def test_broadcast_note_event_success(self):
        """Test successful note event broadcast."""
        from app.routers.notes import broadcast_note_event

        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish_note_event = AsyncMock()

            await broadcast_note_event(
                whiteboard_id,
                "note_created",
                {"id": str(uuid4()), "title": "Test"},
                {"id": str(uuid4()), "username": "testuser"},
            )

            mock_nats.publish_note_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_note_event_failure(self):
        """Test note event broadcast handles failures gracefully."""
        from app.routers.notes import broadcast_note_event

        whiteboard_id = uuid4()

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish_note_event = AsyncMock(side_effect=Exception("NATS error"))

            # Should not raise, just log warning
            await broadcast_note_event(
                whiteboard_id,
                "note_created",
                {"id": str(uuid4()), "title": "Test"},
                {"id": str(uuid4()), "username": "testuser"},
            )


class TestWhiteboardPermissionHelpers:
    """Tests for whiteboard permission helper functions."""

    def test_get_user_permission_owner(self):
        """Test owner gets admin permission."""
        from app.routers.whiteboards import get_user_permission
        from app.models import AccessType, PermissionLevel, Whiteboard

        user_id = uuid4()
        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = user_id
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []

        permission = get_user_permission(whiteboard, user_id)
        assert permission == PermissionLevel.ADMIN

    def test_get_user_permission_public(self):
        """Test public whiteboard gives write permission."""
        from app.routers.whiteboards import get_user_permission
        from app.models import AccessType, PermissionLevel, Whiteboard

        owner_id = uuid4()
        user_id = uuid4()
        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.PUBLIC
        whiteboard.shared_with = []

        permission = get_user_permission(whiteboard, user_id)
        assert permission == PermissionLevel.WRITE

    def test_get_user_permission_shared_read(self):
        """Test shared whiteboard with read permission."""
        from app.routers.whiteboards import get_user_permission
        from app.models import AccessType, PermissionLevel, Whiteboard, WhiteboardShare

        owner_id = uuid4()
        user_id = uuid4()

        share = MagicMock(spec=WhiteboardShare)
        share.user_id = user_id
        share.permission = PermissionLevel.READ

        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.SHARED
        whiteboard.shared_with = [share]

        permission = get_user_permission(whiteboard, user_id)
        assert permission == PermissionLevel.READ

    def test_get_user_permission_no_access(self):
        """Test private whiteboard gives no permission to non-owner."""
        from app.routers.whiteboards import get_user_permission
        from app.models import AccessType, Whiteboard

        owner_id = uuid4()
        user_id = uuid4()
        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []

        permission = get_user_permission(whiteboard, user_id)
        assert permission is None

    def test_can_access_whiteboard(self):
        """Test can_access_whiteboard helper."""
        from app.routers.whiteboards import can_access_whiteboard
        from app.models import AccessType, Whiteboard

        user_id = uuid4()
        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = user_id
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []

        assert can_access_whiteboard(whiteboard, user_id) is True

    def test_can_write_whiteboard(self):
        """Test can_write_whiteboard helper."""
        from app.routers.whiteboards import can_write_whiteboard
        from app.models import AccessType, Whiteboard

        user_id = uuid4()
        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = user_id
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []

        assert can_write_whiteboard(whiteboard, user_id) is True

    def test_can_admin_whiteboard(self):
        """Test can_admin_whiteboard helper."""
        from app.routers.whiteboards import can_admin_whiteboard
        from app.models import AccessType, Whiteboard

        user_id = uuid4()
        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = user_id
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []

        assert can_admin_whiteboard(whiteboard, user_id) is True


class TestWhiteboardResponseConversion:
    """Tests for whiteboard response conversion."""

    def test_whiteboard_to_response_with_shares(self):
        """Test whiteboard_to_response with shared users."""
        from app.routers.whiteboards import whiteboard_to_response
        from app.models import AccessType, PermissionLevel, Whiteboard, WhiteboardShare, User
        from datetime import datetime

        owner = MagicMock(spec=User)
        owner.id = uuid4()
        owner.username = "owner"

        shared_user = MagicMock(spec=User)
        shared_user.id = uuid4()
        shared_user.username = "shared"

        share = MagicMock(spec=WhiteboardShare)
        share.user = shared_user
        share.permission = PermissionLevel.WRITE

        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.id = uuid4()
        whiteboard.name = "Test Whiteboard"
        whiteboard.owner_id = owner.id
        whiteboard.owner = owner
        whiteboard.access_type = AccessType.SHARED
        whiteboard.shared_with = [share]
        whiteboard.created_at = datetime.now()
        whiteboard.updated_at = datetime.now()

        response = whiteboard_to_response(whiteboard)

        assert response.name == "Test Whiteboard"
        assert response.owner_username == "owner"
        assert len(response.shared_with) == 1
        assert response.shared_with[0].username == "shared"

    def test_whiteboard_to_response_without_shares(self):
        """Test whiteboard_to_response without shared users."""
        from app.routers.whiteboards import whiteboard_to_response
        from app.models import AccessType, Whiteboard, User
        from datetime import datetime

        owner = MagicMock(spec=User)
        owner.id = uuid4()
        owner.username = "owner"

        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.id = uuid4()
        whiteboard.name = "Test Whiteboard"
        whiteboard.owner_id = owner.id
        whiteboard.owner = owner
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []
        whiteboard.created_at = datetime.now()
        whiteboard.updated_at = datetime.now()

        response = whiteboard_to_response(whiteboard)

        assert response.name == "Test Whiteboard"
        assert len(response.shared_with) == 0
