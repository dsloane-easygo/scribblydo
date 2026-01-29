"""Tests for whiteboard endpoints."""

import pytest
from httpx import AsyncClient


class TestListWhiteboards:
    """Tests for GET /api/whiteboards."""

    @pytest.mark.asyncio
    async def test_list_whiteboards_empty(self, client: AsyncClient, test_user: dict):
        """Test listing whiteboards when none exist."""
        response = await client.get("/api/whiteboards", headers=test_user["headers"])
        assert response.status_code == 200

        data = response.json()
        assert data["whiteboards"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_whiteboards_with_whiteboards(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test listing whiteboards returns created whiteboards."""
        response = await client.get("/api/whiteboards", headers=test_user["headers"])
        assert response.status_code == 200

        data = response.json()
        assert data["total"] >= 1
        assert any(wb["id"] == test_whiteboard["id"] for wb in data["whiteboards"])

    @pytest.mark.asyncio
    async def test_list_whiteboards_no_auth(self, client: AsyncClient):
        """Test listing whiteboards without auth fails."""
        response = await client.get("/api/whiteboards")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_whiteboards_shows_public_from_other_users(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that public whiteboards from other users are visible."""
        # First user creates a public whiteboard
        response = await client.post(
            "/api/whiteboards",
            json={"name": "Public Board", "access_type": "public"},
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        public_wb = response.json()

        # Second user should see it
        response = await client.get("/api/whiteboards", headers=second_user["headers"])
        assert response.status_code == 200

        data = response.json()
        assert any(wb["id"] == public_wb["id"] for wb in data["whiteboards"])

    @pytest.mark.asyncio
    async def test_list_whiteboards_hides_private_from_other_users(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that private whiteboards from other users are not visible."""
        # First user creates a private whiteboard
        response = await client.post(
            "/api/whiteboards",
            json={"name": "Private Board", "access_type": "private"},
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        private_wb = response.json()

        # Second user should NOT see it
        response = await client.get("/api/whiteboards", headers=second_user["headers"])
        assert response.status_code == 200

        data = response.json()
        assert not any(wb["id"] == private_wb["id"] for wb in data["whiteboards"])


class TestCreateWhiteboard:
    """Tests for POST /api/whiteboards."""

    @pytest.mark.asyncio
    async def test_create_whiteboard_success(self, client: AsyncClient, test_user: dict):
        """Test successful whiteboard creation."""
        response = await client.post(
            "/api/whiteboards",
            json={"name": "My New Board"},
            headers=test_user["headers"],
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "My New Board"
        assert data["owner_id"] == test_user["id"]
        assert data["owner_username"] == test_user["username"]
        assert data["access_type"] == "public"  # default
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_whiteboard_private(self, client: AsyncClient, test_user: dict):
        """Test creating a private whiteboard."""
        response = await client.post(
            "/api/whiteboards",
            json={"name": "Secret Board", "access_type": "private"},
            headers=test_user["headers"],
        )
        assert response.status_code == 201

        data = response.json()
        assert data["access_type"] == "private"

    @pytest.mark.asyncio
    async def test_create_whiteboard_shared(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test creating a shared whiteboard with permissions."""
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Shared Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "write"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201

        data = response.json()
        assert data["access_type"] == "shared"
        assert len(data["shared_with"]) == 1
        assert data["shared_with"][0]["id"] == second_user["id"]
        assert data["shared_with"][0]["permission"] == "write"

    @pytest.mark.asyncio
    async def test_create_whiteboard_shared_with_admin(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test creating a shared whiteboard with admin permission."""
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Admin Shared Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "admin"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201

        data = response.json()
        assert data["shared_with"][0]["permission"] == "admin"

    @pytest.mark.asyncio
    async def test_create_whiteboard_no_auth(self, client: AsyncClient):
        """Test creating whiteboard without auth fails."""
        response = await client.post(
            "/api/whiteboards",
            json={"name": "Unauthorized Board"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_whiteboard_empty_name(self, client: AsyncClient, test_user: dict):
        """Test creating whiteboard with empty name fails."""
        response = await client.post(
            "/api/whiteboards",
            json={"name": ""},
            headers=test_user["headers"],
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_whiteboard_long_name(self, client: AsyncClient, test_user: dict):
        """Test creating whiteboard with too long name fails."""
        response = await client.post(
            "/api/whiteboards",
            json={"name": "x" * 300},
            headers=test_user["headers"],
        )
        assert response.status_code == 422


class TestGetWhiteboard:
    """Tests for GET /api/whiteboards/{whiteboard_id}."""

    @pytest.mark.asyncio
    async def test_get_whiteboard_success(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test getting a whiteboard by ID."""
        response = await client.get(
            f"/api/whiteboards/{test_whiteboard['id']}",
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == test_whiteboard["id"]
        assert data["name"] == test_whiteboard["name"]

    @pytest.mark.asyncio
    async def test_get_whiteboard_not_found(self, client: AsyncClient, test_user: dict):
        """Test getting nonexistent whiteboard returns 404."""
        response = await client.get(
            "/api/whiteboards/00000000-0000-0000-0000-000000000000",
            headers=test_user["headers"],
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_private_whiteboard_by_owner(
        self, client: AsyncClient, test_user: dict, private_whiteboard: dict
    ):
        """Test owner can access private whiteboard."""
        response = await client.get(
            f"/api/whiteboards/{private_whiteboard['id']}",
            headers=test_user["headers"],
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_private_whiteboard_by_other_user(
        self, client: AsyncClient, test_user: dict, second_user: dict, private_whiteboard: dict
    ):
        """Test non-owner cannot access private whiteboard."""
        response = await client.get(
            f"/api/whiteboards/{private_whiteboard['id']}",
            headers=second_user["headers"],
        )
        assert response.status_code == 403


class TestUpdateWhiteboard:
    """Tests for PUT /api/whiteboards/{whiteboard_id}."""

    @pytest.mark.asyncio
    async def test_update_whiteboard_name(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test updating whiteboard name."""
        response = await client.put(
            f"/api/whiteboards/{test_whiteboard['id']}",
            json={"name": "Updated Name"},
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_whiteboard_access_type(
        self, client: AsyncClient, test_user: dict, test_whiteboard: dict
    ):
        """Test updating whiteboard access type."""
        response = await client.put(
            f"/api/whiteboards/{test_whiteboard['id']}",
            json={"access_type": "private"},
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["access_type"] == "private"

    @pytest.mark.asyncio
    async def test_update_whiteboard_by_non_owner(
        self, client: AsyncClient, test_user: dict, second_user: dict, test_whiteboard: dict
    ):
        """Test non-owner cannot update whiteboard."""
        response = await client.put(
            f"/api/whiteboards/{test_whiteboard['id']}",
            json={"name": "Hacked Name"},
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_whiteboard_not_found(self, client: AsyncClient, test_user: dict):
        """Test updating nonexistent whiteboard returns 404."""
        response = await client.put(
            "/api/whiteboards/00000000-0000-0000-0000-000000000000",
            json={"name": "New Name"},
            headers=test_user["headers"],
        )
        assert response.status_code == 404


class TestDeleteWhiteboard:
    """Tests for DELETE /api/whiteboards/{whiteboard_id}."""

    @pytest.mark.asyncio
    async def test_delete_whiteboard_success(self, client: AsyncClient, test_user: dict):
        """Test successful whiteboard deletion."""
        # Create whiteboard to delete
        create_response = await client.post(
            "/api/whiteboards",
            json={"name": "To Delete"},
            headers=test_user["headers"],
        )
        wb_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(
            f"/api/whiteboards/{wb_id}",
            headers=test_user["headers"],
        )
        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(
            f"/api/whiteboards/{wb_id}",
            headers=test_user["headers"],
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_whiteboard_by_non_owner(
        self, client: AsyncClient, test_user: dict, second_user: dict, test_whiteboard: dict
    ):
        """Test non-owner cannot delete whiteboard."""
        response = await client.delete(
            f"/api/whiteboards/{test_whiteboard['id']}",
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_whiteboard_not_found(self, client: AsyncClient, test_user: dict):
        """Test deleting nonexistent whiteboard returns 404."""
        response = await client.delete(
            "/api/whiteboards/00000000-0000-0000-0000-000000000000",
            headers=test_user["headers"],
        )
        assert response.status_code == 404


class TestSearchUsers:
    """Tests for GET /api/whiteboards/users/search."""

    @pytest.mark.asyncio
    async def test_search_users_success(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test searching for users."""
        response = await client.get(
            "/api/whiteboards/users/search?q=second",
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1
        assert any(u["username"] == "seconduser" for u in data)

    @pytest.mark.asyncio
    async def test_search_users_excludes_self(
        self, client: AsyncClient, test_user: dict
    ):
        """Test that search excludes the current user."""
        response = await client.get(
            "/api/whiteboards/users/search?q=test",
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert not any(u["id"] == test_user["id"] for u in data)

    @pytest.mark.asyncio
    async def test_search_users_short_query(self, client: AsyncClient, test_user: dict):
        """Test that short queries return empty results."""
        response = await client.get(
            "/api/whiteboards/users/search?q=a",
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data == []


class TestPermissions:
    """Tests for permission-based access control."""

    @pytest.mark.asyncio
    async def test_admin_user_can_update_whiteboard(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with admin permission can update the whiteboard."""
        # Create shared whiteboard with second user as admin
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Admin Test Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "admin"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Second user (admin) updates the whiteboard
        response = await client.put(
            f"/api/whiteboards/{wb_id}",
            json={"name": "Updated by Admin"},
            headers=second_user["headers"],
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated by Admin"

    @pytest.mark.asyncio
    async def test_admin_user_can_delete_whiteboard(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with admin permission can delete the whiteboard."""
        # Create shared whiteboard with second user as admin
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Delete Test Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "admin"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Second user (admin) deletes the whiteboard
        response = await client.delete(
            f"/api/whiteboards/{wb_id}",
            headers=second_user["headers"],
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_write_user_cannot_update_whiteboard(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with write permission cannot update whiteboard settings."""
        # Create shared whiteboard with second user as write-only
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Write Only Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "write"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Second user (write) tries to update the whiteboard
        response = await client.put(
            f"/api/whiteboards/{wb_id}",
            json={"name": "Hacked Name"},
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_write_user_cannot_delete_whiteboard(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with write permission cannot delete the whiteboard."""
        # Create shared whiteboard with second user as write-only
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "No Delete Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "write"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Second user (write) tries to delete the whiteboard
        response = await client.delete(
            f"/api/whiteboards/{wb_id}",
            headers=second_user["headers"],
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_read_user_can_view_whiteboard(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a user with read permission can view the whiteboard."""
        # Create shared whiteboard with second user as read-only
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Read Only Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "read"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Second user (read) can view the whiteboard
        response = await client.get(
            f"/api/whiteboards/{wb_id}",
            headers=second_user["headers"],
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_read_user_appears_in_whiteboard_list(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that a shared whiteboard appears in read user's list."""
        # Create shared whiteboard with second user as read-only
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Shared Read Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "read"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Second user sees it in their list
        response = await client.get("/api/whiteboards", headers=second_user["headers"])
        assert response.status_code == 200
        assert any(wb["id"] == wb_id for wb in response.json()["whiteboards"])

    @pytest.mark.asyncio
    async def test_admin_can_update_share_permissions(
        self, client: AsyncClient, test_user: dict, second_user: dict
    ):
        """Test that owner can update user permissions."""
        # Create a third user
        response = await client.post(
            "/api/auth/register",
            json={"username": "thirduser", "password": "testpass123"},
        )
        assert response.status_code == 201
        third_user_id = response.json()["id"]

        # Create shared whiteboard with second user
        response = await client.post(
            "/api/whiteboards",
            json={
                "name": "Permission Update Board",
                "access_type": "shared",
                "shared_with": [{"user_id": second_user["id"], "permission": "read"}],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 201
        wb_id = response.json()["id"]

        # Owner updates permissions - upgrade second user to admin, add third user
        response = await client.put(
            f"/api/whiteboards/{wb_id}",
            json={
                "shared_with": [
                    {"user_id": second_user["id"], "permission": "admin"},
                    {"user_id": third_user_id, "permission": "write"},
                ],
            },
            headers=test_user["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["shared_with"]) == 2
        second_share = next(s for s in data["shared_with"] if s["id"] == second_user["id"])
        assert second_share["permission"] == "admin"
