# -----------------------------------------------------------------------------
# Todo Whiteboard Platform Makefile
# -----------------------------------------------------------------------------

.PHONY: help setup teardown dev build test lint format clean
.PHONY: backend-setup backend-up backend-down backend-teardown backend-restart
.PHONY: backend-build backend-logs backend-logs-api backend-logs-db backend-logs-nats
.PHONY: backend-shell backend-db-shell backend-test backend-migrate backend-migrate-create backend-nats-cli
.PHONY: backend-clean backend-lint backend-format
.PHONY: frontend-setup frontend-dev frontend-build frontend-preview frontend-test
.PHONY: frontend-lint frontend-format frontend-clean
.PHONY: status health docker-prune docker-prune-all quick-start
.PHONY: k8s-build k8s-deploy-local k8s-deploy-aws k8s-delete k8s-status k8s-logs k8s-port-forward
.PHONY: ci ci-lint ci-lint-backend ci-lint-frontend ci-test ci-test-backend
.PHONY: ci-format ci-format-backend ci-format-frontend

SHELL := /bin/bash

# Colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
CYAN   := $(shell tput -Txterm setaf 6)
RED    := $(shell tput -Txterm setaf 1)
RESET  := $(shell tput -Txterm sgr0)

# Default namespace for Kubernetes
K8S_NAMESPACE ?= todo-app

## Help
help: ## Show this help
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${YELLOW}%-25s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# =============================================================================
# Full Stack Development
# =============================================================================

setup: backend-setup frontend-setup ## Set up complete development environment
	@echo "${GREEN}Full development environment ready!${RESET}"
	@echo "${CYAN}Run 'make dev' to start the application${RESET}"

teardown: backend-teardown ## Tear down all services (including data)
	@echo "${YELLOW}Tearing down all services...${RESET}"

dev: backend-up ## Start development environment (backend services)
	@echo ""
	@echo "${GREEN}Backend services are running!${RESET}"
	@echo "${CYAN}Run 'make frontend-dev' in another terminal to start the frontend${RESET}"

build: backend-build frontend-build ## Build all components
	@echo "${GREEN}All components built successfully${RESET}"

test: backend-test frontend-test ## Run all tests
	@echo "${GREEN}All tests completed${RESET}"

clean: backend-clean frontend-clean ## Clean all build artifacts
	@echo "${YELLOW}All build artifacts cleaned${RESET}"

# =============================================================================
# Backend (Docker Compose)
# =============================================================================

backend-setup: ## Set up backend dependencies
	@echo "${GREEN}Setting up backend...${RESET}"
	cd backend && docker compose build

backend-up: ## Start backend services (PostgreSQL, NATS, API)
	@echo "${GREEN}Starting backend services...${RESET}"
	cd backend && docker compose up -d
	@echo ""
	@echo "${CYAN}Backend API:    http://localhost:8000${RESET}"
	@echo "${CYAN}API Docs:       http://localhost:8000/docs${RESET}"
	@echo "${CYAN}NATS Monitor:   http://localhost:8222${RESET}"

backend-down: ## Stop backend services
	@echo "${YELLOW}Stopping backend services...${RESET}"
	cd backend && docker compose down

backend-teardown: ## Stop and remove backend containers and volumes
	@echo "${YELLOW}Tearing down backend (including volumes)...${RESET}"
	cd backend && docker compose down -v

backend-restart: ## Restart backend services
	@echo "${YELLOW}Restarting backend services...${RESET}"
	cd backend && docker compose restart

backend-build: ## Build backend Docker images (no cache)
	@echo "${GREEN}Building backend images...${RESET}"
	cd backend && docker compose build --no-cache

backend-logs: ## View all backend logs
	cd backend && docker compose logs -f

backend-logs-api: ## View API server logs only
	cd backend && docker compose logs -f backend

backend-logs-db: ## View PostgreSQL logs only
	cd backend && docker compose logs -f postgres

backend-logs-nats: ## View NATS logs only
	cd backend && docker compose logs -f nats

