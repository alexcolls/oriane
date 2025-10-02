#!/bin/bash

# =============================================================================
# Build and Deploy Script for KinD Cluster
# =============================================================================
# This script builds the docker image of the pipeline and deploys it to KinD
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_NAME="pipeline-api-service"

function build_docker_image() {
    echo "Building Docker image for pipeline API..."
    docker build -f "$PROJECT_ROOT/Dockerfile.test" -t pipeline-api-test:latest "."
}

function load_image_to_kind() {
    CLUSTER_NAME="pipeline-test"
    echo "Loading Docker image into KinD cluster..."
    kind load docker-image --name "$CLUSTER_NAME" "pipeline-api-test:latest"
}

function apply_k8s_manifests() {
    echo "Applying Kubernetes manifests..."
    kubectl apply -f "$PROJECT_ROOT/k8s/configmap.yaml"
    kubectl apply -f "$PROJECT_ROOT/k8s/secret.yaml"
    kubectl apply -f "$PROJECT_ROOT/k8s/deployment.yaml"
    kubectl apply -f "$PROJECT_ROOT/k8s/service.yaml"
}

build_docker_image
load_image_to_kind
apply_k8s_manifests

# Wait for deployment
kubectl rollout status deployment/pipeline-api -n pipeline --timeout=120s

# Display all resources
echo ""
echo "=== Kubernetes Resources ==="
kubectl get all -n pipeline

# Display service details
echo ""
echo "Service details:"
kubectl get service "$SERVICE_NAME" -n pipeline

# Display endpoint information
SERVICE_IP=$(kubectl get service "${SERVICE_NAME}" -n pipeline -o jsonpath='{.spec.clusterIP}')
echo "Cluster IP for ${SERVICE_NAME}: $SERVICE_IP"

# Health Check - Test container
kubectl port-forward -n pipeline service/${SERVICE_NAME} 8080:80 &
PORT_FORWARD_PID=$!

# Wait for port-forward
sleep 3

# Perform a health check and stop port-forward
curl -sf http://localhost:8080/health
curl -sf http://localhost:8080/

# Cleanup
kill $PORT_FORWARD_PID 2>/dev/null || true

echo ""
echo "✓ Build and deploy complete!"
echo "Pipeline API is accessible at http://${SERVICE_IP}"
