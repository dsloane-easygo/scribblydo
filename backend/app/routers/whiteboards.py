"""Whiteboards API router with CRUD operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Whiteboard
from app.schemas import (
    WhiteboardCreate,
    WhiteboardListResponse,
    WhiteboardResponse,
    WhiteboardUpdate,
)

router = APIRouter(prefix="/api/whiteboards", tags=["whiteboards"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get(
    "",
    response_model=WhiteboardListResponse,
    summary="List all whiteboards",
    description="Retrieve all whiteboards.",
)
async def list_whiteboards(db: DbSession) -> WhiteboardListResponse:
    """
    List all whiteboards.

    Returns all whiteboards sorted by creation date (newest first).
    """
    result = await db.execute(
        select(Whiteboard).order_by(Whiteboard.created_at.desc())
    )
    whiteboards = result.scalars().all()
    return WhiteboardListResponse(
        whiteboards=[WhiteboardResponse.model_validate(wb) for wb in whiteboards],
        total=len(whiteboards),
    )


@router.post(
    "",
    response_model=WhiteboardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new whiteboard",
    description="Create a new whiteboard.",
)
async def create_whiteboard(
    whiteboard_data: WhiteboardCreate, db: DbSession
) -> WhiteboardResponse:
    """
    Create a new whiteboard.

    Args:
        whiteboard_data: Whiteboard creation data including name.
        db: Database session.

    Returns:
        The created whiteboard with generated ID and timestamps.
    """
    whiteboard = Whiteboard(**whiteboard_data.model_dump())
    db.add(whiteboard)
    await db.flush()
    await db.refresh(whiteboard)
    return WhiteboardResponse.model_validate(whiteboard)


@router.get(
    "/{whiteboard_id}",
    response_model=WhiteboardResponse,
    summary="Get a whiteboard by ID",
    description="Retrieve a specific whiteboard by its unique identifier.",
    responses={
        404: {"description": "Whiteboard not found"},
    },
)
async def get_whiteboard(whiteboard_id: UUID, db: DbSession) -> WhiteboardResponse:
    """
    Get a whiteboard by ID.

    Args:
        whiteboard_id: The unique identifier of the whiteboard.
        db: Database session.

    Returns:
        The requested whiteboard.

    Raises:
        HTTPException: If the whiteboard is not found.
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

    return WhiteboardResponse.model_validate(whiteboard)


@router.put(
    "/{whiteboard_id}",
    response_model=WhiteboardResponse,
    summary="Update a whiteboard",
    description="Update an existing whiteboard's name.",
    responses={
        404: {"description": "Whiteboard not found"},
    },
)
async def update_whiteboard(
    whiteboard_id: UUID,
    whiteboard_data: WhiteboardUpdate,
    db: DbSession,
) -> WhiteboardResponse:
    """
    Update a whiteboard.

    Args:
        whiteboard_id: The unique identifier of the whiteboard to update.
        whiteboard_data: Fields to update.
        db: Database session.

    Returns:
        The updated whiteboard.

    Raises:
        HTTPException: If the whiteboard is not found.
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

    # Update only provided fields
    update_data = whiteboard_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(whiteboard, field, value)

    await db.flush()
    await db.refresh(whiteboard)
    return WhiteboardResponse.model_validate(whiteboard)


@router.delete(
    "/{whiteboard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a whiteboard",
    description="Permanently delete a whiteboard and all its notes.",
    responses={
        404: {"description": "Whiteboard not found"},
    },
)
async def delete_whiteboard(whiteboard_id: UUID, db: DbSession) -> None:
    """
    Delete a whiteboard.

    Args:
        whiteboard_id: The unique identifier of the whiteboard to delete.
        db: Database session.

    Raises:
        HTTPException: If the whiteboard is not found.
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

    await db.delete(whiteboard)
