"""Tests for SQLAlchemy models."""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models import AccessType, PermissionLevel, User, Whiteboard, Note, WhiteboardShare


class TestUser:
    """Tests for User model."""

    def test_user_repr(self):
        """Test User __repr__ method."""
        user = User(
            id=uuid4(),
            username="testuser",
            password_hash="hashed",
        )
        repr_str = repr(user)
        assert "User" in repr_str
        assert "testuser" in repr_str


class TestWhiteboard:
    """Tests for Whiteboard model."""

    def test_whiteboard_repr(self):
        """Test Whiteboard __repr__ method."""
        whiteboard = Whiteboard(
            id=uuid4(),
            name="Test Board",
            owner_id=uuid4(),
            access_type=AccessType.PUBLIC,
        )
        repr_str = repr(whiteboard)
        assert "Whiteboard" in repr_str
        assert "Test Board" in repr_str

    def test_whiteboard_is_private_true(self):
        """Test is_private property returns True for private whiteboards."""
        whiteboard = Whiteboard(
            id=uuid4(),
            name="Private Board",
            owner_id=uuid4(),
            access_type=AccessType.PRIVATE,
        )
        assert whiteboard.is_private is True

    def test_whiteboard_is_private_false(self):
        """Test is_private property returns False for public whiteboards."""
        whiteboard = Whiteboard(
            id=uuid4(),
            name="Public Board",
            owner_id=uuid4(),
            access_type=AccessType.PUBLIC,
        )
        assert whiteboard.is_private is False

    def test_whiteboard_is_private_shared(self):
        """Test is_private property returns False for shared whiteboards."""
        whiteboard = Whiteboard(
            id=uuid4(),
            name="Shared Board",
            owner_id=uuid4(),
            access_type=AccessType.SHARED,
        )
        assert whiteboard.is_private is False


class TestNote:
    """Tests for Note model."""

    def test_note_repr(self):
        """Test Note __repr__ method."""
        note = Note(
            id=uuid4(),
            whiteboard_id=uuid4(),
            title="Test Note",
            content="Content",
            color="#FFEB3B",
            x_position=100.0,
            y_position=200.0,
        )
        repr_str = repr(note)
        assert "Note" in repr_str
        assert "Test Note" in repr_str


class TestWhiteboardShare:
    """Tests for WhiteboardShare model."""

    def test_whiteboard_share_repr(self):
        """Test WhiteboardShare __repr__ method."""
        whiteboard_id = uuid4()
        user_id = uuid4()
        share = WhiteboardShare(
            id=uuid4(),
            whiteboard_id=whiteboard_id,
            user_id=user_id,
            permission=PermissionLevel.WRITE,
        )
        repr_str = repr(share)
        assert "WhiteboardShare" in repr_str
        assert str(whiteboard_id) in repr_str
        assert str(user_id) in repr_str


class TestAccessType:
    """Tests for AccessType enum."""

    def test_access_type_values(self):
        """Test AccessType enum has expected values."""
        assert AccessType.PUBLIC.value == "public"
        assert AccessType.PRIVATE.value == "private"
        assert AccessType.SHARED.value == "shared"


class TestPermissionLevel:
    """Tests for PermissionLevel enum."""

    def test_permission_level_values(self):
        """Test PermissionLevel enum has expected values."""
        assert PermissionLevel.READ.value == "read"
        assert PermissionLevel.WRITE.value == "write"
        assert PermissionLevel.ADMIN.value == "admin"
