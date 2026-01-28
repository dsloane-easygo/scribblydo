"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import async_session_factory, close_db
from app.routers import notes, whiteboards
from app.schemas import ErrorResponse, HealthResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler for startup and shutdown events.

    Database tables are managed by Alembic migrations.
    On shutdown: Close database connections.
    """
    # Startup - tables created via Alembic migrations
    yield
    # Shutdown
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
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