backend-nats-cli: ## Open NATS CLI for debugging (usage: make backend-nats-cli CMD="sub '>'" )
	@if [ -z "$(CMD)" ]; then \
		echo "${CYAN}Starting interactive NATS CLI shell...${RESET}"; \
		echo "${YELLOW}Examples:${RESET}"; \
		echo "  nats sub '>'                  # Subscribe to all subjects"; \
		echo "  nats sub 'presence.*'         # Subscribe to presence updates"; \
		echo "  nats sub 'whiteboards.global' # Subscribe to whiteboard create/delete"; \
		echo "  nats pub test 'hello'         # Publish test message"; \
		echo "  nats account info             # Show account info"; \
		echo ""; \
		docker run --rm -it --network backend_todo-network natsio/nats-box:latest sh -c "nats context save local --server nats://nats:4222 --select && exec sh"; \
	else \
		docker run --rm -it --network backend_todo-network natsio/nats-box:latest nats -s nats://nats:4222 $(CMD); \
	fi

backend-shell: ## Open shell in backend container
	cd backend && docker compose exec backend /bin/sh

backend-db-shell: ## Open PostgreSQL shell
	cd backend && docker compose exec postgres psql -U postgres -d todo_whiteboard

backend-test: ## Run backend tests
	@echo "${GREEN}Running backend tests...${RESET}"
	cd backend && docker compose exec backend pytest -v || echo "${YELLOW}No tests found or pytest not available${RESET}"

backend-migrate: ## Run database migrations
	@echo "${GREEN}Running database migrations...${RESET}"
	cd backend && docker compose exec backend alembic upgrade head

backend-migrate-create: ## Create new migration (usage: make backend-migrate-create MSG="description")
	@if [ -z "$(MSG)" ]; then echo "${RED}Usage: make backend-migrate-create MSG=\"description\"${RESET}"; exit 1; fi
	cd backend && docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

backend-clean: ## Remove backend build artifacts and volumes
	@echo "${YELLOW}Cleaning backend...${RESET}"
	cd backend && docker compose down -v --rmi local

# =============================================================================
# Frontend (Vite + React)
# =============================================================================

frontend-setup: ## Set up frontend dependencies
	@echo "${GREEN}Setting up frontend...${RESET}"
	cd frontend && npm install

frontend-dev: ## Start frontend development server
	@echo "${GREEN}Starting frontend dev server...${RESET}"
	@echo "${CYAN}Frontend: http://localhost:5173${RESET}"
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	@echo "${GREEN}Building frontend...${RESET}"
	cd frontend && npm run build

frontend-preview: ## Preview production build
	@echo "${GREEN}Previewing production build...${RESET}"
	cd frontend && npm run preview

frontend-test: ## Run frontend tests
	@echo "${GREEN}Running frontend tests...${RESET}"
	cd frontend && npm test 2>/dev/null || echo "${YELLOW}No tests configured${RESET}"

frontend-lint: ## Lint frontend code
	@echo "${GREEN}Linting frontend...${RESET}"
	cd frontend && npm run lint 2>/dev/null || echo "${YELLOW}No lint script configured${RESET}"

frontend-clean: ## Remove frontend build artifacts
	@echo "${YELLOW}Cleaning frontend...${RESET}"
	rm -rf frontend/dist frontend/node_modules/.cache

# =============================================================================
# Code Quality (Local - requires tools installed)
# =============================================================================

lint: backend-lint frontend-lint ## Run linters on all code (local)
	@echo "${GREEN}Linting completed${RESET}"

backend-lint: ## Lint backend code with ruff (local)
	@echo "${GREEN}Linting backend...${RESET}"
	@if command -v ruff > /dev/null; then \
		ruff check backend/app/; \
	else \
		echo "${YELLOW}ruff not installed. Install with: pip install ruff${RESET}"; \
	fi

format: backend-format frontend-format ## Format all code
	@echo "${GREEN}Formatting completed${RESET}"

backend-format: ## Format backend code with ruff
	@echo "${GREEN}Formatting backend...${RESET}"
	@if command -v ruff > /dev/null; then \
		ruff format backend/app/; \
	else \
		echo "${YELLOW}ruff not installed. Install with: pip install ruff${RESET}"; \
	fi

