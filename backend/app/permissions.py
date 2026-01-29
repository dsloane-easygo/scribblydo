"""Shared permission checking utilities for whiteboard access control."""

from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AccessType, PermissionLevel, Whiteboard


def get_user_permission(whiteboard: Whiteboard, user_id: UUID) -> Optional[PermissionLevel]:
    """
    Get the user's permission level for a whiteboard.

    Args:
        whiteboard: The whiteboard to check (must have shared_with relationship loaded).
        user_id: The user's ID.

    Returns:
        The user's permission level, or None if no access.
    """
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
) -> Optional[Whiteboard]:
    """
    Get a whiteboard with its shares loaded.

    Args:
        whiteboard_id: The whiteboard's UUID.
        db: Database session.

    Returns:
        The whiteboard with shares loaded, or None if not found.
    """
    result = await db.execute(
        select(Whiteboard)
        .options(selectinload(Whiteboard.shared_with))
        .where(Whiteboard.id == whiteboard_id)
    )
    return result.scalar_one_or_none()


async def check_whiteboard_access(
    whiteboard_id: UUID,
    user_id: UUID,
    db: AsyncSession,
    require_write: bool = False,
) -> Tuple[Optional[Whiteboard], Optional[PermissionLevel], Optional[str]]:
    """
    Check if a user has access to a whiteboard.

    Args:
        whiteboard_id: The whiteboard's UUID.
        user_id: The user's UUID.
        db: Database session.
        require_write: If True, require at least WRITE permission.

    Returns:
        Tuple of (whiteboard, permission, error_message).
        If access is granted: (whiteboard, permission, None)
        If access is denied: (None, None, error_message)
    """
    whiteboard = await get_whiteboard_with_shares(whiteboard_id, db)

    if whiteboard is None:
        return None, None, f"Whiteboard with ID {whiteboard_id} not found"

    permission = get_user_permission(whiteboard, user_id)

    if permission is None:
        return None, None, "Access denied to this whiteboard"

    if require_write and permission not in (PermissionLevel.WRITE, PermissionLevel.ADMIN):
        return None, None, "Write permission required for this operation"

    return whiteboard, permission, None


async def has_whiteboard_read_access(
    whiteboard_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> bool:
    """
    Check if a user has read access to a whiteboard.

    This is a lightweight check that returns a boolean.
    Use check_whiteboard_access() when you need the whiteboard object.

    Args:
        whiteboard_id: The whiteboard's UUID.
        user_id: The user's UUID.
        db: Database session.

    Returns:
        True if the user has at least read access, False otherwise.
    """
    whiteboard, permission, _ = await check_whiteboard_access(whiteboard_id, user_id, db)
    return permission is not None
