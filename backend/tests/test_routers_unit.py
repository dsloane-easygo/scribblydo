"""Unit tests for router functions with mocked dependencies."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.models import AccessType, PermissionLevel, User, Whiteboard, WhiteboardShare, Note
from app.schemas import (
    NoteCreate,
    NoteUpdate,
    WhiteboardCreate,
    WhiteboardUpdate,
    UserCreate,
)


class TestAuthRouterUnit:
    """Unit tests for auth router functions."""

    @pytest.mark.asyncio
    async def test_register_creates_user(self):
        """Test register function creates user in database."""
        from app.routers.auth import register

        user_data = UserCreate(
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing user
        mock_db.execute.return_value = mock_result

        # Mock user that will be created
        created_user = MagicMock(spec=User)
        created_user.id = uuid4()
        created_user.username = "testuser"
        created_user.first_name = "Test"
        created_user.last_name = "User"
        created_user.created_at = datetime.now(timezone.utc)

        async def mock_refresh(obj):
            for attr in ['id', 'username', 'first_name', 'last_name', 'created_at']:
                setattr(obj, attr, getattr(created_user, attr))

        mock_db.refresh = mock_refresh
        mock_db.flush = AsyncMock()

        mock_request = MagicMock()

        with patch("app.routers.auth.get_password_hash", return_value="hashed"):
            response = await register(mock_request, user_data, mock_db)

        assert response.username == "testuser"
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_username_raises(self):
        """Test register raises for duplicate username."""
        from app.routers.auth import register
        from fastapi import HTTPException

        user_data = UserCreate(username="existing", password="testpass123")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(spec=User)  # Existing user
        mock_db.execute.return_value = mock_result

        mock_request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await register(mock_request, user_data, mock_db)

        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test login function returns token for valid credentials."""
        from app.routers.auth import login

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()
        mock_user.password_hash = "hashed"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        mock_form = MagicMock()
        mock_form.username = "testuser"
        mock_form.password = "correctpassword"

        mock_request = MagicMock()

        with patch("app.routers.auth.verify_password", return_value=True):
            with patch("app.routers.auth.create_access_token", return_value="test.token"):
                response = await login(mock_request, mock_form, mock_db)

        assert response.access_token == "test.token"
        assert response.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials_raises(self):
        """Test login raises for invalid credentials."""
        from app.routers.auth import login
        from fastapi import HTTPException

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # User not found
        mock_db.execute.return_value = mock_result

        mock_form = MagicMock()
        mock_form.username = "nonexistent"
        mock_form.password = "password"

        mock_request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await login(mock_request, mock_form, mock_db)

        assert exc_info.value.status_code == 401


