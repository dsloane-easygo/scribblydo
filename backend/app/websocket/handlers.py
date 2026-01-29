"""WebSocket message handlers."""

from typing import Any, Dict
from uuid import UUID

from app.websocket.connection_manager import UserConnection, manager


async def handle_websocket_message(
    connection: UserConnection, message: Dict[str, Any]
) -> None:
    """Route incoming WebSocket messages to appropriate handlers."""
    msg_type = message.get("type")
    payload = message.get("payload", {})

    handlers = {
        "join_whiteboard": handle_join_whiteboard,
        "leave_whiteboard": handle_leave_whiteboard,
        "cursor_move": handle_cursor_move,
        "note_position": handle_note_position,
        "ping": handle_ping,
    }

    handler = handlers.get(msg_type)
    if handler:
        await handler(connection, payload)
    else:
        await connection.websocket.send_json(
            {
                "type": "error",
                "payload": {"code": "unknown_message_type", "message": f"Unknown message type: {msg_type}"},
            }
        )


async def handle_join_whiteboard(
    connection: UserConnection, payload: Dict[str, Any]
) -> None:
    """Handle user joining a whiteboard."""
    whiteboard_id_str = payload.get("whiteboard_id")
    if not whiteboard_id_str:
        await connection.websocket.send_json(
            {
                "type": "error",
                "payload": {"code": "missing_whiteboard_id", "message": "whiteboard_id is required"},
            }
        )
        return

    try:
        whiteboard_id = UUID(whiteboard_id_str)
    except ValueError:
        await connection.websocket.send_json(
            {
                "type": "error",
                "payload": {"code": "invalid_whiteboard_id", "message": "Invalid whiteboard_id format"},
            }
        )
        return

    await manager.join_whiteboard(connection, whiteboard_id)

    # Send current viewers and their cursors to the joining user
    viewers = await manager.get_whiteboard_viewers(whiteboard_id)
    await connection.websocket.send_json(
        {
            "type": "whiteboard_joined",
            "payload": {
                "whiteboard_id": str(whiteboard_id),
                "viewers": viewers,
            },
        }
    )


async def handle_leave_whiteboard(
    connection: UserConnection, payload: Dict[str, Any]
) -> None:
    """Handle user leaving a whiteboard."""
    await manager.leave_whiteboard(connection)
    await connection.websocket.send_json(
        {
            "type": "whiteboard_left",
            "payload": {},
        }
    )


async def handle_cursor_move(
    connection: UserConnection, payload: Dict[str, Any]
) -> None:
    """Handle cursor position update."""
    x = payload.get("x", 0.0)
    y = payload.get("y", 0.0)

    try:
        x = float(x)
        y = float(y)
    except (TypeError, ValueError):
        return  # Silently ignore invalid cursor data

    await manager.update_cursor(connection, x, y)


async def handle_note_position(
    connection: UserConnection, payload: Dict[str, Any]
) -> None:
    """Handle real-time note position streaming during drag."""
    note_id = payload.get("note_id")
    x_position = payload.get("x_position")
    y_position = payload.get("y_position")

    if not note_id or x_position is None or y_position is None:
        return  # Silently ignore invalid position data

    try:
        x_position = float(x_position)
        y_position = float(y_position)
    except (TypeError, ValueError):
        return  # Silently ignore invalid position data

    # Broadcast to other viewers of the same whiteboard
    if connection.current_whiteboard_id:
        await manager.broadcast_to_whiteboard(
            connection.current_whiteboard_id,
            {
                "type": "note_position",
                "payload": {
                    "note_id": note_id,
                    "x_position": x_position,
                    "y_position": y_position,
                    "by_user": {
                        "id": str(connection.user_id),
                        "username": connection.username,
                    },
                },
            },
            exclude=connection,
        )


async def handle_ping(connection: UserConnection, payload: Dict[str, Any]) -> None:
    """Handle ping message for keep-alive."""
    await connection.websocket.send_json({"type": "pong", "payload": {}})
