"""Unit tests for permissions module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models import AccessType, PermissionLevel, Whiteboard, WhiteboardShare, User
from app.permissions import (
    get_user_permission,
    get_whiteboard_with_shares,
    check_whiteboard_access,
    has_whiteboard_read_access,
)


class TestGetUserPermission:
    """Tests for get_user_permission function."""

    def test_owner_has_admin_permission(self):
        """Test that owner gets admin permission."""
        user_id = uuid4()
        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = user_id
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []

        permission = get_user_permission(whiteboard, user_id)
        assert permission == PermissionLevel.ADMIN

    def test_public_whiteboard_gives_write_permission(self):
        """Test that public whiteboards give write permission."""
        owner_id = uuid4()
        user_id = uuid4()
        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.PUBLIC
        whiteboard.shared_with = []

        permission = get_user_permission(whiteboard, user_id)
        assert permission == PermissionLevel.WRITE

    def test_shared_whiteboard_gives_shared_permission(self):
        """Test that shared whiteboards give the shared permission level."""
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

    def test_private_whiteboard_no_access(self):
        """Test that private whiteboards give no access to non-owners."""
        owner_id = uuid4()
        user_id = uuid4()
        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []

        permission = get_user_permission(whiteboard, user_id)
        assert permission is None

    def test_shared_whiteboard_not_in_list(self):
        """Test that shared whiteboards give no access to users not in share list."""
        owner_id = uuid4()
        user_id = uuid4()
        other_user_id = uuid4()

        share = MagicMock(spec=WhiteboardShare)
        share.user_id = other_user_id
        share.permission = PermissionLevel.WRITE

        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.SHARED
        whiteboard.shared_with = [share]

        permission = get_user_permission(whiteboard, user_id)
        assert permission is None


class TestGetWhiteboardWithShares:
    """Tests for get_whiteboard_with_shares function."""

    @pytest.mark.asyncio
    async def test_returns_whiteboard_with_shares(self):
        """Test that whiteboard with shares is returned."""
        whiteboard_id = uuid4()
        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        result = await get_whiteboard_with_shares(whiteboard_id, mock_db)

        assert result == mock_whiteboard
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_if_not_found(self):
        """Test that None is returned if whiteboard not found."""
        whiteboard_id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await get_whiteboard_with_shares(whiteboard_id, mock_db)

        assert result is None


class TestCheckWhiteboardAccess:
    """Tests for check_whiteboard_access function."""

    @pytest.mark.asyncio
    async def test_whiteboard_not_found(self):
        """Test that not found error is returned for missing whiteboard."""
        whiteboard_id = uuid4()
        user_id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        whiteboard, permission, error = await check_whiteboard_access(
            whiteboard_id, user_id, mock_db
        )

        assert whiteboard is None
        assert permission is None
        assert "not found" in error

    @pytest.mark.asyncio
    async def test_access_denied(self):
        """Test that access denied error is returned for private whiteboards."""
        whiteboard_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        whiteboard, permission, error = await check_whiteboard_access(
            whiteboard_id, user_id, mock_db
        )

        assert whiteboard is None
        assert permission is None
        assert "Access denied" in error

    @pytest.mark.asyncio
    async def test_write_required_but_only_read(self):
        """Test that write required error is returned for read-only users."""
        whiteboard_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()

        share = MagicMock(spec=WhiteboardShare)
        share.user_id = user_id
        share.permission = PermissionLevel.READ

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.access_type = AccessType.SHARED
        mock_whiteboard.shared_with = [share]

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        whiteboard, permission, error = await check_whiteboard_access(
            whiteboard_id, user_id, mock_db, require_write=True
        )

        assert whiteboard is None
        assert permission is None
        assert "Write permission required" in error

    @pytest.mark.asyncio
    async def test_access_granted(self):
        """Test that access is granted for owners."""
        whiteboard_id = uuid4()
        owner_id = uuid4()

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        whiteboard, permission, error = await check_whiteboard_access(
            whiteboard_id, owner_id, mock_db
        )

        assert whiteboard == mock_whiteboard
        assert permission == PermissionLevel.ADMIN
        assert error is None


class TestHasWhiteboardReadAccess:
    """Tests for has_whiteboard_read_access function."""

    @pytest.mark.asyncio
    async def test_returns_true_for_owner(self):
        """Test that owner has read access."""
        whiteboard_id = uuid4()
        owner_id = uuid4()

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        result = await has_whiteboard_read_access(whiteboard_id, owner_id, mock_db)

        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_for_no_access(self):
        """Test that non-owner has no read access to private whiteboard."""
        whiteboard_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        result = await has_whiteboard_read_access(whiteboard_id, user_id, mock_db)

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_not_found(self):
        """Test that not found whiteboard returns False."""
        whiteboard_id = uuid4()
        user_id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await has_whiteboard_read_access(whiteboard_id, user_id, mock_db)

        assert result is False
