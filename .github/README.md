# Todo Whiteboard

A modern, whiteboard-style todo application featuring draggable post-it notes. Built with React and FastAPI, designed for cloud-native deployment on Kubernetes.

## Features

- **Draggable Post-it Notes**: Intuitive drag-and-drop interface for organizing tasks
- **Real-time Editing**: Edit note titles and content with auto-save functionality
- **Color Customization**: Choose from 6 vibrant post-it colors (yellow, pink, blue, green, orange, purple)
- **Persistent Positioning**: Note positions are saved and restored across sessions
- **Optimistic Updates**: Instant UI feedback with automatic rollback on errors
- **RESTful API**: Full CRUD operations with OpenAPI documentation
- **Health Monitoring**: Built-in health check endpoints for Kubernetes probes

## Architecture

```
                                    +------------------+
                                    |                  |
                                    |   PostgreSQL     |
                                    |   Database       |
                                    |                  |
                                    +--------+---------+
                                             |
                                             | Port 5432
                                             |
+------------------+              +----------+---------+
|                  |   REST API   |                    |
|   React          +------------->|   FastAPI          |
|   Frontend       |   /api/*     |   Backend          |
|   (Vite)         |              |   (Uvicorn)        |
|                  |<-------------+                    |
+------------------+   JSON       +--------------------+
     Port 5173                         Port 8000

+----------------------------------------------------------------+
|                        Kubernetes Cluster                       |
|  +------------------+  +------------------+  +----------------+ |
|  |   Frontend       |  |   Backend        |  |   PostgreSQL   | |
|  |   Deployment     |  |   Deployment     |  |   StatefulSet  | |
|  |   + Service      |  |   + Service      |  |   + Service    | |
|  +------------------+  +------------------+  +----------------+ |
|            |                   |                    |           |
|            +-------------------+--------------------+           |
|                                |                                |
|                    +-----------+-----------+                    |
|                    |       Ingress         |                    |
|                    +-----------------------+                    |
+----------------------------------------------------------------+
```

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.x | UI framework |
| Vite | 5.0.x | Build tool and dev server |
| react-draggable | 4.4.x | Drag-and-drop functionality |
| CSS Modules | - | Scoped component styling |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.109.x | Web framework |
| Uvicorn | 0.27.x | ASGI server |
| SQLAlchemy | 2.0.x | ORM and database toolkit |
| asyncpg | 0.29.x | Async PostgreSQL driver |
| Pydantic | 2.5.x | Data validation |
| Alembic | 1.13.x | Database migrations |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| PostgreSQL 16 | Primary database |
| Docker | Containerization |
| Docker Compose | Local development |
| Kubernetes | Production orchestration |

## Local Development Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.9+ (for backend development)

### Quick Start with Docker Compose

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd _vcluster_todo
   ```

2. **Start the backend and database**
   ```bash
   cd backend
   docker compose up -d
   ```

   This automatically:
   - Starts PostgreSQL
   - Runs database migrations (Alembic)
   - Starts the backend API

3. **Start the frontend development server**
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Complete Local Testing Walkthrough

This section provides a step-by-step guide for testing the todo app locally.

#### Step 1: Start All Services

```bash
cd backend

# Start all services (postgres, migrations, backend)
docker compose up -d

# Watch the startup (migrations run before backend)
docker compose logs -f

# Expected sequence:
# postgres-1  | ... database system is ready to accept connections
# migrate-1   | INFO  [alembic.runtime.migration] Running upgrade ...
# migrate-1 exited with code 0
# backend-1   | INFO:     Uvicorn running on http://0.0.0.0:8000

# Verify services are running
docker compose ps
# Expected output:
# NAME                 SERVICE    STATUS
# backend-backend-1    backend    running
# backend-postgres-1   postgres   running (healthy)
# backend-migrate-1    migrate    exited (0)  <- Exit code 0 means success
```

#### Step 2: Verify the Backend API

```bash
# Check health endpoint
curl http://localhost:8000/api/health
# Expected: {"status":"healthy","database":"connected"}

