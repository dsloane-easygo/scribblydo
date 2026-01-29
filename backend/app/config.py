"""Application configuration using Pydantic Settings."""

import secrets
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application settings
    app_name: str = "Todo Whiteboard API"
    debug: bool = False

    # Database settings - either use DATABASE_URL or individual components
    database_url: Optional[str] = None

    # Individual database components (used if DATABASE_URL is not set)
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "todo_whiteboard"
    db_user: str = "postgres"
    db_password: str = "postgres"

    # CORS settings
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # JWT settings - MUST be set via SECRET_KEY environment variable in production
    secret_key: str = ""

    @field_validator("secret_key", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is set and secure."""
        insecure_defaults = [
            "",
            "change-me-in-production-use-a-long-random-string",
            "dev-secret-key-change-in-production",
            "k8s-dev-secret-key-change-in-production",
        ]
        if v in insecure_defaults:
            import os
            if os.getenv("TESTING", "").lower() == "true":
                # Allow insecure key only in test environment
                return secrets.token_urlsafe(32)
            raise ValueError(
                "SECRET_KEY environment variable must be set to a secure random value. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    # NATS settings
    nats_url: str = "nats://nats:4222"

    @property
    def async_database_url(self) -> str:
        """Get the async database URL for SQLAlchemy."""
        if self.database_url:
            # Convert postgres:// to postgresql+asyncpg://
            url = self.database_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def sync_database_url(self) -> str:
        """Get the sync database URL for Alembic migrations."""
        if self.database_url:
            url = self.database_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
