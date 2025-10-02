#!/bin/bash


# =============================================================================
# Local API Access Script using Port-Forwarding
# =============================================================================
# This script provides immediate access to the FastAPI docs through port-forwarding
# while the ingress is being set up or if external access is not available.
# =============================================================================

set -euo pipefail

# Set default values
K8S_NAMESPACE="oriane-pipeline-api"
LOCAL_PORT="8000"
SERVICE_NAME="oriane-pipeline-api-service"
SERVICE_PORT="80"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

# Check if pods are running
check_pods() {
    log "Checking if API pods are running..."
    
    RUNNING_PODS=$(kubectl get pods -n "$K8S_NAMESPACE" -l app=oriane-pipeline-api --field-selector=status.phase=Running --no-headers | wc -l)
    
    if [[ "$RUNNING_PODS" -eq 0 ]]; then
        error "No running API pods found. Please check your deployment status."
    fi
    
    success "Found $RUNNING_PODS running API pod(s)"
}

# Start port-forwarding
start_port_forward() {
    log "Starting port-forwarding to service $SERVICE_NAME..."
    
    # Check if port is already in use
    if lsof -i :$LOCAL_PORT >/dev/null 2>&1; then
        warning "Port $LOCAL_PORT is already in use. Trying to kill existing process..."
        pkill -f "kubectl.*port-forward.*$LOCAL_PORT" || true
        sleep 2
    fi
    
    echo ""
    echo "=== FastAPI Access URLs (Local) ==="
    echo "API Docs: http://localhost:$LOCAL_PORT/docs"
    echo "OpenAPI JSON: http://localhost:$LOCAL_PORT/openapi.json"
    echo "API Root: http://localhost:$LOCAL_PORT/"
    echo ""
    echo "Press Ctrl+C to stop port-forwarding"
    echo ""
    
    # Start port-forwarding
    kubectl port-forward service/$SERVICE_NAME -n "$K8S_NAMESPACE" $LOCAL_PORT:$SERVICE_PORT
}

# Main execution
main() {
    log "Setting up local access to FastAPI..."
    
    check_pods
    start_port_forward
}

# Handle Ctrl+C
trap 'echo ""; log "Port-forwarding stopped"; exit 0' INT

main "$@"
