#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# deploy-local-k8s.sh - Deploy Todo Whiteboard to Docker Desktop Kubernetes
# -----------------------------------------------------------------------------
set -eo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Check prerequisites
check_prereqs() {
    log_info "Checking prerequisites..."

    local missing=()

    command -v docker >/dev/null 2>&1 || missing+=("docker")
    command -v kubectl >/dev/null 2>&1 || missing+=("kubectl")

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        exit 1
    fi

    # Check Kubernetes is running
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "Cannot connect to Kubernetes cluster."
        log_error "Ensure Docker Desktop Kubernetes is enabled and running."
        exit 1
    fi

    log_info "  ✓ Docker installed"
    log_info "  ✓ kubectl installed"
    log_info "  ✓ Kubernetes cluster running"
}

# Build images
build_images() {
    log_info "Building container images..."

    cd "$PROJECT_ROOT"

    log_info "  Building backend image..."
    docker build -t todo-backend:local ./backend

    log_info "  Building frontend image..."
    docker build -t todo-frontend:local ./frontend

    log_info "  ✓ Images built successfully"
}

# Deploy to Kubernetes
deploy() {
    log_info "Deploying to Kubernetes..."

    cd "$PROJECT_ROOT"

    # Apply manifests
    kubectl apply -k k8s/overlays/local

    log_info "Waiting for pods to be ready..."

    # Wait for postgres
    kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/name=postgres \
        -n todo-app \
        --timeout=120s || true

    # Wait for backend (may take longer due to init container)
    kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/name=backend \
        -n todo-app \
        --timeout=180s || true

    # Wait for frontend
    kubectl wait --for=condition=ready pod \
        -l app.kubernetes.io/name=frontend \
        -n todo-app \
        --timeout=120s || true

    log_info "  ✓ Deployment complete"
}

# Show status
show_status() {
    echo ""
    log_info "Deployment Status:"
    echo ""
    kubectl get pods -n todo-app
    echo ""
    kubectl get svc -n todo-app
    echo ""

    log_info "============================================"
    log_info "  Todo Whiteboard deployed successfully!"
    log_info "============================================"
    echo ""
    log_info "Access the application:"
    log_info "  • NodePort: http://localhost:30080"
    log_info "  • Port Forward: kubectl port-forward -n todo-app svc/frontend-service 8080:80"
    echo ""
    log_info "Useful commands:"
    log_info "  • View logs: kubectl logs -n todo-app -l app.kubernetes.io/name=backend"
    log_info "  • Delete: kubectl delete -k k8s/overlays/local"
    echo ""
}

# Main
main() {
    echo ""
    log_info "============================================"
    log_info "  Todo Whiteboard - Local K8s Deployment"
    log_info "============================================"
    echo ""

    check_prereqs
    build_images
    deploy
    show_status
}

main "$@"
