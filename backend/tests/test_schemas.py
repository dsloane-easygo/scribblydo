"""Tests for Pydantic schemas."""

import pytest
from datetime import datetime
from uuid import uuid4

from app.schemas import (
    AccessType,
    PermissionLevel,
    WhiteboardResponse,
    WhiteboardWithOwnerResponse,
    SharedUserResponse,
    NoteResponse,
    NoteCreate,
    NoteUpdate,
    UserCreate,
    UserResponse,
)


class TestWhiteboardResponse:
    """Tests for WhiteboardResponse schema."""

    def test_is_private_true(self):
        """Test is_private property returns True for private whiteboards."""
        response = WhiteboardResponse(
            id=uuid4(),
            name="Test",
            owner_id=uuid4(),
            access_type=AccessType.PRIVATE,
            shared_with=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert response.is_private is True

    def test_is_private_false_public(self):
        """Test is_private property returns False for public whiteboards."""
        response = WhiteboardResponse(
            id=uuid4(),
            name="Test",
            owner_id=uuid4(),
            access_type=AccessType.PUBLIC,
            shared_with=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert response.is_private is False

    def test_is_private_false_shared(self):
        """Test is_private property returns False for shared whiteboards."""
        response = WhiteboardResponse(
            id=uuid4(),
            name="Test",
            owner_id=uuid4(),
            access_type=AccessType.SHARED,
            shared_with=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert response.is_private is False


class TestWhiteboardWithOwnerResponse:
    """Tests for WhiteboardWithOwnerResponse schema."""

    def test_create_with_owner(self):
        """Test creating whiteboard response with owner info."""
        response = WhiteboardWithOwnerResponse(
            id=uuid4(),
            name="Test Board",
            owner_id=uuid4(),
            owner_username="testuser",
            access_type=AccessType.PUBLIC,
            shared_with=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert response.owner_username == "testuser"

    def test_create_with_shared_users(self):
        """Test creating whiteboard response with shared users."""
        shared_user = SharedUserResponse(
            id=uuid4(),
            username="shareduser",
            permission=PermissionLevel.WRITE,
        )
        response = WhiteboardWithOwnerResponse(
            id=uuid4(),
            name="Test Board",
            owner_id=uuid4(),
            owner_username="testuser",
            access_type=AccessType.SHARED,
            shared_with=[shared_user],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert len(response.shared_with) == 1
        assert response.shared_with[0].username == "shareduser"


class TestNoteSchemas:
    """Tests for Note schemas."""

    def test_note_create_with_defaults(self):
        """Test NoteCreate with default values."""
        note = NoteCreate(
            whiteboard_id=uuid4(),
            title="Test",
            content="Content",
            color="#FFEB3B",
            x_position=100.0,
            y_position=200.0,
        )
        assert note.width == 200.0
        assert note.height == 180.0

    def test_note_create_with_custom_dimensions(self):
        """Test NoteCreate with custom dimensions."""
        note = NoteCreate(
            whiteboard_id=uuid4(),
            title="Test",
            content="Content",
            color="#FFEB3B",
            x_position=100.0,
            y_position=200.0,
            width=300.0,
            height=250.0,
        )
        assert note.width == 300.0
        assert note.height == 250.0

    def test_note_update_partial(self):
        """Test NoteUpdate with partial fields."""
        update = NoteUpdate(title="New Title")
        data = update.model_dump(exclude_unset=True)
        assert "title" in data
        assert "content" not in data

    def test_note_response(self):
        """Test NoteResponse schema."""
        response = NoteResponse(
            id=uuid4(),
            whiteboard_id=uuid4(),
            title="Test",
            content="Content",
            color="#FFEB3B",
            x_position=100.0,
            y_position=200.0,
            width=200.0,
            height=180.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert response.title == "Test"


class TestUserSchemas:
    """Tests for User schemas."""

    def test_user_create_minimal(self):
        """Test UserCreate with minimal fields."""
        user = UserCreate(username="testuser", password="password123")
        assert user.first_name is None
        assert user.last_name is None

    def test_user_create_with_names(self):
        """Test UserCreate with names."""
        user = UserCreate(
            username="testuser",
            password="password123",
            first_name="Test",
            last_name="User",
        )
        assert user.first_name == "Test"
        assert user.last_name == "User"

    def test_user_response(self):
        """Test UserResponse schema."""
        response = UserResponse(
            id=uuid4(),
            username="testuser",
            first_name="Test",
            last_name="User",
            created_at=datetime.now(),
        )
        assert response.username == "testuser"
