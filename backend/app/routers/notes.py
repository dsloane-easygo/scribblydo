"""Notes API router with CRUD operations."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import CurrentUser
from app.database import get_db
from app.models import AccessType, Note, PermissionLevel, User, Whiteboard
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


def get_user_permission(whiteboard: Whiteboard, user_id: UUID) -> PermissionLevel | None:
    """Get the user's permission level for a whiteboard."""
    # Owner has implicit admin permission
    if whiteboard.owner_id == user_id:
        return PermissionLevel.ADMIN

    # Public whiteboards grant write access to everyone
    if whiteboard.access_type == AccessType.PUBLIC:
        return PermissionLevel.WRITE

    # Check shared access
    if whiteboard.access_type == AccessType.SHARED:
        for share in whiteboard.shared_with:
            if share.user_id == user_id:
                return share.permission

    # No access
    return None


async def get_whiteboard_with_shares(
    whiteboard_id: UUID,
    db: AsyncSession,
) -> Whiteboard | None:
    """Get a whiteboard with its shares loaded."""
    result = await db.execute(
        select(Whiteboard)
        .options(selectinload(Whiteboard.shared_with))
        .where(Whiteboard.id == whiteboard_id)
    )
    return result.scalar_one_or_none()


async def check_whiteboard_read_access(
    whiteboard_id: UUID,
    user: User,
    db: AsyncSession,
) -> Whiteboard:
    """
    Check if user has read access to the whiteboard.

    Returns the whiteboard if accessible, raises HTTPException otherwise.
    """
    whiteboard = await get_whiteboard_with_shares(whiteboard_id, db)

    if whiteboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Whiteboard with ID {whiteboard_id} not found",
        )

    permission = get_user_permission(whiteboard, user.id)
    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this whiteboard",
        )

    return whiteboard


async def check_whiteboard_write_access(
    whiteboard_id: UUID,
    user: User,
    db: AsyncSession,
) -> Whiteboard:
    """
    Check if user has write access to the whiteboard.

    Returns the whiteboard if accessible, raises HTTPException otherwise.
    """
    whiteboard = await get_whiteboard_with_shares(whiteboard_id, db)

    if whiteboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Whiteboard with ID {whiteboard_id} not found",
        )

    permission = get_user_permission(whiteboard, user.id)
    if permission not in (PermissionLevel.WRITE, PermissionLevel.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write permission required for this operation",
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
    User must have read access to the whiteboard.
    """
    # Check whiteboard read access
    await check_whiteboard_read_access(whiteboard_id, current_user, db)

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
    description="Create a new post-it note on a whiteboard. Requires write permission.",
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
    # Check whiteboard write access
    await check_whiteboard_write_access(note_data.whiteboard_id, current_user, db)

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
        403: {"description": "Access denied to whiteboard"},
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
        select(Note).where(Note.id == note_id)
    )
    note = result.scalar_one_or_none()

    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with ID {note_id} not found",
        )

    # Check whiteboard read access
    await check_whiteboard_read_access(note.whiteboard_id, current_user, db)

    return NoteResponse.model_validate(note)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
    description="Update an existing note's properties including position. Requires write permission.",
    responses={
        403: {"description": "Write permission required"},
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

    Any user with write permission to the whiteboard can update notes (collaborative editing).

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

    # Check whiteboard write access
    whiteboard_id = note.whiteboard_id
    await check_whiteboard_write_access(whiteboard_id, current_user, db)

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
    description="Permanently delete a note from the whiteboard. Requires write permission.",
    responses={
        403: {"description": "Write permission required"},
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

    Any user with write permission to the whiteboard can delete notes (collaborative editing).

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

    # Check whiteboard write access
    whiteboard_id = note.whiteboard_id
    await check_whiteboard_write_access(whiteboard_id, current_user, db)

    await db.delete(note)

    # Broadcast via NATS
    background_tasks.add_task(
        broadcast_note_event,
        whiteboard_id,
        "note_deleted",
        {"id": str(note_id)},
        {"id": str(current_user.id), "username": current_user.username},
    )
