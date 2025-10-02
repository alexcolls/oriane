#!/bin/bash

# KinD Cluster Integration Test Script
# This script tests the pipeline API deployment on a KinD cluster

set -e

# Configuration
DOCKER_IMAGE="pipeline-api-test:latest"
K8S_NAMESPACE="pipeline"
SERVICE_NAME="pipeline-api-service"
CLUSTER_NAME="pipeline-test"

echo "=== KinD Cluster Integration Test ==="

# Check if KinD cluster is running
echo "Checking KinD cluster status..."
if ! kubectl cluster-info --context kind-${CLUSTER_NAME} >/dev/null 2>&1; then
    echo "ERROR: KinD cluster '${CLUSTER_NAME}' is not running"
    exit 1
fi

# Check if namespace exists
echo "Checking namespace..."
if ! kubectl get namespace ${K8S_NAMESPACE} >/dev/null 2>&1; then
    echo "ERROR: Namespace '${K8S_NAMESPACE}' does not exist"
    exit 1
fi

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl rollout status deployment/pipeline-api -n ${K8S_NAMESPACE} --timeout=120s

# Get the service cluster IP
echo "Getting service cluster IP..."
SERVICE_IP=$(kubectl get service ${SERVICE_NAME} -n ${K8S_NAMESPACE} -o jsonpath='{.spec.clusterIP}')
echo "Service IP: ${SERVICE_IP}"

# Test health endpoint using port-forward
echo "Testing health endpoint..."
kubectl port-forward -n ${K8S_NAMESPACE} service/${SERVICE_NAME} 8080:80 &
PORT_FORWARD_PID=$!

# Wait for port-forward to be ready
sleep 3

# Test the health endpoint
if curl -sf http://localhost:8080/health; then
    echo "✓ Health check passed"
    HEALTH_STATUS="PASS"
else
    echo "✗ Health check failed"
    HEALTH_STATUS="FAIL"
fi

# Test the root endpoint
if curl -sf http://localhost:8080/; then
    echo "✓ Root endpoint test passed"
    ROOT_STATUS="PASS"
else
    echo "✗ Root endpoint test failed"
    ROOT_STATUS="FAIL"
fi

# Clean up port-forward
kill $PORT_FORWARD_PID 2>/dev/null || true

# Display results
echo ""
echo "=== Test Results ==="
echo "Health endpoint: $HEALTH_STATUS"
echo "Root endpoint: $ROOT_STATUS"

# Check overall status
if [[ "$HEALTH_STATUS" == "PASS" && "$ROOT_STATUS" == "PASS" ]]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed!"
    exit 1
fi