# List notes (should be empty initially)
curl http://localhost:8000/api/notes
# Expected: []

# Create a test note
curl -X POST http://localhost:8000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Note","content":"Hello World","color":"#FFEB3B","x_position":100,"y_position":100}'
# Expected: {"id":"...","title":"Test Note",...}

# Verify the note was created
curl http://localhost:8000/api/notes
# Expected: [{"id":"...","title":"Test Note",...}]
```

#### Step 3: Start the Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Expected output:
#   VITE v5.x.x  ready in xxx ms
#   ➜  Local:   http://localhost:5173/
```

#### Step 4: Test the Application

1. Open http://localhost:5173 in your browser
2. You should see a whiteboard with any existing notes
3. Click the "+" button in the bottom-right to add a new note
4. Drag notes around the whiteboard - positions are saved automatically
5. Click on a note to edit its title or content
6. Right-click (or use delete button) to remove a note

#### Step 5: Cleanup

```bash
cd backend

# Stop all services
docker compose down

# To also remove the database volume (all data)
docker compose down -v
```

### Troubleshooting

#### Migration Error: "relation already exists"

If you see this error in the migrate container logs:

```
psycopg2.errors.DuplicateTable: relation "notes" already exists
```

This means the database tables exist but Alembic's migration tracking is out of sync. Reset the database:

```bash
cd backend

# Stop services and remove volumes (deletes all data)
docker compose down -v

# Start fresh - migrations will run automatically
docker compose up -d

# Verify migrations succeeded
docker compose logs migrate
# Should show: migrate-1 exited with code 0
```

If you need to keep existing data, stamp the migration as already applied:

```bash
cd backend

# Mark the migration as applied without running it
docker compose run --rm migrate alembic stamp head

# Restart services
docker compose up -d
```

#### Backend Cannot Connect to Database

If the backend fails with database connection errors:

```bash
# Check if PostgreSQL is healthy
docker compose ps
# The postgres service should show "healthy"

# View PostgreSQL logs
docker compose logs postgres

# Ensure the backend is waiting for postgres
docker compose down
docker compose up -d
```

#### Frontend Cannot Reach Backend API

If the frontend shows network errors:

1. Verify the backend is running: `docker compose ps`
2. Check backend logs: `docker compose logs backend`
3. Test the API directly: `curl http://localhost:8000/api/health`
4. Ensure the frontend proxy is configured correctly in `vite.config.js`

#### Port Already in Use

If you get "port already in use" errors:

```bash
# Find what's using the port
lsof -i :8000  # For backend
lsof -i :5432  # For PostgreSQL
lsof -i :5173  # For frontend

# Stop the conflicting process or use different ports
docker compose down
# Edit docker-compose.yml to use different ports
```

#### Docker Compose Warnings

If you see warnings about deprecated attributes, ensure you're using Docker Compose V2:

```bash
# Check Docker Compose version
docker compose version
# Should be v2.x.x

# Use 'docker compose' (without hyphen) instead of 'docker-compose'
```

### Manual Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (if not using Docker)
# Ensure PostgreSQL is running on localhost:5432

# Run migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Container registry access

### Deployment Steps

1. **Build and push container images**
   ```bash
   # Backend
   docker build -t your-registry/todo-backend:latest ./backend
   docker push your-registry/todo-backend:latest

   # Frontend
   docker build -t your-registry/todo-frontend:latest ./frontend
   docker push your-registry/todo-frontend:latest
   ```

2. **Create namespace**
   ```bash
   kubectl create namespace todo-app
   ```

3. **Deploy PostgreSQL**
   ```bash
   kubectl apply -f k8s/postgres/ -n todo-app
   ```

4. **Create secrets**
   ```bash
   kubectl create secret generic todo-db-credentials \
     --from-literal=DB_USER=postgres \
     --from-literal=DB_PASSWORD=<your-secure-password> \
     -n todo-app
   ```

5. **Deploy application**
   ```bash
   kubectl apply -f k8s/backend/ -n todo-app
   kubectl apply -f k8s/frontend/ -n todo-app
   kubectl apply -f k8s/ingress/ -n todo-app
   ```