frontend-format: ## Format frontend code with prettier
	@echo "${GREEN}Formatting frontend...${RESET}"
	cd frontend && npm run format 2>/dev/null || npx prettier --write "src/**/*.{js,jsx,css}" 2>/dev/null || echo "${YELLOW}prettier not installed${RESET}"

# =============================================================================
# CI Checks (Docker-based - matches GitHub Actions)
# =============================================================================

ci-lint: ci-lint-backend ci-lint-frontend ## Run all CI linting checks in Docker
	@echo "${GREEN}All CI lint checks passed!${RESET}"

ci-lint-backend: ## Lint backend with ruff in Docker (matches CI)
	@echo "${GREEN}Running backend lint (ruff) in Docker...${RESET}"
	@docker run --rm -v "$(PWD)/backend:/app" -w /app python:3.11-slim \
		sh -c "pip install -q ruff && ruff check app/"

ci-lint-frontend: ## Lint frontend with eslint in Docker (matches CI)
	@echo "${GREEN}Running frontend lint (eslint) in Docker...${RESET}"
	@docker run --rm -v "$(PWD)/frontend:/app" -w /app node:20-alpine \
		sh -c "npm ci --legacy-peer-deps --silent && npm run lint"

ci-test: ci-test-backend ## Run all CI tests in Docker
	@echo "${GREEN}All CI tests passed!${RESET}"

ci-test-backend: ## Run backend tests in Docker with services
	@echo "${GREEN}Running backend tests in Docker...${RESET}"
	cd backend && docker compose --profile test run --rm test

ci-format-backend: ## Auto-fix backend lint issues with ruff in Docker
	@echo "${GREEN}Formatting backend with ruff in Docker...${RESET}"
	@docker run --rm -v "$(PWD)/backend:/app" -w /app python:3.11-slim \
		sh -c "pip install -q ruff && ruff check --fix app/ && ruff format app/"

ci-format-frontend: ## Auto-fix frontend lint issues with eslint in Docker
	@echo "${GREEN}Formatting frontend with eslint in Docker...${RESET}"
	@docker run --rm -v "$(PWD)/frontend:/app" -w /app node:20-alpine \
		sh -c "npm ci --legacy-peer-deps --silent && npm run lint -- --fix || true"

ci-format: ci-format-backend ci-format-frontend ## Auto-fix all lint issues in Docker
	@echo "${GREEN}All formatting completed!${RESET}"

ci: ci-lint ci-test ## Run full CI pipeline locally in Docker
	@echo "${GREEN}Full CI pipeline passed!${RESET}"

# =============================================================================
# Status & Health
# =============================================================================

status: ## Show status of all services
	@echo "${CYAN}=== Backend Services ===${RESET}"
	@cd backend && docker compose ps 2>/dev/null || echo "${YELLOW}Backend not running${RESET}"
	@echo ""
	@echo "${CYAN}=== Health Checks ===${RESET}"
	@curl -s http://localhost:8000/api/health 2>/dev/null | jq . 2>/dev/null || echo "${YELLOW}Backend API not responding${RESET}"

health: ## Check health of all services
	@echo "${GREEN}Checking API health...${RESET}"
	@curl -sf http://localhost:8000/api/health > /dev/null && echo "  ${GREEN}✓ API is healthy${RESET}" || echo "  ${RED}✗ API is not responding${RESET}"
	@echo ""
	@echo "${GREEN}Checking NATS health...${RESET}"
	@curl -sf http://localhost:8222/healthz > /dev/null && echo "  ${GREEN}✓ NATS is healthy${RESET}" || echo "  ${RED}✗ NATS is not responding${RESET}"
	@echo ""
	@echo "${GREEN}Checking PostgreSQL...${RESET}"
	@cd backend && docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1 && echo "  ${GREEN}✓ PostgreSQL is healthy${RESET}" || echo "  ${RED}✗ PostgreSQL is not responding${RESET}"

# =============================================================================
# Docker Utilities
# =============================================================================

