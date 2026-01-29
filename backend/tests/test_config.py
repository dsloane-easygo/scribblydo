"""Tests for application configuration."""

import os
import pytest
from unittest.mock import patch


class TestSettings:
    """Tests for Settings configuration."""

    def test_async_database_url_from_components(self):
        """Test async database URL constructed from components."""
        with patch.dict(os.environ, {
            "TESTING": "true",
            "DB_HOST": "testhost",
            "DB_PORT": "5433",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
        }, clear=False):
            # Clear the cache to get fresh settings
            from app.config import get_settings, Settings
            get_settings.cache_clear()

            settings = Settings(
                db_host="testhost",
                db_port=5433,
                db_name="testdb",
                db_user="testuser",
                db_password="testpass",
            )

            assert "testhost" in settings.async_database_url
            assert "5433" in settings.async_database_url
            assert "testdb" in settings.async_database_url
            assert "asyncpg" in settings.async_database_url

    def test_async_database_url_from_postgres_url(self):
        """Test async database URL converted from postgres:// URL."""
        with patch.dict(os.environ, {"TESTING": "true"}, clear=False):
            from app.config import Settings

            settings = Settings(database_url="postgres://user:pass@host:5432/db")

            assert settings.async_database_url == "postgresql+asyncpg://user:pass@host:5432/db"

    def test_async_database_url_from_postgresql_url(self):
        """Test async database URL converted from postgresql:// URL."""
        with patch.dict(os.environ, {"TESTING": "true"}, clear=False):
            from app.config import Settings

            settings = Settings(database_url="postgresql://user:pass@host:5432/db")

            assert settings.async_database_url == "postgresql+asyncpg://user:pass@host:5432/db"

    def test_sync_database_url_from_postgres_url(self):
        """Test sync database URL converted from postgres:// URL."""
        with patch.dict(os.environ, {"TESTING": "true"}, clear=False):
            from app.config import Settings

            settings = Settings(database_url="postgres://user:pass@host:5432/db")

            assert settings.sync_database_url == "postgresql://user:pass@host:5432/db"

    def test_sync_database_url_from_components(self):
        """Test sync database URL constructed from components."""
        with patch.dict(os.environ, {"TESTING": "true"}, clear=False):
            from app.config import Settings

            settings = Settings(
                db_host="testhost",
                db_port=5433,
                db_name="testdb",
                db_user="testuser",
                db_password="testpass",
            )

            assert "testhost" in settings.sync_database_url
            assert "5433" in settings.sync_database_url
            assert "testdb" in settings.sync_database_url
            assert "asyncpg" not in settings.sync_database_url

    def test_secret_key_validation_too_short(self):
        """Test that short secret keys are rejected."""
        with patch.dict(os.environ, {"TESTING": "false"}, clear=False):
            from app.config import Settings

            with pytest.raises(ValueError, match="at least 32 characters"):
                Settings(secret_key="tooshort")

    def test_secret_key_validation_empty_in_production(self):
        """Test that empty secret key raises error in production."""
        with patch.dict(os.environ, {"TESTING": "false"}, clear=False):
            from app.config import Settings

            with pytest.raises(ValueError, match="SECRET_KEY environment variable must be set"):
                Settings(secret_key="")

    def test_secret_key_auto_generated_in_test(self):
        """Test that secret key is auto-generated in test environment."""
        with patch.dict(os.environ, {"TESTING": "true"}, clear=False):
            from app.config import Settings

            settings = Settings(secret_key="")

            assert len(settings.secret_key) >= 32

    def test_default_cors_origins(self):
        """Test default CORS origins."""
        with patch.dict(os.environ, {"TESTING": "true"}, clear=False):
            from app.config import Settings

            settings = Settings()

            assert "http://localhost:3000" in settings.cors_origins
            assert "http://localhost:5173" in settings.cors_origins

    def test_default_nats_url(self):
        """Test default NATS URL when NATS_URL is not set."""
        # Clear NATS_URL to test the default value
        env_without_nats = {k: v for k, v in os.environ.items() if k != "NATS_URL"}
        env_without_nats["TESTING"] = "true"
        with patch.dict(os.environ, env_without_nats, clear=True):
            from app.config import Settings

            settings = Settings()

            assert settings.nats_url == "nats://nats:4222"
