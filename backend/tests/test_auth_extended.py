"""Extended tests for authentication module."""

import pytest
import pytest_asyncio
from datetime import timedelta
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
)


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    """Tests for JWT token operations."""

    def test_create_access_token(self):
        """Test creating access token."""
        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id})

        assert token is not None
        assert isinstance(token, str)

    def test_create_access_token_with_custom_expiry(self):
        """Test creating access token with custom expiry."""
        user_id = str(uuid4())
        token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(hours=1),
        )

        assert token is not None

    def test_decode_valid_token(self):
        """Test decoding valid token."""
        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id})

        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == user_id

    def test_decode_invalid_token(self):
        """Test decoding invalid token returns None."""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_malformed_token(self):
        """Test decoding malformed token returns None."""
        payload = decode_token("notavalidjwt")
        assert payload is None


class TestAuthEndpoints:
    """Tests for auth API endpoints."""

    @pytest.mark.asyncio
    async def test_register_with_names(self, client):
        """Test registration with first and last names."""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "nameduser",
                "password": "testpass123",
                "first_name": "John",
                "last_name": "Doe",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "nameduser"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"

    @pytest.mark.asyncio
    async def test_register_without_names(self, client):
        """Test registration without optional names."""
        response = await client.post(
            "/api/auth/register",
            json={
                "username": "nonames",
                "password": "testpass123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "nonames"
        assert data["first_name"] is None
        assert data["last_name"] is None

    @pytest.mark.asyncio
    async def test_login_returns_token_type(self, client, test_user):
        """Test that login returns correct token type."""
        response = await client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_get_me_returns_full_user(self, client, test_user):
        """Test that /me returns complete user information."""
        response = await client.get(
            "/api/auth/me",
            headers=test_user["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user["id"]
        assert data["username"] == test_user["username"]
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_expired_token_rejected(self, client):
        """Test that expired tokens are rejected."""
        # Create a token that expired 1 hour ago
        from datetime import datetime, timezone
        user_id = str(uuid4())
        token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(hours=-1),  # Already expired
        )

        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_without_sub_rejected(self, client):
        """Test that tokens without sub claim are rejected."""
        from jose import jwt
        from app.auth import SECRET_KEY, ALGORITHM

        # Create a token without sub claim
        token = jwt.encode({"exp": datetime.now(timezone.utc) + timedelta(hours=1)}, SECRET_KEY, algorithm=ALGORITHM)

        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_with_invalid_uuid_rejected(self, client):
        """Test that tokens with invalid UUID are rejected."""
        token = create_access_token(data={"sub": "not-a-uuid"})

        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_with_nonexistent_user_rejected(self, client):
        """Test that tokens for non-existent users are rejected."""
        # Create token for user that doesn't exist
        fake_user_id = str(uuid4())
        token = create_access_token(data={"sub": fake_user_id})

        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


# Import datetime for the tests above
from datetime import datetime, timezone
