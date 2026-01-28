"""Notes API router with CRUD operations."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Note, Whiteboard
from app.schemas import (
    NoteCreate,
    NoteListResponse,
    NoteResponse,
    NoteUpdate,
)

router = APIRouter(prefix="/api/notes", tags=["notes"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "",
    response_model=NoteListResponse,
    summary="List notes",
    description="Retrieve notes, optionally filtered by whiteboard.",
)
async def list_notes(
    db: DbSession,
    whiteboard_id: Optional[UUID] = Query(None, description="Filter by whiteboard ID"),
) -> NoteListResponse:
    """
    List notes.

    Returns notes sorted by creation date (newest first).
    Optionally filter by whiteboard_id.
    """
    query = select(Note).order_by(Note.created_at.desc())

    if whiteboard_id:
        query = query.where(Note.whiteboard_id == whiteboard_id)

    result = await db.execute(query)
    notes = result.scalars().all()
    return NoteListResponse(
        notes=[NoteResponse.model_validate(note) for note in notes],
        total=len(notes),
    )


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note",
    description="Create a new post-it note on a whiteboard.",
)
async def create_note(note_data: NoteCreate, db: DbSession) -> NoteResponse:
    """
    Create a new note.

    Args:
        note_data: Note creation data including whiteboard_id, title, content, color, and position.
        db: Database session.

    Returns:
        The created note with generated ID and timestamps.
    """
    # Verify whiteboard exists
    result = await db.execute(
        select(Whiteboard).where(Whiteboard.id == note_data.whiteboard_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Whiteboard with ID {note_data.whiteboard_id} not found",
        )

    note = Note(**note_data.model_dump())
    db.add(note)
    await db.flush()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get a note by ID",
    description="Retrieve a specific note by its unique identifier.",
    responses={
        404: {"description": "Note not found"},
    },
)
async def get_note(note_id: UUID, db: DbSession) -> NoteResponse:
    """
    Get a note by ID.

    Args:
        note_id: The unique identifier of the note.
        db: Database session.

    Returns:
        The requested note.

    Raises:
        HTTPException: If the note is not found.
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found",
        )

    return NoteResponse.model_validate(note)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
    description="Update an existing note's properties including position.",
    responses={
        404: {"description": "Note not found"},
    },
)
async def update_note(
    note_id: UUID,
    note_data: NoteUpdate,
    db: DbSession,
) -> NoteResponse:
    """
    Update a note.

    Args:
        note_id: The unique identifier of the note to update.
        note_data: Fields to update (only provided fields are updated).
        db: Database session.

    Returns:
        The updated note.

    Raises:
        HTTPException: If the note is not found.
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found",
        )

    # Update only provided fields
    update_data = note_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    await db.flush()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
    description="Permanently delete a note from the whiteboard.",
    responses={
        404: {"description": "Note not found"},
    },
)
async def delete_note(note_id: UUID, db: DbSession) -> None:
    """
    Delete a note.

    Args:
        note_id: The unique identifier of the note to delete.
        db: Database session.

    Raises:
        HTTPException: If the note is not found.
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found",
        )

    await db.delete(note)
