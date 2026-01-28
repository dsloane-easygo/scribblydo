"""SQLAlchemy models for the Todo Whiteboard application."""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Whiteboard(Base):
    """
    Whiteboard model representing a named collection of notes.

    Attributes:
        id: Unique identifier (UUID)
        name: Whiteboard name
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

    # Relationship to notes
    notes: Mapped[list["Note"]] = relationship(
        "Note", back_populates="whiteboard", cascade="all, delete-orphan"
    )

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
        default="#FFEB3B",  # Default yellow post-it color
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
