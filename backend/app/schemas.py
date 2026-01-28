"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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


class WhiteboardCreate(WhiteboardBase):
    """Schema for creating a new whiteboard."""

    pass


class WhiteboardUpdate(BaseModel):
    """Schema for updating an existing whiteboard."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Whiteboard name",
    )


class WhiteboardResponse(WhiteboardBase):
    """Schema for whiteboard response including database fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique identifier")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class WhiteboardListResponse(BaseModel):
    """Schema for listing multiple whiteboards."""

    whiteboards: list[WhiteboardResponse]
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
