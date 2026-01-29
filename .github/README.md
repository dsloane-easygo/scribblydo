# Scribblydo

A modern, real-time collaborative whiteboard application featuring draggable post-it notes, live 
cursor tracking, and instant updates. Built with React and FastAPI, designed for cloud-native 
deployment on Kubernetes.

## Features

### Core Features
- **Multiple Whiteboards**: Create and manage multiple named whiteboards (public or private)
- **Draggable Post-it Notes**: Intuitive drag-and-drop interface for organizing tasks
- **Real-time Editing**: Edit note titles and content with auto-save functionality
- **Color Customization**: Choose from 6 vibrant post-it colors
- **Persistent Positioning**: Note positions are saved and restored across sessions
- **User Authentication**: Secure login and registration with JWT tokens

### Real-Time Collaboration
- **Live Cursor Tracking**: See other users' mouse cursors on shared whiteboards
- **Instant Updates**: Notes created/moved/edited/deleted appear instantly for all viewers
- **User Presence**: Right sidebar shows online users and who's viewing the current board
- **WebSocket Communication**: Low-latency real-time updates via WebSocket
- **NATS Messaging**: Scalable pub/sub messaging for distributed deployments

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Browser                                         │
│  ┌─────────────┐                                      ┌─────────────────┐   │
│  │   Sidebar   │  ┌─────────────────────────────────┐ │  Right Sidebar  │   │
│  │ ─────────── │  │                                 │ │ ─────────────── │   │
│  │ Whiteboards │  │         Whiteboard Area         │ │  Online Users   │   │
│  │ • Board 1   │  │   ┌─────┐  ┌─────┐  ┌─────┐    │ │  • User 1 (you) │   │
│  │ • Board 2   │  │   │Note │  │Note │  │Note │    │ │  • User 2       │   │
│  │ + New Board │  │   └─────┘  └─────┘  └─────┘    │ │ ─────────────── │   │
│  │ ─────────── │  │        ↖ cursor (User 2)       │ │  Viewing Board  │   │
│  │ + New Note  │  │                                 │ │  • User 2       │   │
│  │ Logout      │  └─────────────────────────────────┘ └─────────────────┘   │
│  └─────────────┘                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
         │                         │ WebSocket                    │
         │ HTTP/REST API           │ (real-time)                  │
         ▼                         ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Kubernetes Cluster                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Frontend   │  │    Backend   │  │  PostgreSQL  │  │     NATS     │    │
│  │ (React+Nginx)│──│   (FastAPI)  │──│  (Database)  │  │  (Messaging) │    │
│  │  Port: 80    │  │  Port: 8000  │  │  Port: 5432  │  │  Port: 4222  │    │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  └──────────────┘    │
│                           │                                    │            │
│                           └────────────────────────────────────┘            │
│                                        Pub/Sub                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.x | UI framework |
| Vite | 5.0.x | Build tool and dev server |
| react-draggable | 4.4.x | Drag-and-drop functionality |
| CSS Modules | - | Scoped component styling |
| WebSocket API | - | Real-time communication |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.109.x | Web framework |
| Uvicorn | 0.27.x | ASGI server |
| SQLAlchemy | 2.0.x | ORM and database toolkit |
| asyncpg | 0.29.x | Async PostgreSQL driver |
| Pydantic | 2.5.x | Data validation |
| Alembic | 1.13.x | Database migrations |
| websockets | 12.x | WebSocket support |
| nats-py | 2.6.x | NATS messaging client |
| python-jose | 3.3.x | JWT token handling |
| passlib/bcrypt | 4.x | Password hashing |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| PostgreSQL 16 | Primary database |
| NATS 2.10 | Message broker for real-time features |
| Docker | Containerization |
| Docker Compose | Local development |
| Kubernetes | Production orchestration |
| Kustomize | K8s configuration management |

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Make (optional, for convenience commands)

### Using Makefile (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd _vcluster_todo

# Quick start - sets up everything
make quick-start

# In another terminal, start the frontend
make frontend-dev
```

### Manual Setup

```bash
# Clone the repository
git clone <repository-url>
cd _vcluster_todo

# Start the backend services (PostgreSQL, NATS, API)
cd backend
docker compose up -d --build

# Watch logs to verify startup
docker compose logs -f

