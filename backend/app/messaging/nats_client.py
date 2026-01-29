"""NATS client for pub/sub messaging."""

import asyncio
import json
import logging
from typing import Any, Callable, Coroutine, Dict, Optional, Set
from uuid import UUID

import nats
from nats.aio.client import Client as NATSClient
from nats.aio.subscription import Subscription

from app.config import get_settings

logger = logging.getLogger(__name__)


class NATSClientManager:
    """Manages NATS connection and pub/sub operations."""

    def __init__(self):
        self._client: Optional[NATSClient] = None
        self._subscriptions: Dict[str, Subscription] = {}
        self._handlers: Dict[str, Set[Callable[[Dict[str, Any]], Coroutine]]] = {}
        self._lock = asyncio.Lock()
        self._connected = False

    async def connect(self) -> None:
        """Connect to NATS server."""
        if self._connected:
            return

        settings = get_settings()
        nats_url = getattr(settings, "nats_url", "nats://nats:4222")

        try:
            self._client = await nats.connect(
                nats_url,
                reconnect_time_wait=2,
                max_reconnect_attempts=-1,  # Unlimited reconnection attempts
                error_cb=self._error_callback,
                disconnected_cb=self._disconnected_callback,
                reconnected_cb=self._reconnected_callback,
            )
            self._connected = True
            logger.info(f"Connected to NATS at {nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise

    async def close(self) -> None:
        """Close NATS connection."""
        if self._client and self._connected:
            await self._client.drain()
            await self._client.close()
            self._connected = False
            logger.info("NATS connection closed")

    async def _error_callback(self, e: Exception) -> None:
        """Handle NATS errors."""
        logger.error(f"NATS error: {e}")

    async def _disconnected_callback(self) -> None:
        """Handle NATS disconnection."""
        logger.warning("Disconnected from NATS")

    async def _reconnected_callback(self) -> None:
        """Handle NATS reconnection."""
        logger.info("Reconnected to NATS")

    async def publish(self, subject: str, data: Dict[str, Any]) -> None:
        """Publish a message to a subject."""
        if not self._connected or not self._client:
            logger.warning(f"Cannot publish to {subject}: not connected to NATS")
            return

        try:
            payload = json.dumps(data, default=str).encode()
            await self._client.publish(subject, payload)
            logger.debug(f"Published to {subject}: {data.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to publish to {subject}: {e}")

    async def subscribe(
        self,
        subject: str,
        handler: Callable[[Dict[str, Any]], Coroutine],
    ) -> None:
        """Subscribe to a subject with a handler."""
        async with self._lock:
            if subject not in self._handlers:
                self._handlers[subject] = set()
            self._handlers[subject].add(handler)

            if subject not in self._subscriptions and self._client:
                async def message_handler(msg):
                    try:
                        data = json.loads(msg.data.decode())
                        handlers = self._handlers.get(subject, set())
                        for h in handlers:
                            try:
                                await h(data)
                            except Exception as e:
                                logger.error(f"Handler error for {subject}: {e}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in message on {subject}: {e}")

                sub = await self._client.subscribe(subject, cb=message_handler)
                self._subscriptions[subject] = sub
                logger.info(f"Subscribed to {subject}")

    async def unsubscribe(
        self,
        subject: str,
        handler: Optional[Callable[[Dict[str, Any]], Coroutine]] = None,
    ) -> None:
        """Unsubscribe a handler from a subject."""
        async with self._lock:
            if subject in self._handlers:
                if handler:
                    self._handlers[subject].discard(handler)
                else:
                    self._handlers[subject].clear()

                if not self._handlers[subject]:
                    del self._handlers[subject]
                    if subject in self._subscriptions:
                        await self._subscriptions[subject].unsubscribe()
                        del self._subscriptions[subject]
                        logger.info(f"Unsubscribed from {subject}")

    # Subject helpers for consistent naming
    @staticmethod
    def whiteboard_subject(whiteboard_id: UUID) -> str:
        """Get NATS subject for whiteboard events."""
        return f"whiteboard.{whiteboard_id}"

    @staticmethod
    def user_subject(user_id: UUID) -> str:
        """Get NATS subject for user-specific events."""
        return f"user.{user_id}"

    @staticmethod
    def notifications_subject(user_id: UUID) -> str:
        """Get NATS subject for user notifications."""
        return f"notifications.{user_id}"

    @staticmethod
    def chat_subject(room_id: UUID) -> str:
        """Get NATS subject for chat room messages."""
        return f"chat.{room_id}"

    @staticmethod
    def presence_subject() -> str:
        """Get NATS subject for presence updates."""
        return "presence.updates"

    # High-level publishing methods
    async def publish_note_event(
        self,
        whiteboard_id: UUID,
        event_type: str,
        note_data: Dict[str, Any],
        by_user: Dict[str, Any],
    ) -> None:
        """Publish a note-related event."""
        await self.publish(
            self.whiteboard_subject(whiteboard_id),
            {
                "type": event_type,
                "payload": {
                    "note": note_data,
                    "by_user": by_user,
                },
            },
        )

    async def publish_whiteboard_event(
        self,
        whiteboard_id: UUID,
        event_type: str,
        whiteboard_data: Dict[str, Any],
        by_user: Dict[str, Any],
    ) -> None:
        """Publish a whiteboard-related event."""
        await self.publish(
            self.whiteboard_subject(whiteboard_id),
            {
                "type": event_type,
                "payload": {
                    "whiteboard": whiteboard_data,
                    "by_user": by_user,
                },
            },
        )

    async def publish_notification(
        self,
        user_id: UUID,
        whiteboard_id: UUID,
        notification_type: str,
        summary: str,
    ) -> None:
        """Publish a notification to a specific user."""
        await self.publish(
            self.notifications_subject(user_id),
            {
                "type": "notification",
                "payload": {
                    "whiteboard_id": str(whiteboard_id),
                    "notification_type": notification_type,
                    "summary": summary,
                },
            },
        )

    async def publish_presence_update(self, online_users: list) -> None:
        """Publish presence update to all users."""
        await self.publish(
            self.presence_subject(),
            {
                "type": "presence_update",
                "payload": {"online_users": online_users},
            },
        )

    async def publish_chat_message(
        self,
        room_id: UUID,
        message_data: Dict[str, Any],
    ) -> None:
        """Publish a chat message to room subscribers."""
        await self.publish(
            self.chat_subject(room_id),
            {
                "type": "new_message",
                "payload": {"message": message_data},
            },
        )


# Global NATS client instance
nats_client = NATSClientManager()
