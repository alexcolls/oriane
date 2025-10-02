#!/bin/bash

# =============================================================================
# Build and Deploy Script for Search API KinD Cluster
# =============================================================================
# This script builds the docker image of the search API and deploys it to KinD
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLUSTER_NAME="search-api-test"
NAMESPACE="search-api"
SERVICE_NAME="search-api-service"

echo "=== Build and Deploy Search API ==="
echo "Project root: $PROJECT_ROOT"
echo "Cluster: $CLUSTER_NAME"
echo "Namespace: $NAMESPACE"

# Change to project root
cd "$PROJECT_ROOT"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
if ! command_exists docker; then
    echo "ERROR: Docker is not installed"
    exit 1
fi

if ! command_exists kind; then
    echo "ERROR: KinD is not installed"
    exit 1
fi

if ! command_exists kubectl; then
    echo "ERROR: kubectl is not installed"
    exit 1
fi

# Check if cluster exists
if ! kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    echo "ERROR: KinD cluster '${CLUSTER_NAME}' does not exist"
    echo "Please run './scripts/setup-kind-cluster.sh' first"
    exit 1
fi

# Switch to the correct kubectl context
kubectl config use-context "kind-${CLUSTER_NAME}"

# Build Docker image
echo "Building Docker image for search API..."
docker build -f Dockerfile.test -t search-api:latest .

# Load image into KinD cluster
echo "Loading Docker image into KinD cluster..."
kind load docker-image search-api:latest --name "$CLUSTER_NAME"

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl rollout status deployment/search-api -n "$NAMESPACE" --timeout=300s

# Display deployment status
echo ""
echo "=== Deployment Status ==="
kubectl get all -n "$NAMESPACE"

# Get service information
echo ""
echo "=== Service Information ==="
kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o wide

SERVICE_IP=$(kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
echo "Service IP: $SERVICE_IP"

# Test the deployment
echo ""
echo "=== Testing Deployment ==="
kubectl port-forward -n "$NAMESPACE" service/"$SERVICE_NAME" 8080:80 &
PORT_FORWARD_PID=$!

# Wait for port-forward to be ready
echo "Waiting for port-forward to be ready..."
sleep 5

# Test endpoints
echo "Testing health endpoint..."
if curl -sf http://localhost:8080/health; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
fi

echo ""
echo "Testing root endpoint..."
if curl -sf http://localhost:8080/; then
    echo "✓ Root endpoint test passed"
else
    echo "✗ Root endpoint test failed"
fi

echo ""
echo "Testing debug settings endpoint..."
if curl -sf http://localhost:8080/debug/settings; then
    echo "✓ Debug settings endpoint test passed"
else
    echo "✗ Debug settings endpoint test failed"
fi

# Cleanup port-forward
kill $PORT_FORWARD_PID 2>/dev/null || true

echo ""
echo "✓ Build and deploy complete!"
echo "Search API is accessible at http://${SERVICE_IP}"
echo ""
echo "To access the API:"
echo "  kubectl port-forward -n $NAMESPACE service/$SERVICE_NAME 8080:80"
echo "  curl http://localhost:8080/health"
