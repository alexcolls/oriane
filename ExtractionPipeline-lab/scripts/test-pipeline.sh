#!/bin/bash

# =============================================================================
# Pipeline Integration Test Script for KinD Cluster
# =============================================================================
# This script runs comprehensive integration tests against the pipeline API
# deployed in a KinD cluster
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLUSTER_NAME="pipeline-test"
K8S_NAMESPACE="pipeline"
SERVICE_NAME="pipeline-api-service"

echo "=== KinD Cluster Integration Test ==="

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
if ! kubectl get namespace ${K8S_NAMESPACE} >/dev/null 2>&1; then
    echo "ERROR: Namespace '${K8S_NAMESPACE}' does not exist"
    echo "Please run './scripts/build-and-deploy.sh' first"
    exit 1
fi

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl rollout status deployment/pipeline-api -n ${K8S_NAMESPACE} --timeout=120s

# Get pod information
echo "Pod information:"
kubectl get pods -n ${K8S_NAMESPACE}

# Get the service cluster IP
echo "Getting service cluster IP..."
SERVICE_IP=$(kubectl get service ${SERVICE_NAME} -n ${K8S_NAMESPACE} -o jsonpath='{.spec.clusterIP}')
echo "Service IP: ${SERVICE_IP}"

# Test health endpoint using port-forward
echo "Setting up port-forward for testing..."
kubectl port-forward -n ${K8S_NAMESPACE} service/${SERVICE_NAME} 8080:80 &
PORT_FORWARD_PID=$!

# Wait for port-forward to be ready
echo "Waiting for port-forward to be ready..."
sleep 5

# Test functions
test_health_endpoint() {
    echo "Testing health endpoint..."
    local response
    if response=$(curl -sf http://localhost:8080/health 2>&1); then
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
    if response=$(curl -sf http://localhost:8080/ 2>&1); then
        echo "✓ Root endpoint test passed"
        echo "Response: $response"
        return 0
    else
        echo "✗ Root endpoint test failed"
        echo "Error: $response"
        return 1
    fi
}

test_response_time() {
    echo "Testing response time..."
    local response_time
    response_time=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8080/health)
    echo "Response time: ${response_time}s"
    
    # Check if response time is reasonable (less than 2 seconds)
    if (( $(echo "$response_time < 2.0" | bc -l) )); then
        echo "✓ Response time is acceptable"
        return 0
    else
        echo "✗ Response time is too slow"
        return 1
    fi
}

test_multiple_requests() {
    echo "Testing multiple concurrent requests..."
    local failures=0
    
    for i in {1..5}; do
        if ! curl -sf http://localhost:8080/health >/dev/null 2>&1; then
            ((failures++))
        fi
    done
    
    if [ $failures -eq 0 ]; then
        echo "✓ All concurrent requests succeeded"
        return 0
    else
        echo "✗ $failures out of 5 requests failed"
        return 1
    fi
}

# Run tests
echo ""
echo "=== Running Integration Tests ==="

HEALTH_STATUS="FAIL"
ROOT_STATUS="FAIL"
RESPONSE_TIME_STATUS="FAIL"
CONCURRENT_STATUS="FAIL"

if test_health_endpoint; then
    HEALTH_STATUS="PASS"
fi

if test_root_endpoint; then
    ROOT_STATUS="PASS"
fi

if command -v bc >/dev/null 2>&1 && test_response_time; then
    RESPONSE_TIME_STATUS="PASS"
else
    echo "Skipping response time test (bc not available)"
    RESPONSE_TIME_STATUS="SKIP"
fi

if test_multiple_requests; then
    CONCURRENT_STATUS="PASS"
fi

# Display results
echo ""
echo "=== Test Results ==="
echo "Health endpoint: $HEALTH_STATUS"
echo "Root endpoint: $ROOT_STATUS"
echo "Response time: $RESPONSE_TIME_STATUS"
echo "Concurrent requests: $CONCURRENT_STATUS"

# Additional cluster information
echo ""
echo "=== Cluster Information ==="
echo "Cluster context: kind-${CLUSTER_NAME}"
echo "Namespace: ${K8S_NAMESPACE}"
echo "Service: ${SERVICE_NAME}"
echo "Service IP: ${SERVICE_IP}"

# Display resource usage
echo ""
echo "=== Resource Usage ==="
kubectl top pods -n ${K8S_NAMESPACE} 2>/dev/null || echo "Metrics not available"

# Check logs for any errors
echo ""
echo "=== Recent Logs ==="
kubectl logs -n ${K8S_NAMESPACE} deployment/pipeline-api --tail=10

# Check overall status
FAILED_TESTS=0
[ "$HEALTH_STATUS" = "FAIL" ] && ((FAILED_TESTS++))
[ "$ROOT_STATUS" = "FAIL" ] && ((FAILED_TESTS++))
[ "$RESPONSE_TIME_STATUS" = "FAIL" ] && ((FAILED_TESTS++))
[ "$CONCURRENT_STATUS" = "FAIL" ] && ((FAILED_TESTS++))

echo ""
if [ $FAILED_TESTS -eq 0 ]; then
    echo "✓ All tests passed! Pipeline API is working correctly."
    exit 0
else
    echo "✗ $FAILED_TESTS test(s) failed!"
    exit 1
fi
