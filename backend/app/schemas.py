"""Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccessType(str, Enum):
    """Whiteboard access type."""
    PUBLIC = "public"
    PRIVATE = "private"
    SHARED = "shared"


class PermissionLevel(str, Enum):
    """Permission level for shared whiteboard access."""
    READ = "read"      # Can view whiteboard and notes
    WRITE = "write"    # Can view, create, edit, and delete notes
    ADMIN = "admin"    # Same as owner: can manage sharing, rename, delete whiteboard


# ============================================================================
# User/Auth Schemas
# ============================================================================


class UserBase(BaseModel):
    """Base schema for user data."""

    username: str = Field(
        min_length=3,
        max_length=50,
        description="Unique username",
    )


class UserCreate(UserBase):
    """Schema for creating a new user (registration)."""

    password: str = Field(
        min_length=8,
        max_length=100,
        description="User password (minimum 8 characters)",
    )
    first_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="User's first name",
    )
    last_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="User's last name",
    )


class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique identifier")
    first_name: Optional[str] = Field(default=None, description="User's first name")
    last_name: Optional[str] = Field(default=None, description="User's last name")
    created_at: datetime = Field(description="Creation timestamp")


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Schema for decoded token data."""

    user_id: Optional[str] = None


# ============================================================================
# Whiteboard Schemas
# ============================================================================


class WhiteboardBase(BaseModel):
    """Base schema for whiteboard data."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Whiteboard name",
    )


class ShareEntry(BaseModel):
    """Schema for sharing a whiteboard with a user."""

    user_id: UUID = Field(description="User ID to share with")
    permission: PermissionLevel = Field(
        default=PermissionLevel.WRITE,
        description="Permission level: read, write, or admin",
    )


class WhiteboardCreate(WhiteboardBase):
    """Schema for creating a new whiteboard."""

    access_type: AccessType = Field(
        default=AccessType.PUBLIC,
        description="Access level: public, private, or shared",
    )
    shared_with: list[ShareEntry] = Field(
        default=[],
        description="List of users to share with and their permissions (for shared access type)",
    )


class WhiteboardUpdate(BaseModel):
    """Schema for updating an existing whiteboard."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Whiteboard name",
    )
    access_type: Optional[AccessType] = Field(
        default=None,
        description="Access level: public, private, or shared",
    )
    shared_with: Optional[list[ShareEntry]] = Field(
        default=None,
        description="List of users to share with and their permissions (for shared access type)",
    )


class SharedUserResponse(BaseModel):
    """Schema for a user with shared access."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="User ID")
    username: str = Field(description="Username")
    permission: PermissionLevel = Field(description="Permission level")


class WhiteboardResponse(WhiteboardBase):
    """Schema for whiteboard response including database fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique identifier")
    owner_id: UUID = Field(description="Owner user ID")
    access_type: AccessType = Field(description="Access level")
    shared_with: list[SharedUserResponse] = Field(
        default=[],
        description="Users with shared access",
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    @property
    def is_private(self) -> bool:
        """Backward compatibility."""
        return self.access_type == AccessType.PRIVATE


class WhiteboardWithOwnerResponse(WhiteboardResponse):
    """Schema for whiteboard response including owner info."""

    owner_username: str = Field(description="Owner username")


class WhiteboardListResponse(BaseModel):
    """Schema for listing multiple whiteboards."""

    whiteboards: list[WhiteboardWithOwnerResponse]
    total: int = Field(description="Total number of whiteboards")


# ============================================================================
# Note Schemas
# ============================================================================


class NoteBase(BaseModel):
    """Base schema for note data."""

    title: str = Field(
        default="",
        max_length=255,
        description="Note title",
    )
    content: Optional[str] = Field(
        default="",
        description="Note content/body text",
    )
    color: str = Field(
        default="#FFEB3B",
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code for the note background",
    )
    x_position: float = Field(
        default=0.0,
        ge=0.0,
        description="X coordinate on the whiteboard",
    )
    y_position: float = Field(
        default=0.0,
        ge=0.0,
        description="Y coordinate on the whiteboard",
    )
    width: float = Field(
        default=200.0,
        ge=100.0,
        le=800.0,
        description="Width of the note in pixels",
    )
    height: float = Field(
        default=180.0,
        ge=100.0,
        le=800.0,
        description="Height of the note in pixels",
    )


class NoteCreate(NoteBase):
    """Schema for creating a new note."""

    whiteboard_id: UUID = Field(description="ID of the whiteboard this note belongs to")


class NoteUpdate(BaseModel):
    """Schema for updating an existing note (all fields optional)."""

    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Note title",
    )
    content: Optional[str] = Field(
        default=None,
        description="Note content/body text",
    )
    color: Optional[str] = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code for the note background",
    )
    x_position: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="X coordinate on the whiteboard",
    )
    y_position: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Y coordinate on the whiteboard",
    )
    width: Optional[float] = Field(
        default=None,
        ge=100.0,
        le=800.0,
        description="Width of the note in pixels",
    )
    height: Optional[float] = Field(
        default=None,
        ge=100.0,
        le=800.0,
        description="Height of the note in pixels",
    )


class NoteResponse(NoteBase):
    """Schema for note response including database fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique identifier")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class NoteListResponse(BaseModel):
    """Schema for listing multiple notes."""

    notes: list[NoteResponse]
    total: int = Field(description="Total number of notes")


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(description="Health status")
    database: str = Field(description="Database connection status")
    version: str = Field(default="1.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str = Field(description="Error message")