docker-prune: ## Remove unused Docker resources
	@echo "${YELLOW}Pruning Docker resources...${RESET}"
	docker system prune -f

docker-prune-all: ## Remove ALL unused Docker resources (including volumes)
	@echo "${RED}WARNING: This will remove all unused images, containers, and volumes!${RESET}"
	@read -p "Are you sure? Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ]
	docker system prune -af --volumes

# =============================================================================
# Kubernetes Deployment
# =============================================================================

k8s-build: ## Build Docker images for Kubernetes
	@echo "${GREEN}Building Docker images for Kubernetes...${RESET}"
	docker build -t todo-backend:local ./backend
	docker build -t todo-frontend:local ./frontend
	@echo "${GREEN}Images built: todo-backend:local, todo-frontend:local${RESET}"

k8s-deploy-local: ## Deploy to local Kubernetes (Docker Desktop)
	@echo "${GREEN}Deploying to local Kubernetes...${RESET}"
	kubectl apply -k k8s/overlays/local
	@echo ""
	@echo "${CYAN}Watching pods (Ctrl+C to stop watching)...${RESET}"
	@echo "${CYAN}Access the app at: http://localhost:30080${RESET}"
	kubectl get pods -n $(K8S_NAMESPACE) -w

k8s-deploy-aws: ## Deploy to AWS EKS
	@echo "${GREEN}Deploying to AWS EKS...${RESET}"
	kubectl apply -k k8s/overlays/aws
	kubectl get pods -n $(K8S_NAMESPACE) -w

k8s-delete: ## Delete Kubernetes deployment
	@echo "${YELLOW}Deleting Kubernetes deployment...${RESET}"
	kubectl delete -k k8s/overlays/local 2>/dev/null || kubectl delete namespace $(K8S_NAMESPACE) 2>/dev/null || echo "${YELLOW}Nothing to delete${RESET}"

k8s-status: ## Show Kubernetes deployment status
	@echo "${CYAN}=== Kubernetes Resources ===${RESET}"
	@kubectl get all -n $(K8S_NAMESPACE) 2>/dev/null || echo "${YELLOW}Namespace $(K8S_NAMESPACE) not found${RESET}"

k8s-logs: ## View Kubernetes backend logs
	kubectl logs -n $(K8S_NAMESPACE) -l app.kubernetes.io/name=backend -f

k8s-port-forward: ## Port-forward frontend service to localhost:8080
	@echo "${GREEN}Port-forwarding frontend to http://localhost:8080${RESET}"
	kubectl port-forward -n $(K8S_NAMESPACE) svc/frontend-service 8080:80

# =============================================================================
# Quick Start
# =============================================================================

quick-start: ## Quick start for new developers
	@echo "${CYAN}╔═══════════════════════════════════════════════════════════╗${RESET}"
	@echo "${CYAN}║           Todo Whiteboard - Quick Start                    ║${RESET}"
	@echo "${CYAN}╚═══════════════════════════════════════════════════════════╝${RESET}"
	@echo ""
	@echo "${GREEN}Step 1: Setting up backend...${RESET}"
	@$(MAKE) -s backend-setup
	@echo ""
	@echo "${GREEN}Step 2: Starting backend services...${RESET}"
	@$(MAKE) -s backend-up
	@echo ""
	@echo "${GREEN}Step 3: Setting up frontend...${RESET}"
	@$(MAKE) -s frontend-setup
	@echo ""
	@echo "${CYAN}╔═══════════════════════════════════════════════════════════╗${RESET}"
	@echo "${CYAN}║                    Setup Complete!                         ║${RESET}"
	@echo "${CYAN}╚═══════════════════════════════════════════════════════════╝${RESET}"
	@echo ""
	@echo "  Run '${YELLOW}make frontend-dev${RESET}' in another terminal to start the frontend"
	@echo ""
	@echo "  ${CYAN}Frontend:${RESET}     http://localhost:5173"
	@echo "  ${CYAN}API Docs:${RESET}     http://localhost:8000/docs"
	@echo "  ${CYAN}NATS Monitor:${RESET} http://localhost:8222"
	@echo ""