6. **Verify deployment**
   ```bash
   kubectl get pods -n todo-app
   kubectl get svc -n todo-app
   ```

### Health Checks

The backend exposes a health endpoint for Kubernetes probes:

```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
```

## API Documentation

### Base URL
- Local: `http://localhost:8000/api`
- Production: `https://your-domain.com/api`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check with database status |
| `GET` | `/notes` | List all notes |
| `POST` | `/notes` | Create a new note |
| `GET` | `/notes/{id}` | Get a specific note |
| `PUT` | `/notes/{id}` | Update a note |
| `DELETE` | `/notes/{id}` | Delete a note |

### Note Schema

```json
{
  "id": "uuid",
  "title": "string (max 255 chars)",
  "content": "string (optional)",
  "color": "string (hex color, e.g., #FFEB3B)",
  "x_position": "float (>= 0)",
  "y_position": "float (>= 0)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Example Requests

**Create a note:**
```bash
curl -X POST http://localhost:8000/api/notes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Task",
    "content": "Remember to complete this",
    "color": "#FFEB3B",
    "x_position": 100,
    "y_position": 150
  }'
```

**Update note position:**
```bash
curl -X PUT http://localhost:8000/api/notes/{id} \
  -H "Content-Type: application/json" \
  -d '{
    "x_position": 250,
    "y_position": 300
  }'
```

### Interactive Documentation

Access the auto-generated API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `Todo Whiteboard API` |
| `DEBUG` | Enable debug mode | `false` |
| `DATABASE_URL` | Full database connection URL | - |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `todo_whiteboard` |
| `DB_USER` | Database username | `postgres` |
| `DB_PASSWORD` | Database password | `postgres` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:3000","http://localhost:5173"]` |

> **Note**: If `DATABASE_URL` is provided, it takes precedence over individual DB_* variables.

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `/api` |

## Project Structure

```
_vcluster_todo/
├── .github/
│   └── README.md           # This file
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── config.py       # Application configuration
│   │   ├── database.py     # Database connection setup
│   │   ├── models.py       # SQLAlchemy ORM models
│   │   ├── schemas.py      # Pydantic request/response schemas
│   │   └── routers/
│   │       ├── __init__.py
│   │       └── notes.py    # Notes CRUD endpoints
│   ├── alembic/            # Database migrations
│   ├── docker-compose.yml  # Local development setup
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.jsx        # React entry point
│   │   ├── App.jsx         # Root component
│   │   ├── components/
│   │   │   ├── Whiteboard.jsx    # Main whiteboard container
│   │   │   ├── PostItNote.jsx    # Draggable note component
│   │   │   └── AddNoteButton.jsx # New note creation button
│   │   ├── hooks/
│   │   │   └── useNotes.js       # API integration hook
│   │   └── styles/
│   │       ├── global.css
│   │       ├── Whiteboard.module.css
│   │       ├── PostItNote.module.css
│   │       └── AddNoteButton.module.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── k8s/                    # Kubernetes manifests
    ├── backend/
    ├── frontend/
    ├── postgres/
    └── ingress/
```

## Contributing

We welcome contributions to the Todo Whiteboard project. Please follow these guidelines:

### Development Workflow

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the code style guidelines
3. **Write tests** for new functionality
4. **Update documentation** as needed
5. **Submit a pull request** with a clear description

### Code Style

**Backend (Python)**
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Document functions with docstrings
- Run `ruff` or `flake8` for linting

**Frontend (JavaScript/React)**
- Use functional components with hooks
- Follow ESLint configuration in the project
- Use CSS Modules for component styling
- Prefer `const` over `let` when possible

### Commit Messages

Use conventional commit format:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(frontend): add color picker to post-it notes
fix(backend): handle database connection timeout
docs: update API documentation
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Reporting Issues

When reporting bugs, please include:
- Description of the expected vs actual behavior
- Steps to reproduce
- Environment details (OS, browser, versions)
- Relevant logs or screenshots

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

Built with care for the vcluster demonstration platform.
