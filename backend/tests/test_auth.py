"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


class TestRegister:
    """Tests for POST /api/auth/register."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "password123"},
        )
        assert response.status_code == 201

        data = response.json()
        assert data["username"] == "newuser"
        assert "id" in data
        assert "created_at" in data
        # Password should not be returned
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        """Test registration with existing username fails."""
        # Register first user
        await client.post(
            "/api/auth/register",
            json={"username": "duplicate", "password": "password123"},
        )

        # Try to register with same username
        response = await client.post(
            "/api/auth/register",
            json={"username": "duplicate", "password": "differentpassword"},
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_short_username(self, client: AsyncClient):
        """Test registration with too short username fails."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "ab", "password": "password123"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with too short password fails."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "validuser", "password": "abc"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing fields fails."""
        response = await client.post("/api/auth/register", json={})
        assert response.status_code == 422

        response = await client.post(
            "/api/auth/register",
            json={"username": "onlyusername"},
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/auth/login."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Register user first
        await client.post(
            "/api/auth/register",
            json={"username": "loginuser", "password": "password123"},
        )

        # Login
        response = await client.post(
            "/api/auth/login",
            data={"username": "loginuser", "password": "password123"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login with wrong password fails."""
        await client.post(
            "/api/auth/register",
            json={"username": "wrongpassuser", "password": "correctpassword"},
        )

        response = await client.post(
            "/api/auth/login",
            data={"username": "wrongpassuser", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        response = await client.post(
            "/api/auth/login",
            data={"username": "doesnotexist", "password": "password123"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields fails."""
        response = await client.post("/api/auth/login", data={})
        assert response.status_code == 422


class TestGetMe:
    """Tests for GET /api/auth/me."""

    @pytest.mark.asyncio
    async def test_get_me_success(self, client: AsyncClient, test_user: dict):
        """Test getting current user info with valid token."""
        response = await client.get("/api/auth/me", headers=test_user["headers"])
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["id"] == test_user["id"]

    @pytest.mark.asyncio
    async def test_get_me_no_token(self, client: AsyncClient):
        """Test getting current user without token fails."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token fails."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401