# In a new terminal, start the frontend
cd ../frontend
npm install
npm run dev
```

### Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | Main application |
| Backend API | http://localhost:8000 | REST API |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| NATS Monitoring | http://localhost:8222 | NATS server stats |

### Default Test Users

Register new users through the UI, or use the API:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

---

## Makefile Commands

Run `make help` to see all available commands:

### Development
| Command | Description |
|---------|-------------|
| `make setup` | Set up complete development environment |
| `make dev` | Start backend + frontend development |
| `make teardown` | Stop all services and remove data |
| `make quick-start` | Onboarding for new developers |

### Backend
| Command | Description |
|---------|-------------|
| `make backend-up` | Start PostgreSQL, NATS, and API |
| `make backend-down` | Stop backend services |
| `make backend-logs` | View all backend logs |
| `make backend-logs-api` | View API server logs |
| `make backend-shell` | Open shell in backend container |
| `make backend-db-shell` | Open PostgreSQL shell |
| `make backend-migrate` | Run database migrations |

### Frontend
| Command | Description |
|---------|-------------|
| `make frontend-dev` | Start development server |
| `make frontend-build` | Build for production |
| `make frontend-preview` | Preview production build |

### Code Quality
| Command | Description |
|---------|-------------|
| `make lint` | Run linters on all code |
| `make format` | Format all code |
| `make status` | Show service status and health |
| `make health` | Check health of all services |

### Kubernetes
| Command | Description |
|---------|-------------|
| `make k8s-build` | Build Docker images for K8s |
| `make k8s-deploy-local` | Deploy to local Kubernetes |
| `make k8s-delete` | Delete K8s deployment |
| `make k8s-status` | Show K8s deployment status |

---

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register a new user |
| `POST` | `/api/auth/login` | Login and get JWT token |
| `GET` | `/api/auth/me` | Get current user info |

### Whiteboard Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/whiteboards` | List all accessible whiteboards |
| `POST` | `/api/whiteboards` | Create a new whiteboard |
| `GET` | `/api/whiteboards/{id}` | Get a specific whiteboard |
| `PUT` | `/api/whiteboards/{id}` | Update a whiteboard (owner only) |
| `DELETE` | `/api/whiteboards/{id}` | Delete a whiteboard (owner only) |

### Note Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/notes?whiteboard_id={id}` | List notes for a whiteboard |
| `POST` | `/api/notes` | Create a new note |
| `GET` | `/api/notes/{id}` | Get a specific note |
| `PUT` | `/api/notes/{id}` | Update a note |
| `DELETE` | `/api/notes/{id}` | Delete a note |

### WebSocket Endpoint

| Endpoint | Description |
|----------|-------------|
| `WS /ws` | Real-time collaboration WebSocket |

### Health Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check with database status |

### Example Requests

**Register a user:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=myuser&password=mypassword"
```

**Create a whiteboard (authenticated):**
```bash
curl -X POST http://localhost:8000/api/whiteboards \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "My Tasks", "is_private": false}'
```

**Create a note (authenticated):**
```bash
curl -X POST http://localhost:8000/api/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "whiteboard_id": "your-whiteboard-uuid",
    "title": "My Task",
    "content": "Remember to complete this",
    "color": "#FFEB3B",
    "x_position": 100,
    "y_position": 150
  }'
```

---

## WebSocket Protocol

### Connection

1. Connect to `ws://localhost:8000/ws`
2. Send auth message: `{"type": "auth", "payload": {"token": "JWT_TOKEN"}}`
3. Receive: `{"type": "auth_success", "payload": {...}}`

### Client → Server Messages

| Type | Payload | Description |
|------|---------|-------------|
| `auth` | `{token}` | Authenticate (must be first) |
| `join_whiteboard` | `{whiteboard_id}` | Start viewing a board |
| `leave_whiteboard` | `{}` | Stop viewing |
| `cursor_move` | `{x, y}` | Update cursor position |
| `ping` | `{}` | Keep-alive ping |

### Server → Client Messages

| Type | Payload | Description |
|------|---------|-------------|
| `auth_success` | `{user_id, username}` | Authentication successful |
| `whiteboard_joined` | `{whiteboard_id, viewers}` | Joined whiteboard |
| `user_joined` | `{user, viewers}` | Another user joined |
| `user_left` | `{user_id, viewers}` | User left |
| `cursor_update` | `{user_id, username, x, y}` | Cursor position |
| `note_created` | `{note, by_user}` | Note was created |
| `note_updated` | `{note, by_user}` | Note was updated |
| `note_deleted` | `{note_id, by_user}` | Note was deleted |
| `whiteboard_updated` | `{whiteboard, by_user}` | Whiteboard updated |
| `presence_update` | `{online_users}` | Online users changed |
| `pong` | `{}` | Response to ping |
| `error` | `{code, message}` | Error occurred |

