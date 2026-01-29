"""FastAPI application entry point."""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.config import get_settings
from app.database import async_session_factory, close_db
from app.messaging import nats_client
from app.routers import auth, notes, whiteboards
from app.schemas import ErrorResponse, HealthResponse
from app.websocket import manager
from app.websocket.handlers import handle_websocket_message

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
# Reduce noise from libraries
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("nats").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

settings = get_settings()

# Rate limiter configuration
# Uses client IP address as the key for rate limiting
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler for startup and shutdown events.

    Database tables are managed by Alembic migrations.
    On startup: Connect to NATS.
    On shutdown: Close database and NATS connections.
    """
    # Startup
    try:
        await nats_client.connect()
        logger.info("NATS connection established")
    except Exception as e:
        logger.warning(f"Could not connect to NATS: {e}. Real-time features may be unavailable.")

    yield

    # Shutdown
    await nats_client.close()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="A REST API for managing post-it notes on a digital whiteboard.",
    version="1.0.0",
    lifespan=lifespan,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(whiteboards.router)
app.include_router(notes.router)


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Check the health status of the API and database connection.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the status of the API and database connection.
    """
    db_status = "healthy"

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        version="1.0.0",
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.exception(f"Unhandled exception for {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


# Root redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/docs")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time collaboration.

    Authentication is done via the first message after connection.
    Expected auth message: {"type": "auth", "payload": {"token": "JWT_TOKEN"}}
    """
    await websocket.accept()

    # Wait for auth message
    try:
        auth_data = await websocket.receive_json()
    except Exception:
        await websocket.close(code=4000, reason="Invalid message format")
        return

    if auth_data.get("type") != "auth":
        await websocket.send_json({
            "type": "error",
            "payload": {"code": "auth_required", "message": "First message must be auth"},
        })
        await websocket.close(code=4001, reason="Authentication required")
        return

    token = auth_data.get("payload", {}).get("token")
    if not token:
        await websocket.send_json({
            "type": "error",
            "payload": {"code": "invalid_token", "message": "Token is required"},
        })
        await websocket.close(code=4001, reason="Token required")
        return

    # Validate token and get user
    from app.auth import decode_token
    from uuid import UUID
    from sqlalchemy import select
    from app.models import User

    payload = decode_token(token)
    if not payload:
        await websocket.send_json({
            "type": "error",
            "payload": {"code": "invalid_token", "message": "Invalid or expired token"},
        })
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id_str = payload.get("sub")
    if not user_id_str:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        await websocket.close(code=4001, reason="Invalid user ID")
        return

    # Fetch user from database
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    if not user:
        await websocket.close(code=4001, reason="User not found")
        return

    # Register connection
    connection = await manager.connect(websocket, user.id, user.username)

    # Send auth success
    await websocket.send_json({
        "type": "auth_success",
        "payload": {
            "user_id": str(user.id),
            "username": user.username,
        },
    })

    # Handle messages
    try:
        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(connection, data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.username}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user.username}: {e}")
    finally:
        await manager.disconnect(connection)
