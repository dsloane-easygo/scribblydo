"""Whiteboards API router with CRUD operations."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import CurrentUser
from app.database import get_db
from app.models import AccessType, User, Whiteboard, WhiteboardShare
from app.schemas import (
    AccessType as SchemaAccessType,
    SharedUserResponse,
    WhiteboardCreate,
    WhiteboardListResponse,
    WhiteboardUpdate,
    WhiteboardWithOwnerResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whiteboards", tags=["whiteboards"])

# Type alias for database session dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


def whiteboard_to_response(whiteboard: Whiteboard) -> WhiteboardWithOwnerResponse:
    """Convert a Whiteboard model to a response with owner info."""
    shared_users = []
    if whiteboard.shared_with:
        shared_users = [
            SharedUserResponse(id=share.user.id, username=share.user.username)
            for share in whiteboard.shared_with
            if share.user
        ]

    return WhiteboardWithOwnerResponse(
        id=whiteboard.id,
        name=whiteboard.name,
        owner_id=whiteboard.owner_id,
        owner_username=whiteboard.owner.username,
        access_type=SchemaAccessType(whiteboard.access_type.value),
        shared_with=shared_users,
        created_at=whiteboard.created_at,
        updated_at=whiteboard.updated_at,
    )


def can_access_whiteboard(whiteboard: Whiteboard, user_id: UUID) -> bool:
    """Check if a user can access a whiteboard."""
    # Owner always has access
    if whiteboard.owner_id == user_id:
        return True

    # Public whiteboards are accessible to all
    if whiteboard.access_type == AccessType.PUBLIC:
        return True

    # Shared whiteboards are accessible to shared users
    if whiteboard.access_type == AccessType.SHARED:
        for share in whiteboard.shared_with:
            if share.user_id == user_id:
                return True

    # Private whiteboards are only accessible to owner
    return False


@router.get(
    "",
    response_model=WhiteboardListResponse,
    summary="List all whiteboards",
    description="Retrieve all accessible whiteboards for the current user.",
)
async def list_whiteboards(
    current_user: CurrentUser,
    db: DbSession,
) -> WhiteboardListResponse:
    """
    List all whiteboards visible to the current user.

    Returns public whiteboards, user's own whiteboards, and shared whiteboards.
    """
    # Get whiteboards where:
    # - access_type is PUBLIC, or
    # - user is the owner, or
    # - user has shared access
    result = await db.execute(
        select(Whiteboard)
        .options(
            selectinload(Whiteboard.owner),
            selectinload(Whiteboard.shared_with).selectinload(WhiteboardShare.user),
        )
        .outerjoin(WhiteboardShare)
        .where(
            or_(
                Whiteboard.access_type == AccessType.PUBLIC,
                Whiteboard.owner_id == current_user.id,
                WhiteboardShare.user_id == current_user.id,
            )
        )
        .distinct()
        .order_by(Whiteboard.created_at.desc())
    )
    whiteboards = result.scalars().all()
    return WhiteboardListResponse(
        whiteboards=[whiteboard_to_response(wb) for wb in whiteboards],
        total=len(whiteboards),
    )


@router.post(
    "",
    response_model=WhiteboardWithOwnerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new whiteboard",
    description="Create a new whiteboard owned by the current user.",
)
async def create_whiteboard(
    whiteboard_data: WhiteboardCreate,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> WhiteboardWithOwnerResponse:
    """Create a new whiteboard."""
    # Convert schema enum to model enum
    access_type = AccessType(whiteboard_data.access_type.value)

    whiteboard = Whiteboard(
        name=whiteboard_data.name,
        access_type=access_type,
        owner_id=current_user.id,
    )
    db.add(whiteboard)
    await db.flush()

    # Add shared users if access_type is SHARED
    if access_type == AccessType.SHARED and whiteboard_data.shared_with:
        for user_id in whiteboard_data.shared_with:
            # Verify user exists
            user_result = await db.execute(select(User).where(User.id == user_id))
            if user_result.scalar_one_or_none():
                share = WhiteboardShare(whiteboard_id=whiteboard.id, user_id=user_id)
                db.add(share)

    await db.flush()

    # Load relationships
    result = await db.execute(
        select(Whiteboard)
        .options(
            selectinload(Whiteboard.owner),
            selectinload(Whiteboard.shared_with).selectinload(WhiteboardShare.user),
        )
        .where(Whiteboard.id == whiteboard.id)
    )
    whiteboard = result.scalar_one()

    response = whiteboard_to_response(whiteboard)

    # Broadcast to all users (only if public)
    if whiteboard.access_type == AccessType.PUBLIC:
        background_tasks.add_task(
            broadcast_global_whiteboard_event,
            "whiteboard_created",
            {
                "id": str(response.id),
                "name": response.name,
                "access_type": response.access_type.value,
                "owner_id": str(response.owner_id),
                "owner_username": response.owner_username,
            },
            {"id": str(current_user.id), "username": current_user.username},
        )

    return response


@router.get(
    "/{whiteboard_id}",
    response_model=WhiteboardWithOwnerResponse,
    summary="Get a whiteboard by ID",
    description="Retrieve a specific whiteboard by its unique identifier.",
    responses={
        403: {"description": "Access denied"},
        404: {"description": "Whiteboard not found"},
    },
)
async def get_whiteboard(
    whiteboard_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> WhiteboardWithOwnerResponse:
    """Get a whiteboard by ID."""
    result = await db.execute(
        select(Whiteboard)
        .options(
            selectinload(Whiteboard.owner),
            selectinload(Whiteboard.shared_with).selectinload(WhiteboardShare.user),
        )
        .where(Whiteboard.id == whiteboard_id)
    )
    whiteboard = result.scalar_one_or_none()

    if whiteboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Whiteboard with ID {whiteboard_id} not found",
        )

    if not can_access_whiteboard(whiteboard, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this whiteboard",
        )

    return whiteboard_to_response(whiteboard)


@router.put(
    "/{whiteboard_id}",
    response_model=WhiteboardWithOwnerResponse,
    summary="Update a whiteboard",
    description="Update an existing whiteboard. Only the owner can update.",
    responses={
        403: {"description": "Only the owner can update this whiteboard"},
        404: {"description": "Whiteboard not found"},
    },
)
async def update_whiteboard(
    whiteboard_id: UUID,
    whiteboard_data: WhiteboardUpdate,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> WhiteboardWithOwnerResponse:
    """Update a whiteboard."""
    result = await db.execute(
        select(Whiteboard)
        .options(
            selectinload(Whiteboard.owner),
            selectinload(Whiteboard.shared_with).selectinload(WhiteboardShare.user),
        )
        .where(Whiteboard.id == whiteboard_id)
    )
    whiteboard = result.scalar_one_or_none()

    if whiteboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Whiteboard with ID {whiteboard_id} not found",
        )

    # Only owner can update
    if whiteboard.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can update this whiteboard",
        )

    # Update fields
    if whiteboard_data.name is not None:
        whiteboard.name = whiteboard_data.name

    if whiteboard_data.access_type is not None:
        whiteboard.access_type = AccessType(whiteboard_data.access_type.value)

    # Update shared users if provided
    if whiteboard_data.shared_with is not None:
        # Remove existing shares
        for share in whiteboard.shared_with:
            await db.delete(share)

        # Add new shares if access_type is SHARED
        if whiteboard.access_type == AccessType.SHARED:
            for user_id in whiteboard_data.shared_with:
                user_result = await db.execute(select(User).where(User.id == user_id))
                if user_result.scalar_one_or_none():
                    share = WhiteboardShare(whiteboard_id=whiteboard.id, user_id=user_id)
                    db.add(share)

    await db.flush()
    await db.refresh(whiteboard)

    # Reload relationships
    result = await db.execute(
        select(Whiteboard)
        .options(
            selectinload(Whiteboard.owner),
            selectinload(Whiteboard.shared_with).selectinload(WhiteboardShare.user),
        )
        .where(Whiteboard.id == whiteboard_id)
    )
    whiteboard = result.scalar_one()

    response = whiteboard_to_response(whiteboard)

    # Broadcast via NATS
    background_tasks.add_task(
        broadcast_whiteboard_event,
        whiteboard_id,
        "whiteboard_updated",
        {
            "id": str(response.id),
            "name": response.name,
            "access_type": response.access_type.value,
            "owner_id": str(response.owner_id),
            "owner_username": response.owner_username,
        },
        {"id": str(current_user.id), "username": current_user.username},
    )

    return response


async def broadcast_whiteboard_event(
    whiteboard_id: UUID,
    event_type: str,
    whiteboard_data: dict,
    by_user: dict,
) -> None:
    """Broadcast whiteboard event via NATS to whiteboard viewers."""
    try:
        from app.messaging import nats_client
        await nats_client.publish_whiteboard_event(
            whiteboard_id, event_type, whiteboard_data, by_user
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast {event_type}: {e}")


async def broadcast_global_whiteboard_event(
    event_type: str,
    whiteboard_data: dict,
    by_user: dict,
) -> None:
    """Broadcast whiteboard event via NATS to all users."""
    try:
        from app.messaging import nats_client
        await nats_client.publish(
            "whiteboards.global",
            {
                "type": event_type,
                "payload": {
                    "whiteboard": whiteboard_data,
                    "by_user": by_user,
                },
            },
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast global {event_type}: {e}")


@router.delete(
    "/{whiteboard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a whiteboard",
    description="Permanently delete a whiteboard and all its notes. Only the owner can delete.",
    responses={
        403: {"description": "Only the owner can delete this whiteboard"},
        404: {"description": "Whiteboard not found"},
    },
)
async def delete_whiteboard(
    whiteboard_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> None:
    """Delete a whiteboard."""
    result = await db.execute(
        select(Whiteboard).where(Whiteboard.id == whiteboard_id)
    )
    whiteboard = result.scalar_one_or_none()

    if whiteboard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Whiteboard with ID {whiteboard_id} not found",
        )

    # Only owner can delete
    if whiteboard.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete this whiteboard",
        )

    was_public = whiteboard.access_type == AccessType.PUBLIC
    await db.delete(whiteboard)

    # Broadcast deletion to all users (only if was public)
    if was_public:
        background_tasks.add_task(
            broadcast_global_whiteboard_event,
            "whiteboard_deleted",
            {"id": str(whiteboard_id)},
            {"id": str(current_user.id), "username": current_user.username},
        )


@router.get(
    "/users/search",
    summary="Search users for sharing",
    description="Search for users to share a whiteboard with.",
)
async def search_users(
    q: str,
    current_user: CurrentUser,
    db: DbSession,
) -> list[SharedUserResponse]:
    """Search for users by username."""
    if len(q) < 2:
        return []

    result = await db.execute(
        select(User)
        .where(
            User.username.ilike(f"%{q}%"),
            User.id != current_user.id,
        )
        .limit(10)
    )
    users = result.scalars().all()
    return [SharedUserResponse(id=u.id, username=u.username) for u in users]
