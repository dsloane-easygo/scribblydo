"""Tests for notes endpoints."""

import pytest
from httpx import AsyncClient


class TestListNotes:
    """Tests for GET /api/notes."""

    @pytest.mark.asyncio
    async def test_list_notes_empty(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test listing notes when whiteboard is empty."""
        response = await client.get(
            f"/api/notes?whiteboard_id={test_whiteboard['id']}",
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["notes"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_notes_with_notes(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict, test_note: dict
    ):
        """Test listing notes returns created notes."""
        response = await client.get(
            f"/api/notes?whiteboard_id={test_whiteboard['id']}",
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["total"] >= 1
        assert any(n["id"] == test_note["id"] for n in data["notes"])

    @pytest.mark.asyncio
    async def test_list_notes_no_whiteboard_id(self, client: AsyncClient, test_user: dict):
        """Test listing notes without whiteboard_id fails."""
        response = await client.get("/api/notes", headers=test_user["headers"])
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_notes_nonexistent_whiteboard(
        self, client: AsyncClient, test_user: dict
    ):
        """Test listing notes from nonexistent whiteboard fails."""
        response = await client.get(
            "/api/notes?whiteboard_id=00000000-0000-0000-0000-000000000000",
            headers=test_user["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_notes_private_whiteboard_by_other_user(
        self, client: AsyncClient, test_user: dict, second_user: dict, private_whiteboard: dict
    ):
        """Test non-owner cannot list notes from private whiteboard."""
        response = await client.get(
            f"/api/notes?whiteboard_id={private_whiteboard['id']}",
            headers=second_user["headers"],
        )
        assert response.status_code == 403


class TestCreateNote:
    """Tests for POST /api/notes."""

    @pytest.mark.asyncio
    async def test_create_note_success(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test successful note creation."""
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": test_whiteboard["id"],
                "title": "New Note",
                "content": "Note content",
                "color": "#FF5733",
                "x_position": 50.0,
                "y_position": 75.0,
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201

        data = response.json()
        assert data["title"] == "New Note"
        assert data["content"] == "Note content"
        assert data["color"] == "#FF5733"
        assert data["x_position"] == 50.0
        assert data["y_position"] == 75.0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_note_default_values(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test creating note with default values."""
        response = await client.post(
            "/api/notes",
            json={"whiteboard_id": test_whiteboard["id"]},
            headers=test_user["headers"],
        )
        assert response.status_code == 201

        data = response.json()
        assert data["title"] == ""
        assert data["content"] == ""
        assert data["color"] == "#FFEB3B"
        assert data["x_position"] == 0.0
        assert data["y_position"] == 0.0
        assert data["width"] == 200.0
        assert data["height"] == 180.0

    @pytest.mark.asyncio
    async def test_create_note_with_custom_dimensions(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test creating note with custom width and height."""
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": test_whiteboard["id"],
                "title": "Resized Note",
                "width": 350.0,
                "height": 280.0,
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201

        data = response.json()
        assert data["width"] == 350.0
        assert data["height"] == 280.0

    @pytest.mark.asyncio
    async def test_create_note_invalid_color(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test creating note with invalid color fails."""
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": test_whiteboard["id"],
                "color": "not-a-color",
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_note_negative_position(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test creating note with negative position fails."""
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": test_whiteboard["id"],
                "x_position": -10.0,
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_note_nonexistent_whiteboard(
        self, client: AsyncClient, test_user: dict
    ):
        """Test creating note on nonexistent whiteboard fails."""
        response = await client.post(
            "/api/notes",
            json={"whiteboard_id": "00000000-0000-0000-0000-000000000000"},
            headers=test_user["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_note_on_private_whiteboard_by_other_user(
        self, client: AsyncClient, test_user: dict, second_user: dict, private_whiteboard: dict
    ):
        """Test non-owner cannot create notes on private whiteboard."""
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": private_whiteboard["id"],
                "title": "Unauthorized Note",
            },
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_note_on_public_whiteboard_by_other_user(
        self, client: AsyncClient, test_user: dict, second_user: dict, test_whiteboard: dict
    ):
        """Test any user can create notes on public whiteboard."""
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": test_whiteboard["id"],
                "title": "Collaborative Note",
            },
            headers=second_user["headers"],
        )
        assert response.status_code == 201


class TestGetNote:
    """Tests for GET /api/notes/{note_id}."""

    @pytest.mark.asyncio
    async def test_get_note_success(
        self, client: AsyncClient, test_user: dict, test_note: dict
    ):
        """Test getting a note by ID."""
        response = await client.get(
            f"/api/notes/{test_note['id']}",
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == test_note["id"]
        assert data["title"] == test_note["title"]

    @pytest.mark.asyncio
    async def test_get_note_not_found(self, client: AsyncClient, test_user: dict):
        """Test getting nonexistent note returns 404."""
        response = await client.get(
            "/api/notes/00000000-0000-0000-0000-000000000000",
            headers=test_user["headers"],
        )
        assert response.status_code == 404


class TestUpdateNote:
    """Tests for PUT /api/notes/{note_id}."""

    @pytest.mark.asyncio
    async def test_update_note_title(
        self, client: AsyncClient, test_user: dict, test_note: dict
    ):
        """Test updating note title."""
        response = await client.put(
            f"/api/notes/{test_note['id']}",
            json={"title": "Updated Title"},
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Updated Title"
        # Other fields should remain unchanged
        assert data["content"] == test_note["content"]

    @pytest.mark.asyncio
    async def test_update_note_position(
        self, client: AsyncClient, test_user: dict, test_note: dict
    ):
        """Test updating note position."""
        response = await client.put(
            f"/api/notes/{test_note['id']}",
            json={"x_position": 300.0, "y_position": 400.0},
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["x_position"] == 300.0
        assert data["y_position"] == 400.0

    @pytest.mark.asyncio
    async def test_update_note_color(
        self, client: AsyncClient, test_user: dict, test_note: dict
    ):
        """Test updating note color."""
        response = await client.put(
            f"/api/notes/{test_note['id']}",
            json={"color": "#00FF00"},
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["color"] == "#00FF00"

    @pytest.mark.asyncio
    async def test_update_note_dimensions(
        self, client: AsyncClient, test_user: dict, test_note: dict
    ):
        """Test updating note width and height."""
        response = await client.put(
            f"/api/notes/{test_note['id']}",
            json={"width": 300.0, "height": 250.0},
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["width"] == 300.0
        assert data["height"] == 250.0

    @pytest.mark.asyncio
    async def test_update_note_dimensions_invalid_too_small(
        self, client: AsyncClient, test_user: dict, test_note: dict
    ):
        """Test updating note with dimensions below minimum fails."""
        response = await client.put(
            f"/api/notes/{test_note['id']}",
            json={"width": 50.0},
            headers=test_user["headers"],
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_note_dimensions_invalid_too_large(
        self, client: AsyncClient, test_user: dict, test_note: dict
    ):
        """Test updating note with dimensions above maximum fails."""
        response = await client.put(
            f"/api/notes/{test_note['id']}",
            json={"height": 1000.0},
            headers=test_user["headers"],
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_note_by_other_user_on_public_whiteboard(
        self, client: AsyncClient, test_user: dict, second_user: dict, test_note: dict
    ):
        """Test any user can update notes on public whiteboard (collaborative)."""
        response = await client.put(
            f"/api/notes/{test_note['id']}",
            json={"title": "Updated by Other User"},
            headers=second_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Updated by Other User"

    @pytest.mark.asyncio
    async def test_update_note_not_found(self, client: AsyncClient, test_user: dict):
        """Test updating nonexistent note returns 404."""
        response = await client.put(
            "/api/notes/00000000-0000-0000-0000-000000000000",
            json={"title": "New Title"},
            headers=test_user["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_note_invalid_color(
        self, client: AsyncClient, test_user: dict, test_note: dict
    ):
        """Test updating note with invalid color fails."""
        response = await client.put(
            f"/api/notes/{test_note['id']}",
            json={"color": "invalid"},
            headers=test_user["headers"],
        )
        assert response.status_code == 422


class TestDeleteNote:
    """Tests for DELETE /api/notes/{note_id}."""

    @pytest.mark.asyncio
    async def test_delete_note_success(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test successful note deletion."""
        # Create note to delete
        create_response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": test_whiteboard["id"],
                "title": "To Delete",
            },
            headers=test_user["headers"],
        )
        note_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(
            f"/api/notes/{note_id}",
            headers=test_user["headers"],
        )
        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(
            f"/api/notes/{note_id}",
            headers=test_user["headers"],
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_note_by_other_user_on_public_whiteboard(
        self, client: AsyncClient, test_user: dict, second_user: dict, test_note: dict
    ):
        """Test any user can delete notes on public whiteboard (collaborative)."""
        response = await client.delete(
            f"/api/notes/{test_note['id']}",
            headers=second_user["headers"],
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_note_not_found(self, client: AsyncClient, test_user: dict):
        """Test deleting nonexistent note returns 404."""
        response = await client.delete(
            "/api/notes/00000000-0000-0000-0000-000000000000",
            headers=test_user["headers"],
        )
        assert response.status_code == 404


class TestNoteAccessControl:
    """Tests for note access control on private/shared whiteboards."""

    @pytest.mark.asyncio
    async def test_note_on_private_whiteboard_accessible_by_owner(
        self, client: AsyncClient, test_user: dict, private_whiteboard: dict
    ):
        """Test owner can create and access notes on private whiteboard."""
        # Create note
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": private_whiteboard["id"],
                "title": "Private Note",
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        note_id = response.json()["id"]

        # Read note
        response = await client.get(
            f"/api/notes/{note_id}",
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        # Update note
        response = await client.put(
            f"/api/notes/{note_id}",
            json={"title": "Updated Private Note"},
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        # Delete note
        response = await client.delete(
            f"/api/notes/{note_id}",
            headers=test_user["headers"],
        )
        assert response.status_code == 204


class TestNotePermissions:
    """Tests for note operations with different permission levels."""

    @pytest.mark.asyncio
    async def test_read_user_can_list_notes(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with read permission can list notes."""
        # Create shared whiteboard with second user as read-only
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Read Notes Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "read"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Owner creates a note
        response = await client.post(
            "/api/notes",
            json={"whiteboard_id": wb_id, "title": "Test Note"},
            headers=test_user["headers"],
        )
        assert response.status_code == 201

        # Read user can list notes
        response = await client.get(
            f"/api/notes?whiteboard_id={wb_id}",
            headers=second_user["headers"],
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1

    @pytest.mark.asyncio
    async def test_read_user_cannot_create_note(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with read permission cannot create notes."""
        # Create shared whiteboard with second user as read-only
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "No Create Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "read"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Read user tries to create a note
        response = await client.post(
            "/api/notes",
            json={"whiteboard_id": wb_id, "title": "Unauthorized Note"},
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_read_user_cannot_update_note(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with read permission cannot update notes."""
        # Create shared whiteboard with second user as read-only
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "No Update Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "read"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Owner creates a note
        response = await client.post(
            "/api/notes",
            json={"whiteboard_id": wb_id, "title": "Original Title"},
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        note_id = response.json()["id"]

        # Read user tries to update the note
        response = await client.put(
            f"/api/notes/{note_id}",
            json={"title": "Hacked Title"},
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_read_user_cannot_delete_note(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with read permission cannot delete notes."""
        # Create shared whiteboard with second user as read-only
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "No Delete Notes Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "read"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Owner creates a note
        response = await client.post(
            "/api/notes",
            json={"whiteboard_id": wb_id, "title": "Do Not Delete"},
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        note_id = response.json()["id"]

        # Read user tries to delete the note
        response = await client.delete(
            f"/api/notes/{note_id}",
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_write_user_can_create_note(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with write permission can create notes."""
        # Create shared whiteboard with second user as write
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Write Notes Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "write"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Write user creates a note
        response = await client.post(
            "/api/notes",
            json={"whiteboard_id": wb_id, "title": "Collaborative Note"},
            headers=second_user["headers"],
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_write_user_can_update_note(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with write permission can update notes."""
        # Create shared whiteboard with second user as write
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Update Notes Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "write"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Owner creates a note
        response = await client.post(
            "/api/notes",
            json={"whiteboard_id": wb_id, "title": "Original"},
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        note_id = response.json()["id"]

        # Write user updates the note
        response = await client.put(
            f"/api/notes/{note_id}",
            json={"title": "Updated by Collaborator"},
            headers=second_user["headers"],
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated by Collaborator"

    @pytest.mark.asyncio
    async def test_write_user_can_delete_note(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with write permission can delete notes."""
        # Create shared whiteboard with second user as write
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Delete Notes Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "write"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Owner creates a note
        response = await client.post(
            "/api/notes",
            json={"whiteboard_id": wb_id, "title": "To Delete"},
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        note_id = response.json()["id"]

        # Write user deletes the note
        response = await client.delete(
            f"/api/notes/{note_id}",
            headers=second_user["headers"],
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_admin_user_can_perform_all_note_operations(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with admin permission can do all note operations."""
        # Create shared whiteboard with second user as admin
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Admin Notes Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "admin"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Admin creates a note
        response = await client.post(
            "/api/notes",
            json={"whiteboard_id": wb_id, "title": "Admin Note"},
            headers=second_user["headers"],
        )
        assert response.status_code == 201
        note_id = response.json()["id"]

        # Admin updates the note
        response = await client.put(
            f"/api/notes/{note_id}",
            json={"title": "Updated by Admin"},
            headers=second_user["headers"],
        )
        assert response.status_code == 200

        # Admin deletes the note
        response = await client.delete(
            f"/api/notes/{note_id}",
            headers=second_user["headers"],
        )
        assert response.status_code == 204
