"""Tests for permission checking utilities."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from uuid import uuid4

from app.models import AccessType, PermissionLevel


class TestPermissions:
    """Tests for permission utilities."""

    @pytest_asyncio.fixture
    async def shared_whiteboard_read(self, client: AsyncClient, test_user: dict, second_user: dict) -> dict:
        """Create a shared whiteboard with read-only access for second_user."""
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Shared Read Whiteboard",
                "access_type": "shared",
                "shared_with": [
                    {"user_id": second_user["id"], "permission": "read"}
                ],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        return response.json()

    @pytest_asyncio.fixture
    async def shared_whiteboard_write(self, client: AsyncClient, test_user: dict, second_user: dict) -> dict:
        """Create a shared whiteboard with write access for second_user."""
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Shared Write Whiteboard",
                "access_type": "shared",
                "shared_with": [
                    {"user_id": second_user["id"], "permission": "write"}
                ],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        return response.json()

    @pytest_asyncio.fixture
    async def shared_whiteboard_admin(self, client: AsyncClient, test_user: dict, second_user: dict) -> dict:
        """Create a shared whiteboard with admin access for second_user."""
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Shared Admin Whiteboard",
                "access_type": "shared",
                "shared_with": [
                    {"user_id": second_user["id"], "permission": "admin"}
                ],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        return response.json()

    @pytest.mark.asyncio
    async def test_owner_has_admin_access(self, client: AsyncClient, test_user: dict, private_whiteboard: dict):
        """Test that owner has admin access to their whiteboard."""
        # Owner can view
        response = await client.get(
            f"/api/whiteboards/{private_whiteboard['id']}",
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        # Owner can update
        response = await client.put(
            f"/api/whiteboards/{private_whiteboard['id']}",
            json={"name": "Updated Name"},
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        # Owner can delete
        response = await client.delete(
            f"/api/whiteboards/{private_whiteboard['id']}",
            headers=test_user["headers"],
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_no_access_to_private_whiteboard(self, client: AsyncClient, test_user: dict, second_user: dict, private_whiteboard: dict):
        """Test that users without access cannot view private whiteboard."""
        response = await client.get(
            f"/api/whiteboards/{private_whiteboard['id']}",
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_read_only_cannot_create_notes(self, client: AsyncClient, second_user: dict, shared_whiteboard_read: dict):
        """Test that read-only users cannot create notes."""
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": shared_whiteboard_read["id"],
                "title": "Test Note",
                "content": "Content",
                "color": "#FFEB3B",
                "x_position": 0.0,
                "y_position": 0.0,
            },
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_read_only_can_view_whiteboard(self, client: AsyncClient, second_user: dict, shared_whiteboard_read: dict):
        """Test that read-only users can view the whiteboard."""
        response = await client.get(
            f"/api/whiteboards/{shared_whiteboard_read['id']}",
            headers=second_user["headers"],
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_read_only_can_list_notes(self, client: AsyncClient, test_user: dict, second_user: dict, shared_whiteboard_read: dict):
        """Test that read-only users can list notes."""
        # First create a note as owner
        await client.post(
            "/api/notes",
            json={
                "whiteboard_id": shared_whiteboard_read["id"],
                "title": "Test Note",
                "content": "Content",
                "color": "#FFEB3B",
                "x_position": 0.0,
                "y_position": 0.0,
            },
            headers=test_user["headers"],
        )

        # Read-only user can list notes
        response = await client.get(
            f"/api/notes?whiteboard_id={shared_whiteboard_read['id']}",
            headers=second_user["headers"],
        )
        assert response.status_code == 200
        assert len(response.json()["notes"]) == 1

    @pytest.mark.asyncio
    async def test_write_user_can_create_notes(self, client: AsyncClient, second_user: dict, shared_whiteboard_write: dict):
        """Test that write users can create notes."""
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": shared_whiteboard_write["id"],
                "title": "Test Note",
                "content": "Content",
                "color": "#FFEB3B",
                "x_position": 0.0,
                "y_position": 0.0,
            },
            headers=second_user["headers"],
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_write_user_can_update_notes(self, client: AsyncClient, test_user: dict, second_user: dict, shared_whiteboard_write: dict):
        """Test that write users can update notes."""
        # Create a note as owner
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": shared_whiteboard_write["id"],
                "title": "Test Note",
                "content": "Content",
                "color": "#FFEB3B",
                "x_position": 0.0,
                "y_position": 0.0,
            },
            headers=test_user["headers"],
        )
        note_id = response.json()["id"]

        # Write user can update
        response = await client.put(
            f"/api/notes/{note_id}",
            json={"title": "Updated Title"},
            headers=second_user["headers"],
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_write_user_can_delete_notes(self, client: AsyncClient, test_user: dict, second_user: dict, shared_whiteboard_write: dict):
        """Test that write users can delete notes."""
        # Create a note as owner
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": shared_whiteboard_write["id"],
                "title": "Test Note",
                "content": "Content",
                "color": "#FFEB3B",
                "x_position": 0.0,
                "y_position": 0.0,
            },
            headers=test_user["headers"],
        )
        note_id = response.json()["id"]

        # Write user can delete
        response = await client.delete(
            f"/api/notes/{note_id}",
            headers=second_user["headers"],
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_write_user_cannot_update_whiteboard(self, client: AsyncClient, second_user: dict, shared_whiteboard_write: dict):
        """Test that write users cannot update whiteboard settings."""
        response = await client.put(
            f"/api/whiteboards/{shared_whiteboard_write['id']}",
            json={"name": "New Name"},
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_write_user_cannot_delete_whiteboard(self, client: AsyncClient, second_user: dict, shared_whiteboard_write: dict):
        """Test that write users cannot delete whiteboard."""
        response = await client.delete(
            f"/api/whiteboards/{shared_whiteboard_write['id']}",
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_user_can_update_whiteboard(self, client: AsyncClient, second_user: dict, shared_whiteboard_admin: dict):
        """Test that admin users can update whiteboard settings."""
        response = await client.put(
            f"/api/whiteboards/{shared_whiteboard_admin['id']}",
            json={"name": "Admin Updated Name"},
            headers=second_user["headers"],
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Admin Updated Name"

    @pytest.mark.asyncio
    async def test_admin_user_can_delete_whiteboard(self, client: AsyncClient, second_user: dict, shared_whiteboard_admin: dict):
        """Test that admin users can delete whiteboard."""
        response = await client.delete(
            f"/api/whiteboards/{shared_whiteboard_admin['id']}",
            headers=second_user["headers"],
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_public_whiteboard_allows_write(self, client: AsyncClient, second_user: dict, test_whiteboard: dict):
        """Test that public whiteboards allow write access to any user."""
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": test_whiteboard["id"],
                "title": "Test Note",
                "content": "Content",
                "color": "#FFEB3B",
                "x_position": 0.0,
                "y_position": 0.0,
            },
            headers=second_user["headers"],
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_whiteboard_not_found(self, client: AsyncClient, test_user: dict):
        """Test accessing non-existent whiteboard."""
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/whiteboards/{fake_id}",
            headers=test_user["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_note_not_found(self, client: AsyncClient, test_user: dict):
        """Test accessing non-existent note."""
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/notes/{fake_id}",
            headers=test_user["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_note_not_found(self, client: AsyncClient, test_user: dict):
        """Test updating non-existent note."""
        fake_id = str(uuid4())
        response = await client.put(
            f"/api/notes/{fake_id}",
            json={"title": "New Title"},
            headers=test_user["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_note_not_found(self, client: AsyncClient, test_user: dict):
        """Test deleting non-existent note."""
        fake_id = str(uuid4())
        response = await client.delete(
            f"/api/notes/{fake_id}",
            headers=test_user["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_read_only_cannot_update_notes(self, client: AsyncClient, test_user: dict, second_user: dict, shared_whiteboard_read: dict):
        """Test that read-only users cannot update notes."""
        # Create a note as owner
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": shared_whiteboard_read["id"],
                "title": "Test Note",
                "content": "Content",
                "color": "#FFEB3B",
                "x_position": 0.0,
                "y_position": 0.0,
            },
            headers=test_user["headers"],
        )
        note_id = response.json()["id"]

        # Read-only user cannot update
        response = await client.put(
            f"/api/notes/{note_id}",
            json={"title": "Updated Title"},
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_read_only_cannot_delete_notes(self, client: AsyncClient, test_user: dict, second_user: dict, shared_whiteboard_read: dict):
        """Test that read-only users cannot delete notes."""
        # Create a note as owner
        response = await client.post(
            "/api/notes",
            json={
                "whiteboard_id": shared_whiteboard_read["id"],
                "title": "Test Note",
                "content": "Content",
                "color": "#FFEB3B",
                "x_position": 0.0,
                "y_position": 0.0,
            },
            headers=test_user["headers"],
        )
        note_id = response.json()["id"]

        # Read-only user cannot delete
        response = await client.delete(
            f"/api/notes/{note_id}",
            headers=second_user["headers"],
        )
        assert response.status_code == 403