class TestNotesRouterUnit:
    """Unit tests for notes router functions."""

    @pytest.mark.asyncio
    async def test_list_notes_success(self):
        """Test list_notes returns notes for accessible whiteboard."""
        from app.routers.notes import list_notes

        whiteboard_id = uuid4()
        user_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = user_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_note = MagicMock(spec=Note)
        mock_note.id = uuid4()
        mock_note.whiteboard_id = whiteboard_id
        mock_note.title = "Test Note"
        mock_note.content = "Content"
        mock_note.color = "#FFEB3B"
        mock_note.x_position = 100.0
        mock_note.y_position = 200.0
        mock_note.width = 200.0
        mock_note.height = 180.0
        mock_note.created_at = datetime.now(timezone.utc)
        mock_note.updated_at = datetime.now(timezone.utc)

        mock_db = AsyncMock()

        # Mock whiteboard query
        wb_result = MagicMock()
        wb_result.scalar_one_or_none.return_value = mock_whiteboard

        # Mock notes query
        notes_result = MagicMock()
        notes_result.scalars.return_value.all.return_value = [mock_note]

        mock_db.execute.side_effect = [wb_result, notes_result]

        response = await list_notes(mock_user, mock_db, whiteboard_id)

        assert response.total == 1
        assert len(response.notes) == 1

    @pytest.mark.asyncio
    async def test_list_notes_whiteboard_not_found(self):
        """Test list_notes raises 404 for nonexistent whiteboard."""
        from app.routers.notes import list_notes
        from fastapi import HTTPException

        whiteboard_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await list_notes(mock_user, mock_db, whiteboard_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_note_success(self):
        """Test create_note creates a note."""
        from app.routers.notes import create_note

        whiteboard_id = uuid4()
        user_id = uuid4()

        note_data = NoteCreate(
            whiteboard_id=whiteboard_id,
            title="New Note",
            content="Content",
            color="#FFEB3B",
            x_position=100.0,
            y_position=200.0,
        )

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.username = "testuser"

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = user_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        mock_background = MagicMock()

        # Setup for note creation
        note_id = uuid4()
        now = datetime.now(timezone.utc)

        async def mock_refresh(note):
            note.id = note_id
            note.created_at = now
            note.updated_at = now

        mock_db.refresh = mock_refresh

        response = await create_note(note_data, mock_user, mock_db, mock_background)

        assert response.title == "New Note"
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_note_not_found(self):
        """Test get_note raises 404 for nonexistent note."""
        from app.routers.notes import get_note
        from fastapi import HTTPException

        note_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_note(note_id, mock_user, mock_db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_note_success(self):
        """Test get_note returns note for accessible whiteboard."""
        from app.routers.notes import get_note

        note_id = uuid4()
        whiteboard_id = uuid4()
        user_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        mock_note = MagicMock(spec=Note)
        mock_note.id = note_id
        mock_note.whiteboard_id = whiteboard_id
        mock_note.title = "Test Note"
        mock_note.content = "Content"
        mock_note.color = "#FFEB3B"
        mock_note.x_position = 100.0
        mock_note.y_position = 200.0
        mock_note.width = 200.0
        mock_note.height = 180.0
        mock_note.created_at = datetime.now(timezone.utc)
        mock_note.updated_at = datetime.now(timezone.utc)

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = user_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()

        # Mock note query
        note_result = MagicMock()
        note_result.scalar_one_or_none.return_value = mock_note

        # Mock whiteboard query
        wb_result = MagicMock()
        wb_result.scalar_one_or_none.return_value = mock_whiteboard

        mock_db.execute.side_effect = [note_result, wb_result]

        response = await get_note(note_id, mock_user, mock_db)

        assert response.id == note_id

    @pytest.mark.asyncio
    async def test_update_note_not_found(self):
        """Test update_note raises 404 for nonexistent note."""
        from app.routers.notes import update_note
        from fastapi import HTTPException

        note_id = uuid4()
        update_data = NoteUpdate(title="Updated")

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        mock_background = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await update_note(note_id, update_data, mock_user, mock_db, mock_background)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_note_success(self):
        """Test update_note updates a note."""
        from app.routers.notes import update_note

        note_id = uuid4()
        whiteboard_id = uuid4()
        user_id = uuid4()

        update_data = NoteUpdate(title="Updated Title")

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.username = "testuser"

        mock_note = MagicMock(spec=Note)
        mock_note.id = note_id
        mock_note.whiteboard_id = whiteboard_id
        mock_note.title = "Original Title"
        mock_note.content = "Content"
        mock_note.color = "#FFEB3B"
        mock_note.x_position = 100.0
        mock_note.y_position = 200.0
        mock_note.width = 200.0
        mock_note.height = 180.0
        mock_note.created_at = datetime.now(timezone.utc)
        mock_note.updated_at = datetime.now(timezone.utc)

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = user_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()

        # Mock note query
        note_result = MagicMock()
        note_result.scalar_one_or_none.return_value = mock_note

        # Mock whiteboard query
        wb_result = MagicMock()
        wb_result.scalar_one_or_none.return_value = mock_whiteboard

        mock_db.execute.side_effect = [note_result, wb_result]

        async def mock_refresh(note):
            note.title = "Updated Title"

        mock_db.refresh = mock_refresh

        mock_background = MagicMock()

        response = await update_note(note_id, update_data, mock_user, mock_db, mock_background)

        assert response.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_delete_note_not_found(self):
        """Test delete_note raises 404 for nonexistent note."""
        from app.routers.notes import delete_note
        from fastapi import HTTPException

        note_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        mock_background = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await delete_note(note_id, mock_user, mock_db, mock_background)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_note_success(self):
        """Test delete_note deletes a note."""
        from app.routers.notes import delete_note

        note_id = uuid4()
        whiteboard_id = uuid4()
        user_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.username = "testuser"

        mock_note = MagicMock(spec=Note)
        mock_note.id = note_id
        mock_note.whiteboard_id = whiteboard_id

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = user_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()

        # Mock note query
        note_result = MagicMock()
        note_result.scalar_one_or_none.return_value = mock_note

        # Mock whiteboard query
        wb_result = MagicMock()
        wb_result.scalar_one_or_none.return_value = mock_whiteboard

        mock_db.execute.side_effect = [note_result, wb_result]

        mock_background = MagicMock()

        # Should not raise
        await delete_note(note_id, mock_user, mock_db, mock_background)

        mock_db.delete.assert_called_once_with(mock_note)


class TestNotesAccessDenied:
    """Tests for access denied scenarios in notes router."""

    @pytest.mark.asyncio
    async def test_list_notes_access_denied(self):
        """Test list_notes raises 403 for private whiteboard."""
        from app.routers.notes import list_notes
        from fastapi import HTTPException

        whiteboard_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()  # Different from owner

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await list_notes(mock_user, mock_db, whiteboard_id)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_create_note_write_permission_denied(self):
        """Test create_note raises 403 when user lacks write permission."""
        from app.routers.notes import create_note
        from fastapi import HTTPException

        whiteboard_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()

        note_data = NoteCreate(
            whiteboard_id=whiteboard_id,
            title="Test",
        )

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        # Create a read-only share
        mock_share = MagicMock(spec=WhiteboardShare)
        mock_share.user_id = user_id
        mock_share.permission = PermissionLevel.READ

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.access_type = AccessType.SHARED
        mock_whiteboard.shared_with = [mock_share]

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        mock_background = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await create_note(note_data, mock_user, mock_db, mock_background)

        assert exc_info.value.status_code == 403


class TestWhiteboardsRouterUnit:
    """Unit tests for whiteboards router functions."""

    @pytest.mark.asyncio
    async def test_whiteboard_to_response(self):
        """Test whiteboard_to_response converts model correctly."""
        from app.routers.whiteboards import whiteboard_to_response

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
        whiteboard.name = "Test Board"
        whiteboard.owner_id = owner.id
        whiteboard.owner = owner
        whiteboard.access_type = AccessType.SHARED
        whiteboard.shared_with = [share]
        whiteboard.created_at = datetime.now(timezone.utc)
        whiteboard.updated_at = datetime.now(timezone.utc)

        response = whiteboard_to_response(whiteboard)

        assert response.name == "Test Board"
        assert response.owner_username == "owner"
        assert len(response.shared_with) == 1
        assert response.shared_with[0].username == "shared"

    @pytest.mark.asyncio
    async def test_get_user_permission_owner(self):
        """Test get_user_permission returns ADMIN for owner."""
        from app.routers.whiteboards import get_user_permission

        user_id = uuid4()

        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = user_id
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []

        permission = get_user_permission(whiteboard, user_id)

        assert permission == PermissionLevel.ADMIN

    @pytest.mark.asyncio
    async def test_get_user_permission_public(self):
        """Test get_user_permission returns WRITE for public whiteboard."""
        from app.routers.whiteboards import get_user_permission

        owner_id = uuid4()
        user_id = uuid4()

        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.PUBLIC
        whiteboard.shared_with = []

        permission = get_user_permission(whiteboard, user_id)

        assert permission == PermissionLevel.WRITE

    @pytest.mark.asyncio
    async def test_get_user_permission_shared(self):
        """Test get_user_permission returns shared permission level."""
        from app.routers.whiteboards import get_user_permission

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

    @pytest.mark.asyncio
    async def test_get_user_permission_none(self):
        """Test get_user_permission returns None for private whiteboard."""
        from app.routers.whiteboards import get_user_permission

        owner_id = uuid4()
        user_id = uuid4()

        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []

        permission = get_user_permission(whiteboard, user_id)

        assert permission is None

    @pytest.mark.asyncio
    async def test_can_access_whiteboard(self):
        """Test can_access_whiteboard helper function."""
        from app.routers.whiteboards import can_access_whiteboard

        owner_id = uuid4()
        user_id = uuid4()

        # Public whiteboard - accessible
        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.PUBLIC
        whiteboard.shared_with = []

        assert can_access_whiteboard(whiteboard, user_id) is True

        # Private whiteboard - not accessible
        whiteboard.access_type = AccessType.PRIVATE
        assert can_access_whiteboard(whiteboard, user_id) is False

    @pytest.mark.asyncio
    async def test_can_write_whiteboard(self):
        """Test can_write_whiteboard helper function."""
        from app.routers.whiteboards import can_write_whiteboard

        owner_id = uuid4()
        user_id = uuid4()

        # Read-only share - cannot write
        share = MagicMock(spec=WhiteboardShare)
        share.user_id = user_id
        share.permission = PermissionLevel.READ

        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.SHARED
        whiteboard.shared_with = [share]

        assert can_write_whiteboard(whiteboard, user_id) is False

        # Write share - can write
        share.permission = PermissionLevel.WRITE
        assert can_write_whiteboard(whiteboard, user_id) is True

    @pytest.mark.asyncio
    async def test_can_admin_whiteboard(self):
        """Test can_admin_whiteboard helper function."""
        from app.routers.whiteboards import can_admin_whiteboard

        owner_id = uuid4()
        user_id = uuid4()

        whiteboard = MagicMock(spec=Whiteboard)
        whiteboard.owner_id = owner_id
        whiteboard.access_type = AccessType.PRIVATE
        whiteboard.shared_with = []

        # Owner is admin
        assert can_admin_whiteboard(whiteboard, owner_id) is True

        # Non-owner is not admin
        assert can_admin_whiteboard(whiteboard, user_id) is False


class TestWhiteboardsRouterCRUD:
    """Unit tests for whiteboards router CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_whiteboard_with_shared_users(self):
        """Test create_whiteboard with shared users."""
        from app.routers.whiteboards import create_whiteboard
        from app.schemas import ShareEntry, PermissionLevel as SchemaPermission

        owner_id = uuid4()
        shared_user_id = uuid4()

        mock_owner = MagicMock(spec=User)
        mock_owner.id = owner_id
        mock_owner.username = "owner"

        mock_shared_user = MagicMock(spec=User)
        mock_shared_user.id = shared_user_id
        mock_shared_user.username = "shared"

        whiteboard_data = WhiteboardCreate(
            name="Shared Board",
            access_type="shared",
            shared_with=[ShareEntry(user_id=shared_user_id, permission=SchemaPermission.WRITE)],
        )

        mock_db = AsyncMock()

        # Mock user lookup for shared user
        user_lookup_result = MagicMock()
        user_lookup_result.scalar_one_or_none.return_value = mock_shared_user

        # Mock the created whiteboard
        created_wb = MagicMock(spec=Whiteboard)
        created_wb.id = uuid4()
        created_wb.name = "Shared Board"
        created_wb.owner_id = owner_id
        created_wb.owner = mock_owner
        created_wb.access_type = AccessType.SHARED
        created_wb.shared_with = []
        created_wb.created_at = datetime.now(timezone.utc)
        created_wb.updated_at = datetime.now(timezone.utc)

        reload_result = MagicMock()
        reload_result.scalar_one.return_value = created_wb

        mock_db.execute.side_effect = [user_lookup_result, reload_result]

        mock_background = MagicMock()

        response = await create_whiteboard(whiteboard_data, mock_owner, mock_db, mock_background)

        assert response.name == "Shared Board"

    @pytest.mark.asyncio
    async def test_get_whiteboard_not_found(self):
        """Test get_whiteboard raises 404 for nonexistent whiteboard."""
        from app.routers.whiteboards import get_whiteboard
        from fastapi import HTTPException

        whiteboard_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_whiteboard(whiteboard_id, mock_user, mock_db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_whiteboard_access_denied(self):
        """Test get_whiteboard raises 403 for private whiteboard."""
        from app.routers.whiteboards import get_whiteboard
        from fastapi import HTTPException

        whiteboard_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        mock_owner = MagicMock(spec=User)
        mock_owner.username = "owner"

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.owner = mock_owner
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_whiteboard(whiteboard_id, mock_user, mock_db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_update_whiteboard_not_found(self):
        """Test update_whiteboard raises 404 for nonexistent whiteboard."""
        from app.routers.whiteboards import update_whiteboard
        from fastapi import HTTPException

        whiteboard_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()

        update_data = WhiteboardUpdate(name="Updated")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        mock_background = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await update_whiteboard(whiteboard_id, update_data, mock_user, mock_db, mock_background)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_whiteboard_access_denied(self):
        """Test update_whiteboard raises 403 for non-admin user."""
        from app.routers.whiteboards import update_whiteboard
        from fastapi import HTTPException

        whiteboard_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        mock_owner = MagicMock(spec=User)
        mock_owner.username = "owner"

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.owner = mock_owner
        mock_whiteboard.access_type = AccessType.PUBLIC
        mock_whiteboard.shared_with = []

        update_data = WhiteboardUpdate(name="Updated")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        mock_background = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await update_whiteboard(whiteboard_id, update_data, mock_user, mock_db, mock_background)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_update_whiteboard_success(self):
        """Test update_whiteboard updates whiteboard for owner."""
        from app.routers.whiteboards import update_whiteboard

        whiteboard_id = uuid4()
        owner_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = owner_id
        mock_user.username = "owner"

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.name = "Original"
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.owner = mock_user
        mock_whiteboard.access_type = AccessType.PUBLIC
        mock_whiteboard.shared_with = []
        mock_whiteboard.created_at = datetime.now(timezone.utc)
        mock_whiteboard.updated_at = datetime.now(timezone.utc)

        update_data = WhiteboardUpdate(name="Updated Name")

        mock_db = AsyncMock()

        # First call returns whiteboard for update check
        first_result = MagicMock()
        first_result.scalar_one_or_none.return_value = mock_whiteboard

        # Update the mock whiteboard name
        updated_wb = MagicMock(spec=Whiteboard)
        updated_wb.id = whiteboard_id
        updated_wb.name = "Updated Name"
        updated_wb.owner_id = owner_id
        updated_wb.owner = mock_user
        updated_wb.access_type = AccessType.PUBLIC
        updated_wb.shared_with = []
        updated_wb.created_at = datetime.now(timezone.utc)
        updated_wb.updated_at = datetime.now(timezone.utc)

        # Second call returns updated whiteboard
        second_result = MagicMock()
        second_result.scalar_one.return_value = updated_wb

        mock_db.execute.side_effect = [first_result, second_result]

        mock_background = MagicMock()

        response = await update_whiteboard(whiteboard_id, update_data, mock_user, mock_db, mock_background)

        assert response.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_whiteboard_not_found(self):
        """Test delete_whiteboard raises 404 for nonexistent whiteboard."""
        from app.routers.whiteboards import delete_whiteboard
        from fastapi import HTTPException

        whiteboard_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        mock_background = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await delete_whiteboard(whiteboard_id, mock_user, mock_db, mock_background)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_whiteboard_access_denied(self):
        """Test delete_whiteboard raises 403 for non-admin user."""
        from app.routers.whiteboards import delete_whiteboard
        from fastapi import HTTPException

        whiteboard_id = uuid4()
        owner_id = uuid4()
        user_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.access_type = AccessType.PUBLIC
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        mock_background = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await delete_whiteboard(whiteboard_id, mock_user, mock_db, mock_background)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_whiteboard_success(self):
        """Test delete_whiteboard deletes whiteboard for owner."""
        from app.routers.whiteboards import delete_whiteboard

        whiteboard_id = uuid4()
        owner_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = owner_id
        mock_user.username = "owner"

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.access_type = AccessType.PRIVATE
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        mock_background = MagicMock()

        await delete_whiteboard(whiteboard_id, mock_user, mock_db, mock_background)

        mock_db.delete.assert_called_once_with(mock_whiteboard)

    @pytest.mark.asyncio
    async def test_delete_whiteboard_public_broadcasts(self):
        """Test delete_whiteboard broadcasts for public whiteboard."""
        from app.routers.whiteboards import delete_whiteboard

        whiteboard_id = uuid4()
        owner_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = owner_id
        mock_user.username = "owner"

        mock_whiteboard = MagicMock(spec=Whiteboard)
        mock_whiteboard.id = whiteboard_id
        mock_whiteboard.owner_id = owner_id
        mock_whiteboard.access_type = AccessType.PUBLIC
        mock_whiteboard.shared_with = []

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_whiteboard
        mock_db.execute.return_value = mock_result

        mock_background = MagicMock()

        await delete_whiteboard(whiteboard_id, mock_user, mock_db, mock_background)

        # Should add broadcast task for public whiteboard
        mock_background.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_users_success(self):
        """Test search_users returns matching users."""
        from app.routers.whiteboards import search_users

        user_id = uuid4()
        other_user_id = uuid4()

        mock_user = MagicMock(spec=User)
        mock_user.id = user_id

        mock_other_user = MagicMock(spec=User)
        mock_other_user.id = other_user_id
        mock_other_user.username = "otheruser"
        mock_other_user.first_name = "Other"
        mock_other_user.last_name = "User"
        mock_other_user.created_at = datetime.now(timezone.utc)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_other_user]
        mock_db.execute.return_value = mock_result

        response = await search_users("other", mock_user, mock_db)

        assert len(response) == 1
        assert response[0].username == "otheruser"

    @pytest.mark.asyncio
    async def test_search_users_short_query(self):
        """Test search_users returns empty for short query."""
        from app.routers.whiteboards import search_users

        mock_user = MagicMock(spec=User)
        mock_user.id = uuid4()

        mock_db = AsyncMock()

        response = await search_users("a", mock_user, mock_db)

        assert response == []
        mock_db.execute.assert_not_called()


class TestWhiteboardsBroadcast:
    """Tests for whiteboard broadcast functions."""

    @pytest.mark.asyncio
    async def test_broadcast_whiteboard_event_success(self):
        """Test broadcast_whiteboard_event publishes to NATS."""
        from app.routers.whiteboards import broadcast_whiteboard_event

        whiteboard_id = uuid4()
        event_type = "whiteboard_updated"
        data = {"id": str(whiteboard_id), "name": "Test"}
        by_user = {"id": str(uuid4()), "username": "testuser"}

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish_whiteboard_event = AsyncMock()

            await broadcast_whiteboard_event(whiteboard_id, event_type, data, by_user)

            mock_nats.publish_whiteboard_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_whiteboard_event_handles_failure(self):
        """Test broadcast_whiteboard_event logs warning on failure."""
        from app.routers.whiteboards import broadcast_whiteboard_event

        whiteboard_id = uuid4()
        event_type = "whiteboard_updated"
        data = {"id": str(whiteboard_id)}
        by_user = {"id": str(uuid4()), "username": "testuser"}

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish_whiteboard_event = AsyncMock(side_effect=Exception("NATS error"))

            # Should not raise
            await broadcast_whiteboard_event(whiteboard_id, event_type, data, by_user)

    @pytest.mark.asyncio
    async def test_broadcast_global_whiteboard_event_success(self):
        """Test broadcast_global_whiteboard_event publishes to NATS."""
        from app.routers.whiteboards import broadcast_global_whiteboard_event

        event_type = "whiteboard_created"
        data = {"id": str(uuid4()), "name": "Test"}
        by_user = {"id": str(uuid4()), "username": "testuser"}

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish = AsyncMock()

            await broadcast_global_whiteboard_event(event_type, data, by_user)

            mock_nats.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_global_whiteboard_event_handles_failure(self):
        """Test broadcast_global_whiteboard_event logs warning on failure."""
        from app.routers.whiteboards import broadcast_global_whiteboard_event

        event_type = "whiteboard_deleted"
        data = {"id": str(uuid4())}
        by_user = {"id": str(uuid4()), "username": "testuser"}

        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish = AsyncMock(side_effect=Exception("NATS error"))

            # Should not raise
            await broadcast_global_whiteboard_event(event_type, data, by_user)


class TestBroadcastNoteEvent:
    """Tests for broadcast_note_event function."""

    @pytest.mark.asyncio
    async def test_broadcast_note_event_success(self):
        """Test broadcast_note_event publishes to NATS."""
        from app.routers.notes import broadcast_note_event

        whiteboard_id = uuid4()
        event_type = "note_created"
        note_data = {"id": str(uuid4()), "title": "Test"}
        by_user = {"id": str(uuid4()), "username": "testuser"}

        # nats_client is imported inside the function from app.messaging
        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish_note_event = AsyncMock()

            await broadcast_note_event(whiteboard_id, event_type, note_data, by_user)

            mock_nats.publish_note_event.assert_called_once_with(
                whiteboard_id, event_type, note_data, by_user
            )

    @pytest.mark.asyncio
    async def test_broadcast_note_event_handles_failure(self):
        """Test broadcast_note_event logs warning on failure."""
        from app.routers.notes import broadcast_note_event

        whiteboard_id = uuid4()
        event_type = "note_created"
        note_data = {"id": str(uuid4())}
        by_user = {"id": str(uuid4()), "username": "testuser"}

        # nats_client is imported inside the function from app.messaging
        with patch("app.messaging.nats_client") as mock_nats:
            mock_nats.publish_note_event = AsyncMock(side_effect=Exception("NATS error"))

            # Should not raise, just log warning
            await broadcast_note_event(whiteboard_id, event_type, note_data, by_user)
