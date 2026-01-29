"""Pytest fixtures for e2e testing."""

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app

# Test database URL - use env var or default to test database
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/todo_whiteboard_test"
)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a fresh engine for each test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session_factory(test_engine):
    """Create session factory for each test."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture(scope="function")
async def client(test_engine, test_session_factory) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with database override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        """Override database dependency for tests."""
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create tables before tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_user(client: AsyncClient) -> dict:
    """Create a test user and return user data with token."""
    # Register user
    response = await client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "testpass123"},
    )
    assert response.status_code == 201
    user_data = response.json()

    # Login to get token
    response = await client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    assert response.status_code == 200
    token_data = response.json()

    return {
        "id": user_data["id"],
        "username": user_data["username"],
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
    }


@pytest_asyncio.fixture
async def second_user(client: AsyncClient) -> dict:
    """Create a second test user for multi-user tests."""
    response = await client.post(
        "/api/auth/register",
        json={"username": "seconduser", "password": "testpass123"},
    )
    assert response.status_code == 201
    user_data = response.json()

    response = await client.post(
        "/api/auth/login",
        data={"username": "seconduser", "password": "testpass123"},
    )
    assert response.status_code == 200
    token_data = response.json()

    return {
        "id": user_data["id"],
        "username": user_data["username"],
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
    }


@pytest_asyncio.fixture
async def test_whiteboard(client: AsyncClient, test_user: dict) -> dict:
    """Create a test whiteboard."""
    response = await client.post(
        "/api/whiteboards",
        json={"name": "Test Whiteboard", "access_type": "public"},
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def private_whiteboard(client: AsyncClient, test_user: dict) -> dict:
    """Create a private test whiteboard."""
    response = await client.post(
        "/api/whiteboards",
        json={"name": "Private Whiteboard", "access_type": "private"},
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def test_note(client: AsyncClient, test_user: dict, test_whiteboard: dict) -> dict:
    """Create a test note on the test whiteboard."""
    response = await client.post(
        "/api/notes",
        json={
            "whiteboard_id": test_whiteboard["id"],
            "title": "Test Note",
            "content": "Test content",
            "color": "#FFEB3B",
            "x_position": 100.0,
            "y_position": 200.0,
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    return response.json()