---

## Kubernetes Deployment

### Prerequisites

1. **Docker Desktop** with Kubernetes enabled (or any K8s cluster)
2. **kubectl** installed
3. Verify Kubernetes is running:
   ```bash
   kubectl cluster-info
   kubectl get nodes
   ```

### Deploy to Local Kubernetes

```bash
# Build images
make k8s-build

# Deploy
make k8s-deploy-local

# Watch pods come up
kubectl get pods -n todo-app -w

# Access via NodePort
open http://localhost:30080
```

### Deploy to AWS EKS

```bash
# Preview what will be deployed
kubectl kustomize k8s/overlays/aws

# Deploy
kubectl apply -k k8s/overlays/aws
```

### Kubernetes Structure

```
k8s/
├── base/                          # Base manifests
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── postgres-secret.yaml
│   ├── configmap.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-service.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   └── ingress.yaml
└── overlays/
    ├── local/                     # Docker Desktop
    │   └── kustomization.yaml
    └── aws/                       # AWS EKS
        ├── kustomization.yaml
        └── pdb.yaml
```

### Key K8s Features

- **Init Containers**: Database migrations run before backend starts
- **Health Checks**: Liveness and readiness probes on all services
- **Security Contexts**: Non-root users, dropped capabilities
- **Resource Limits**: CPU and memory limits defined
- **Pod Disruption Budgets**: Production stability (AWS overlay)

---

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `todo_whiteboard` |
| `DB_USER` | Database username | `postgres` |
| `DB_PASSWORD` | Database password | `postgres` |
| `SECRET_KEY` | JWT signing key | (required) |
| `NATS_URL` | NATS server URL | `nats://nats:4222` |
| `DEBUG` | Enable debug mode | `false` |
| `CORS_ORIGINS` | Allowed origins (JSON) | `["http://localhost:5173"]` |

---

## Project Structure

```
_vcluster_todo/
├── Makefile                  # Development commands
├── .github/
│   └── README.md             # This file
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + WebSocket endpoint
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database connection
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── auth.py           # JWT authentication
│   │   ├── routers/          # API routers
│   │   │   ├── auth.py
│   │   │   ├── notes.py
│   │   │   └── whiteboards.py
│   │   ├── websocket/        # WebSocket handlers
│   │   │   ├── connection_manager.py
│   │   │   └── handlers.py
│   │   └── messaging/        # NATS client
│   │       └── nats_client.py
│   ├── alembic/              # Database migrations
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.jsx          # React entry point
│   │   ├── App.jsx           # Root component
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Whiteboard.jsx
│   │   │   ├── PostItNote.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── cursors/      # Cursor tracking
│   │   │   └── presence/     # Online users
│   │   ├── context/          # React contexts
│   │   │   ├── AuthContext.jsx
│   │   │   ├── WebSocketContext.jsx
│   │   │   └── PresenceContext.jsx
│   │   ├── hooks/            # Custom hooks
│   │   └── styles/           # CSS Modules
│   ├── Dockerfile
│   └── package.json
├── k8s/                      # Kubernetes manifests
│   ├── base/
│   └── overlays/
└── scripts/                  # Deployment scripts
```

---

## Troubleshooting

### Docker Compose Issues

**Backend can't connect to database**
```bash
docker compose ps         # Check if postgres is healthy
docker compose logs postgres
```

**Backend can't connect to NATS**
```bash
docker compose logs nats
curl http://localhost:8222/healthz  # Should return "ok"
```

**Migration errors**
```bash
cd backend
docker compose down -v    # Remove volumes and start fresh
docker compose up -d --build
```

### WebSocket Issues

**WebSocket connection fails**
- Check that you're authenticated first
- Verify the token is valid
- Check browser console for errors
- Ensure Vite proxy is configured for `/ws`

**Cursors not showing**
- Both users must be viewing the same whiteboard
- Check WebSocket connection status in browser devtools
- Verify NATS is running: `curl http://localhost:8222/healthz`

### Kubernetes Issues

**Pods stuck in Pending**
```bash
kubectl describe pod -n todo-app <pod-name>
# Check for resource constraints or PVC issues
```

**Backend CrashLoopBackOff**
```bash
kubectl logs -n todo-app -l app.kubernetes.io/name=backend --previous
# Check for database connection or migration errors
```

**Init container (migration) failing**
```bash
kubectl logs -n todo-app <backend-pod-name> -c migrate
```

---

## License

This project is licensed under the MIT License.
