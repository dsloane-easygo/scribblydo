# Todo Whiteboard Backend

A FastAPI backend for managing post-it notes on a digital whiteboard.

## Features

- REST API for CRUD operations on notes
- PostgreSQL database with async SQLAlchemy
- Database migrations with Alembic
- Docker support for local development
- Health check endpoint

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start PostgreSQL and run migrations
docker compose up -d postgres
docker compose --profile migrate run --rm migrate

# Start the backend
docker compose up -d backend

# View logs
docker compose logs -f backend
```

### Local Development

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

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/notes` | List all notes |
| POST | `/api/notes` | Create a note |
| GET | `/api/notes/{id}` | Get a note by ID |
| PUT | `/api/notes/{id}` | Update a note |
| DELETE | `/api/notes/{id}` | Delete a note |

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Full database connection URL | - |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `todo_whiteboard` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | `postgres` |
| `DEBUG` | Enable debug mode | `false` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:3000"]` |

## Note Model

```json
{
  "id": "uuid",
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
