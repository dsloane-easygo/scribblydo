"""Notes API router with CRUD operations."""

import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import CurrentUser
from app.database import get_db
from app.models import Note, User, Whiteboard
from app.schemas import (
    NoteCreate,
    NoteListResponse,
    NoteResponse,
    NoteUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notes", tags=["notes"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def check_whiteboard_access(
    whiteboard_id: UUID,
    user: User,
    db: AsyncSession,
) -> Whiteboard:
    """
    Check if user has access to the whiteboard.

    Returns the whiteboard if accessible, raises HTTPException otherwise.
    """
    result = await db.execute(
        select(Whiteboard).where(Whiteboard.id == whiteboard_id)
    )
    whiteboard = result.scalar_one_or_none()

    if whiteboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Whiteboard with ID {whiteboard_id} not found",
        )

    # Check access: allow if public or user is owner
    if whiteboard.is_private and whiteboard.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to private whiteboard",
        )

    return whiteboard


@router.get(
    "",
    response_model=NoteListResponse,
    summary="List notes",
    description="Retrieve notes filtered by whiteboard ID.",
)
async def list_notes(
    current_user: CurrentUser,
    db: DbSession,
    whiteboard_id: UUID = Query(..., description="Filter by whiteboard ID"),
) -> NoteListResponse:
    """
    List notes from a specific whiteboard.

    Returns notes sorted by creation date (newest first).
    User must have access to the whiteboard.
    """
    # Check whiteboard access
    await check_whiteboard_access(whiteboard_id, current_user, db)

    query = select(Note).where(Note.whiteboard_id == whiteboard_id).order_by(Note.created_at.desc())

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
async def create_note(
    note_data: NoteCreate,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> NoteResponse:
    """
    Create a new note.

    Args:
        note_data: Note creation data including whiteboard_id, title, content, color, and position.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The created note with generated ID and timestamps.
    """
    # Check whiteboard access
    await check_whiteboard_access(note_data.whiteboard_id, current_user, db)

    note = Note(**note_data.model_dump())
    db.add(note)
    await db.flush()
    await db.refresh(note)

    note_response = NoteResponse.model_validate(note)

    # Broadcast via NATS
    background_tasks.add_task(
        broadcast_note_event,
        note_data.whiteboard_id,
        "note_created",
        note_response.model_dump(),
        {"id": str(current_user.id), "username": current_user.username},
    )

    return note_response


async def broadcast_note_event(
    whiteboard_id: UUID,
    event_type: str,
    note_data: dict,
    by_user: dict,
) -> None:
    """Broadcast note event via NATS."""
    try:
        from app.messaging import nats_client
        await nats_client.publish_note_event(whiteboard_id, event_type, note_data, by_user)
    except Exception as e:
        logger.warning(f"Failed to broadcast {event_type}: {e}")


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get a note by ID",
    description="Retrieve a specific note by its unique identifier.",
    responses={
        403: {"description": "Access denied to private whiteboard"},
        404: {"description": "Note not found"},
    },
)
async def get_note(
    note_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> NoteResponse:
    """
    Get a note by ID.

    Args:
        note_id: The unique identifier of the note.
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The requested note.

    Raises:
        HTTPException: If the note is not found or access is denied.
    """
    result = await db.execute(
        select(Note).options(selectinload(Note.whiteboard)).where(Note.id == note_id)
    )
    note = result.scalar_one_or_none()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found",
        )

    # Check whiteboard access
    await check_whiteboard_access(note.whiteboard_id, current_user, db)

    return NoteResponse.model_validate(note)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
    description="Update an existing note's properties including position. Any user with whiteboard access can update notes.",
    responses={
        403: {"description": "Access denied to private whiteboard"},
        404: {"description": "Note not found"},
    },
)
async def update_note(
    note_id: UUID,
    note_data: NoteUpdate,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> NoteResponse:
    """
    Update a note.

    Any user with access to the whiteboard can update notes (collaborative editing).

    Args:
        note_id: The unique identifier of the note to update.
        note_data: Fields to update (only provided fields are updated).
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The updated note.

    Raises:
        HTTPException: If the note is not found or access is denied.
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found",
        )

    # Check whiteboard access (collaborative - anyone with access can modify)
    whiteboard_id = note.whiteboard_id
    await check_whiteboard_access(whiteboard_id, current_user, db)

    # Update only provided fields
    update_data = note_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)

    await db.flush()
    await db.refresh(note)

    note_response = NoteResponse.model_validate(note)

    # Broadcast via NATS
    background_tasks.add_task(
        broadcast_note_event,
        whiteboard_id,
        "note_updated",
        note_response.model_dump(),
        {"id": str(current_user.id), "username": current_user.username},
    )

    return note_response


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
    description="Permanently delete a note from the whiteboard. Any user with whiteboard access can delete notes.",
    responses={
        403: {"description": "Access denied to private whiteboard"},
        404: {"description": "Note not found"},
    },
)
async def delete_note(
    note_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> None:
    """
    Delete a note.

    Any user with access to the whiteboard can delete notes (collaborative editing).

    Args:
        note_id: The unique identifier of the note to delete.
        current_user: The authenticated user.
        db: Database session.

    Raises:
        HTTPException: If the note is not found or access is denied.
    """
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found",
        )

    # Check whiteboard access (collaborative - anyone with access can delete)
    whiteboard_id = note.whiteboard_id
    await check_whiteboard_access(whiteboard_id, current_user, db)

    await db.delete(note)

    # Broadcast via NATS
    background_tasks.add_task(
        broadcast_note_event,
        whiteboard_id,
        "note_deleted",
        {"id": str(note_id)},
        {"id": str(current_user.id), "username": current_user.username},
    )
