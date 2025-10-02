#!/bin/bash

# =============================================================================
# Search API Integration Test Script for KinD Cluster
# =============================================================================
# This script runs integration tests against the Search API deployed in KinD
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLUSTER_NAME="search-api-test"
NAMESPACE="search-api"
SERVICE_NAME="search-api-service"


echo "=== KinD Cluster Integration Test: Search API ==="

# Function to cleanup on exit
cleanup() {
    if [ -n "$PORT_FORWARD_PID" ]; then
        echo "Cleaning up port-forward..."
        kill $PORT_FORWARD_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Check if KinD cluster is running
echo "Checking KinD cluster status..."
if ! kubectl cluster-info --context kind-${CLUSTER_NAME} >/dev/null 2>&1; then
    echo "ERROR: KinD cluster '${CLUSTER_NAME}' is not running"
    echo "Please run './scripts/setup-kind-cluster.sh' first"
    exit 1
fi

# Check if namespace exists
echo "Checking namespace..."
if ! kubectl get namespace ${NAMESPACE} >/dev/null 2>&1; then
    echo "ERROR: Namespace '${NAMESPACE}' does not exist"
    echo "Please run './scripts/build-and-deploy.sh' first"
    exit 1
fi

# Wait for deployment to be ready
echo "Waiting for Search API deployment to be ready..."
kubectl rollout status deployment/search-api -n ${NAMESPACE} --timeout=300s

# Get pod information
echo "Pod information:"
kubectl get pods -n ${NAMESPACE}

# Get the service cluster IP
echo "Getting service cluster IP..."
SERVICE_IP=$(kubectl get service ${SERVICE_NAME} -n ${NAMESPACE} -o jsonpath='{.spec.clusterIP}')
echo "Service IP: ${SERVICE_IP}"

# Test health endpoint using port-forward
echo "Setting up port-forward for testing..."
kubectl port-forward -n ${NAMESPACE} service/${SERVICE_NAME} 8080:80 &
PORT_FORWARD_PID=$!

# Wait for port-forward to be ready
echo "Waiting for port-forward to be ready..."
sleep 5

# Test functions
test_health_endpoint() {
    echo "Testing health endpoint..."
    local response
    if response=$(curl -sf http://localhost:8080/health 2u003eu00261); then
        echo "✓ Health check passed"
        echo "Response: $response"
        return 0
    else
        echo "✗ Health check failed"
        echo "Error: $response"
        return 1
    fi
}

test_root_endpoint() {
    echo "Testing root endpoint..."
    local response
    if response=$(curl -sf http://localhost:8080/ 2u003eu00261); then
        echo "✓ Root endpoint test passed"
        echo "Response: $response"
        return 0
    else
        echo "✗ Root endpoint test failed"
        echo "Error: $response"
        return 1
    fi
}

test_debug_settings_endpoint() {
    echo "Testing debug settings endpoint..."
    local response
    if response=$(curl -sf http://localhost:8080/debug/settings 2u003eu00261); then
        echo "✓ Debug settings endpoint test passed"
        echo "Response: $response"
        return 0
    else
        echo "✗ Debug settings endpoint test failed"
        echo "Error: $response"
        return 1
    fi
}

# Run tests
echo ""
echo "=== Running Integration Tests ==="

HEALTH_STATUS="FAIL"
ROOT_STATUS="FAIL"
DEBUG_STATUS="FAIL"

if test_health_endpoint; then
    HEALTH_STATUS="PASS"
fi

if test_root_endpoint; then
    ROOT_STATUS="PASS"
fi

if test_debug_settings_endpoint; then
    DEBUG_STATUS="PASS"
fi

# Display results
echo ""
echo "=== Test Results ==="
echo "Health endpoint: $HEALTH_STATUS"
echo "Root endpoint: $ROOT_STATUS"
echo "Debug settings endpoint: $DEBUG_STATUS"

# Additional cluster information
echo ""
echo "=== Cluster Information ==="
echo "Cluster context: kind-${CLUSTER_NAME}"
echo "Namespace: ${NAMESPACE}"
echo "Service: ${SERVICE_NAME}"
echo "Service IP: ${SERVICE_IP}"

# Display resource usage
echo ""
echo "=== Resource Usage ==="
kubectl top pods -n ${NAMESPACE} 2u003e/dev/null || echo "Metrics not available"

# Check overall status
FAILED_TESTS=0
[ "$HEALTH_STATUS" = "FAIL" ] u0026u0026 ((FAILED_TESTS++))
[ "$ROOT_STATUS" = "FAIL" ] u0026u0026 ((FAILED_TESTS++))
[ "$DEBUG_STATUS" = "FAIL" ] u0026u0026 ((FAILED_TESTS++))

echo ""
if [ $FAILED_TESTS -eq 0 ]; then
    echo "✓ All tests passed! Search API is working correctly."
    exit 0
else
    echo "✗ $FAILED_TESTS test(s) failed!"
    exit 1
fi

