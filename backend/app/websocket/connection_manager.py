"""WebSocket connection manager for tracking and broadcasting."""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class UserConnection:
    """Represents a single WebSocket connection for a user."""

    websocket: WebSocket
    user_id: UUID
    username: str
    current_whiteboard_id: Optional[UUID] = None
    cursor_x: float = 0.0
    cursor_y: float = 0.0

    def __hash__(self):
        # Hash based on websocket id which is unique per connection
        return id(self.websocket)

    def __eq__(self, other):
        if not isinstance(other, UserConnection):
            return False
        return id(self.websocket) == id(other.websocket)


class ConnectionManager:
    """Manages WebSocket connections, presence, and message broadcasting."""

    def __init__(self):
        # All active connections: user_id -> Set[UserConnection]
        self._connections: Dict[UUID, Set[UserConnection]] = {}
        # Whiteboard viewers: whiteboard_id -> Set[UserConnection]
        self._whiteboard_viewers: Dict[UUID, Set[UserConnection]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(
        self, websocket: WebSocket, user_id: UUID, username: str
    ) -> UserConnection:
        """Register a new WebSocket connection."""
        connection = UserConnection(
            websocket=websocket,
            user_id=user_id,
            username=username,
        )

        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(connection)

        # Subscribe to user-specific NATS subject for notifications
        await self._setup_user_subscriptions(connection)

        # Broadcast presence update to all users
        await self.broadcast_presence_update()

        return connection

    async def _setup_user_subscriptions(self, connection: UserConnection) -> None:
        """Set up NATS subscriptions for a user connection."""
        try:
            from app.messaging import nats_client

            # Subscribe to user notifications
            async def notification_handler(data: Dict[str, Any]) -> None:
                await self._send_to_connection(connection, data)

            await nats_client.subscribe(
                nats_client.notifications_subject(connection.user_id),
                notification_handler,
            )

            # Subscribe to presence updates
            async def presence_handler(data: Dict[str, Any]) -> None:
                await self._send_to_connection(connection, data)

            await nats_client.subscribe(
                nats_client.presence_subject(),
                presence_handler,
            )

            # Subscribe to global whiteboard events (create/delete)
            async def whiteboard_global_handler(data: Dict[str, Any]) -> None:
                await self._send_to_connection(connection, data)

            await nats_client.subscribe(
                "whiteboards.global",
                whiteboard_global_handler,
            )
        except Exception as e:
            logger.warning(f"Could not set up NATS subscriptions: {e}")

    async def disconnect(self, connection: UserConnection) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            # Remove from user connections
            if connection.user_id in self._connections:
                self._connections[connection.user_id].discard(connection)
                if not self._connections[connection.user_id]:
                    del self._connections[connection.user_id]

            # Remove from whiteboard viewers
            if connection.current_whiteboard_id:
                await self._leave_whiteboard_internal(connection)

        # Broadcast presence update
        await self.broadcast_presence_update()

    async def join_whiteboard(
        self, connection: UserConnection, whiteboard_id: UUID
    ) -> None:
        """User starts viewing a whiteboard."""
        async with self._lock:
            # Leave current whiteboard if any
            if connection.current_whiteboard_id:
                await self._leave_whiteboard_internal(connection)

            # Join new whiteboard
            connection.current_whiteboard_id = whiteboard_id
            if whiteboard_id not in self._whiteboard_viewers:
                self._whiteboard_viewers[whiteboard_id] = set()
            self._whiteboard_viewers[whiteboard_id].add(connection)

        # Subscribe to whiteboard events via NATS
        await self._subscribe_to_whiteboard(connection, whiteboard_id)

        # Notify other viewers
        await self.broadcast_to_whiteboard(
            whiteboard_id,
            {
                "type": "user_joined",
                "payload": {
                    "user": {
                        "id": str(connection.user_id),
                        "username": connection.username,
                    },
                    "viewers": await self.get_whiteboard_viewers(whiteboard_id),
                },
            },
            exclude=connection,
        )

    async def _subscribe_to_whiteboard(
        self, connection: UserConnection, whiteboard_id: UUID
    ) -> None:
        """Subscribe a connection to whiteboard events via NATS."""
        try:
            from app.messaging import nats_client

            async def whiteboard_handler(data: Dict[str, Any]) -> None:
                # Only forward if user is still viewing this whiteboard
                if connection.current_whiteboard_id == whiteboard_id:
                    await self._send_to_connection(connection, data)

            await nats_client.subscribe(
                nats_client.whiteboard_subject(whiteboard_id),
                whiteboard_handler,
            )
        except Exception as e:
            logger.warning(f"Could not subscribe to whiteboard {whiteboard_id}: {e}")

    async def leave_whiteboard(self, connection: UserConnection) -> None:
        """User stops viewing a whiteboard."""
        whiteboard_id = connection.current_whiteboard_id
        if not whiteboard_id:
            return

        async with self._lock:
            await self._leave_whiteboard_internal(connection)

        # Notify other viewers
        await self.broadcast_to_whiteboard(
            whiteboard_id,
            {
                "type": "user_left",
                "payload": {
                    "user_id": str(connection.user_id),
                    "viewers": await self.get_whiteboard_viewers(whiteboard_id),
                },
            },
        )

    async def _leave_whiteboard_internal(self, connection: UserConnection) -> None:
        """Internal method to remove connection from whiteboard (no lock)."""
        whiteboard_id = connection.current_whiteboard_id
        if whiteboard_id and whiteboard_id in self._whiteboard_viewers:
            self._whiteboard_viewers[whiteboard_id].discard(connection)
            if not self._whiteboard_viewers[whiteboard_id]:
                del self._whiteboard_viewers[whiteboard_id]
        connection.current_whiteboard_id = None
        connection.cursor_x = 0.0
        connection.cursor_y = 0.0

    async def update_cursor(
        self, connection: UserConnection, x: float, y: float
    ) -> None:
        """Update cursor position and broadcast to whiteboard viewers."""
        connection.cursor_x = x
        connection.cursor_y = y

        if connection.current_whiteboard_id:
            await self.broadcast_to_whiteboard(
                connection.current_whiteboard_id,
                {
                    "type": "cursor_update",
                    "payload": {
                        "user_id": str(connection.user_id),
                        "username": connection.username,
                        "x": x,
                        "y": y,
                    },
                },
                exclude=connection,
            )

    async def broadcast_to_whiteboard(
        self,
        whiteboard_id: UUID,
        message: dict,
        exclude: Optional[UserConnection] = None,
    ) -> None:
        """Send message to all viewers of a whiteboard."""
        viewers = self._whiteboard_viewers.get(whiteboard_id, set())
        tasks = []
        for conn in viewers:
            if conn != exclude:
                tasks.append(self._send_to_connection(conn, message))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_to_user(self, user_id: UUID, message: dict) -> None:
        """Send message to all connections of a specific user."""
        connections = self._connections.get(user_id, set())
        tasks = [self._send_to_connection(conn, message) for conn in connections]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_to_all(
        self, message: dict, exclude: Optional[UserConnection] = None
    ) -> None:
        """Send message to all connected users."""
        tasks = []
        for connections in self._connections.values():
            for conn in connections:
                if conn != exclude:
                    tasks.append(self._send_to_connection(conn, message))
        logger.info(f"broadcast_to_all: sending {message.get('type')} to {len(tasks)} connections")
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_presence_update(self) -> None:
        """Broadcast updated online users list to everyone via NATS."""
        online_users = await self.get_online_users()
        logger.info(f"Broadcasting presence update: {len(online_users)} users online")
        try:
            from app.messaging import nats_client
            await nats_client.publish_presence_update(online_users)
        except Exception as e:
            logger.warning(f"Could not publish presence update via NATS: {e}")
        # Also do direct broadcast as fallback/supplement
        await self.broadcast_to_all(
            {
                "type": "presence_update",
                "payload": {"online_users": online_users},
            }
        )

    async def _send_to_connection(
        self, connection: UserConnection, message: dict
    ) -> None:
        """Send a message to a single connection."""
        try:
            await connection.websocket.send_json(message)
            logger.debug(f"Sent {message.get('type')} to {connection.username}")
        except Exception as e:
            logger.warning(f"Failed to send to {connection.username}: {e}")

    async def get_online_users(self) -> List[dict]:
        """Get list of all online users."""
        users = []
        seen_ids = set()
        for user_id, connections in self._connections.items():
            if user_id not in seen_ids and connections:
                conn = next(iter(connections))
                users.append(
                    {
                        "id": str(user_id),
                        "username": conn.username,
                    }
                )
                seen_ids.add(user_id)
        return users

    async def get_whiteboard_viewers(self, whiteboard_id: UUID) -> List[dict]:
        """Get list of users viewing a specific whiteboard."""
        viewers = []
        seen_ids = set()
        for conn in self._whiteboard_viewers.get(whiteboard_id, set()):
            if conn.user_id not in seen_ids:
                viewers.append(
                    {
                        "id": str(conn.user_id),
                        "username": conn.username,
                        "cursor_x": conn.cursor_x,
                        "cursor_y": conn.cursor_y,
                    }
                )
                seen_ids.add(conn.user_id)
        return viewers

    def get_users_not_viewing_whiteboard(self, whiteboard_id: UUID) -> Set[UUID]:
        """Get user IDs who are online but not viewing a specific whiteboard."""
        viewing_users = {
            conn.user_id
            for conn in self._whiteboard_viewers.get(whiteboard_id, set())
        }
        all_users = set(self._connections.keys())
        return all_users - viewing_users

    def is_user_viewing_whiteboard(self, user_id: UUID, whiteboard_id: UUID) -> bool:
        """Check if a user is currently viewing a whiteboard."""
        for conn in self._connections.get(user_id, set()):
            if conn.current_whiteboard_id == whiteboard_id:
                return True
        return False


# Global connection manager instance
manager = ConnectionManager()
