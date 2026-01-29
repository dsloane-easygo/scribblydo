"""SQLAlchemy models for the Todo Whiteboard application."""

import enum
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AccessType(str, enum.Enum):
    """Whiteboard access type."""
    PUBLIC = "public"
    PRIVATE = "private"
    SHARED = "shared"


class PermissionLevel(str, enum.Enum):
    """Permission level for shared whiteboard access."""
    READ = "read"      # Can view whiteboard and notes
    WRITE = "write"    # Can view, create, edit, and delete notes
    ADMIN = "admin"    # Same as owner: can manage sharing, rename, delete whiteboard


class User(Base):
    """
    User model for authentication.

    Attributes:
        id: Unique identifier (UUID)
        username: Unique username
        password_hash: Hashed password
        created_at: Timestamp when the user was created
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship to whiteboards
    whiteboards: Mapped[list["Whiteboard"]] = relationship(
        "Whiteboard", back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"


class Whiteboard(Base):
    """
    Whiteboard model representing a named collection of notes.

    Attributes:
        id: Unique identifier (UUID)
        name: Whiteboard name
        owner_id: Foreign key to the user who owns this whiteboard
        access_type: Access level (public, private, shared)
        created_at: Timestamp when the whiteboard was created
        updated_at: Timestamp when the whiteboard was last updated
    """

    __tablename__ = "whiteboards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_type: Mapped[AccessType] = mapped_column(
        Enum(AccessType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AccessType.PUBLIC,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="whiteboards")
    notes: Mapped[list["Note"]] = relationship(
        "Note", back_populates="whiteboard", cascade="all, delete-orphan"
    )
    shared_with: Mapped[list["WhiteboardShare"]] = relationship(
        "WhiteboardShare", back_populates="whiteboard", cascade="all, delete-orphan"
    )

    @property
    def is_private(self) -> bool:
        """Backward compatibility property."""
        return self.access_type == AccessType.PRIVATE

    def __repr__(self) -> str:
        return f"<Whiteboard(id={self.id}, name='{self.name}')>"


class Note(Base):
    """
    Note model representing a post-it note on the whiteboard.

    Attributes:
        id: Unique identifier (UUID)
        whiteboard_id: Foreign key to the whiteboard this note belongs to
        title: Note title
        content: Note content/body text
        color: Hex color code for the note background
        x_position: X coordinate on the whiteboard
        y_position: Y coordinate on the whiteboard
        created_at: Timestamp when the note was created
        updated_at: Timestamp when the note was last updated
    """

    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    whiteboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("whiteboards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
    )
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default="",
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#FFEB3B",
    )
    x_position: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    y_position: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    width: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=200.0,
    )
    height: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=180.0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to whiteboard
    whiteboard: Mapped["Whiteboard"] = relationship("Whiteboard", back_populates="notes")

    def __repr__(self) -> str:
        return f"<Note(id={self.id}, title='{self.title}')>"


class WhiteboardShare(Base):
    """
    WhiteboardShare model for granting specific users access to a whiteboard.

    Attributes:
        id: Unique identifier (UUID)
        whiteboard_id: Foreign key to the whiteboard
        user_id: Foreign key to the user who has access
        permission: Permission level (read, write, admin)
        created_at: Timestamp when the share was created
    """

    __tablename__ = "whiteboard_shares"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    whiteboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("whiteboards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission: Mapped[PermissionLevel] = mapped_column(
        Enum(PermissionLevel, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PermissionLevel.WRITE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    whiteboard: Mapped["Whiteboard"] = relationship("Whiteboard", back_populates="shared_with")
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<WhiteboardShare(whiteboard_id={self.whiteboard_id}, user_id={self.user_id}, permission={self.permission})>"
