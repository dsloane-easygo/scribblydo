# Todo Whiteboard Backend

A FastAPI backend for managing post-it notes on a digital whiteboard with real-time collaboration features.

## Features

- REST API for CRUD operations on whiteboards and notes
- User authentication with JWT tokens
- PostgreSQL database with async SQLAlchemy
- Database migrations with Alembic
- WebSocket endpoint for real-time collaboration
- NATS messaging for scalable pub/sub
- Docker support for local development
- Health check endpoint

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services (PostgreSQL, NATS, Backend)
docker compose up -d --build

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove all data
docker compose down -v
```

### Local Development (without Docker)

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate on Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Start the development server:
```bash
uvicorn app.main:app --reload
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Backend API | 8000 | FastAPI application |
| PostgreSQL | 5432 | Primary database |
| NATS | 4222 | Message broker |
| NATS Monitor | 8222 | NATS monitoring UI |

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login (returns JWT token) |
| GET | `/api/auth/me` | Get current user info |

### Whiteboards

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/whiteboards` | List accessible whiteboards |
| POST | `/api/whiteboards` | Create a whiteboard |
| GET | `/api/whiteboards/{id}` | Get a whiteboard |
| PUT | `/api/whiteboards/{id}` | Update a whiteboard |
| DELETE | `/api/whiteboards/{id}` | Delete a whiteboard |

### Notes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notes?whiteboard_id={id}` | List notes |
| POST | `/api/notes` | Create a note |
| GET | `/api/notes/{id}` | Get a note |
| PUT | `/api/notes/{id}` | Update a note |
| DELETE | `/api/notes/{id}` | Delete a note |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| WS `/ws` | Real-time collaboration |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## WebSocket Protocol

### Connection Flow

1. Connect to `ws://localhost:8000/ws`
2. Send authentication: `{"type": "auth", "payload": {"token": "JWT_TOKEN"}}`
3. Receive: `{"type": "auth_success", "payload": {...}}`

### Message Types

**Client → Server:**
- `auth` - Authenticate with JWT token
- `join_whiteboard` - Start viewing a whiteboard
- `leave_whiteboard` - Stop viewing
- `cursor_move` - Update cursor position
- `ping` - Keep-alive

**Server → Client:**
- `auth_success` - Authentication successful
- `whiteboard_joined` - Joined a whiteboard
- `user_joined` / `user_left` - User presence changes
- `cursor_update` - Another user's cursor moved
- `note_created` / `note_updated` / `note_deleted` - Note changes
- `whiteboard_updated` - Whiteboard changes
- `presence_update` - Online users changed
- `pong` - Response to ping
- `error` - Error occurred

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Full database URL | - |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `todo_whiteboard` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | `postgres` |
| `SECRET_KEY` | JWT signing key | (required) |
| `NATS_URL` | NATS server URL | `nats://nats:4222` |
| `DEBUG` | Enable debug mode | `false` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:5173"]` |

## Data Models

### User
```json
{
  "id": "uuid",
  "username": "string",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Whiteboard
```json
{
  "id": "uuid",
  "name": "string",
  "owner_id": "uuid",
  "owner_username": "string",
  "is_private": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Note
```json
{
  "id": "uuid",
  "whiteboard_id": "uuid",
  "title": "string",
  "content": "string",
  "color": "#FFEB3B",
  "x_position": 0.0,
  "y_position": 0.0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + WebSocket endpoint
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT authentication
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # Auth endpoints
│   │   ├── notes.py         # Notes endpoints
│   │   └── whiteboards.py   # Whiteboards endpoints
│   ├── websocket/
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # WebSocket connections
│   │   └── handlers.py      # Message handlers
│   └── messaging/
│       ├── __init__.py
│       └── nats_client.py   # NATS pub/sub client
├── alembic/
│   ├── env.py
│   └── versions/            # Migration files
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Testing

```bash
# Run tests (inside container)
docker compose exec backend pytest -v

# Run with coverage
docker compose exec backend pytest --cov=app --cov-report=html
```
