#!/bin/bash

# =============================================================================
# Oriane Search API - Deployment Test Script
# =============================================================================
# This script performs basic API testing after deployment
# 
# Usage:
#   ./test-deployment.sh [OPTIONS]
#
# Options:
#   -n, --namespace NS      Kubernetes namespace (default: search)
#   -k, --api-key KEY       API key for testing (default: test-api-key)
#   -h, --help             Show this help message
#
# =============================================================================

set -euo pipefail

# Default values
K8S_NAMESPACE=${K8S_NAMESPACE:-"search"}
API_KEY=${API_KEY:-"test-api-key"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Oriane Search API - Deployment Test Script

Usage: $0 [OPTIONS]

Options:
  -n, --namespace NS      Kubernetes namespace (default: search)
  -k, --api-key KEY       API key for testing (default: test-api-key)
  -h, --help             Show this help message

Examples:
  $0
  $0 -n search-prod -k my-api-key
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            K8S_NAMESPACE="$2"
            shift 2
            ;;
        -k|--api-key)
            API_KEY="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Setup port forwarding
setup_port_forward() {
    log_info "Setting up port forwarding..."
    
    # Start port forward in background
    kubectl port-forward -n "$K8S_NAMESPACE" svc/search-api-service 8081:80 &
    PORT_FORWARD_PID=$!
    
    # Give it time to establish
    sleep 5
    
    # Test if port forward is working
    if ! curl -f -s http://localhost:8081/health > /dev/null; then
        log_error "Port forwarding failed to establish"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        return 1
    fi
    
    log_success "Port forwarding established (PID: $PORT_FORWARD_PID)"
}

# Cleanup port forwarding
cleanup_port_forward() {
    if [[ -n "${PORT_FORWARD_PID:-}" ]]; then
        log_info "Cleaning up port forwarding..."
        kill $PORT_FORWARD_PID 2>/dev/null || true
    fi
}

# Test health endpoint
test_health() {
    log_info "Testing health endpoint..."
    
    local response=$(curl -s http://localhost:8081/health)
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/health)
    
    if [[ "$status_code" == "200" ]]; then
        log_success "Health endpoint returned 200 OK"
        echo "Response: $response"
    else
        log_error "Health endpoint returned status code: $status_code"
        return 1
    fi
}

# Test root endpoint
test_root() {
    log_info "Testing root endpoint..."
    
    local response=$(curl -s http://localhost:8081/)
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/)
    
    if [[ "$status_code" == "200" ]]; then
        log_success "Root endpoint returned 200 OK"
        echo "Response: $response"
    else
        log_error "Root endpoint returned status code: $status_code"
        return 1
    fi
}

# Test debug settings endpoint
test_debug_settings() {
    log_info "Testing debug settings endpoint..."
    
    local response=$(curl -s "http://localhost:8081/debug/settings" -H "X-API-Key: $API_KEY")
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8081/debug/settings" -H "X-API-Key: $API_KEY")
    
    if [[ "$status_code" == "200" ]]; then
        log_success "Debug settings endpoint returned 200 OK"
        echo "Response: $response"
    else
        log_error "Debug settings endpoint returned status code: $status_code"
        return 1
    fi
}

# Test API authentication
test_auth() {
    log_info "Testing API authentication..."
    
    # Test without API key (should fail)
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8081/debug/settings")
    
    if [[ "$status_code" == "401" ]]; then
        log_success "Authentication properly rejected request without API key"
    else
        log_warning "Expected 401 for request without API key, got: $status_code"
    fi
    
    # Test with API key (should succeed)
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8081/debug/settings" -H "X-API-Key: $API_KEY")
    
    if [[ "$status_code" == "200" ]]; then
        log_success "Authentication properly accepted request with API key"
    else
        log_error "Authentication failed with API key, status code: $status_code"
        return 1
    fi
}

# Test API endpoints
test_endpoints() {
    log_info "Testing API endpoints availability..."
    
    # Test search endpoints (should return method not allowed or similar)
    local endpoints=(
        "/search-by/text"
        "/search-by/image"
        "/search-by-user-content"
        "/get-embeddings"
        "/add-content/image"
        "/add-content/video"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8081$endpoint" -H "X-API-Key: $API_KEY")
        
        if [[ "$status_code" == "405" ]] || [[ "$status_code" == "422" ]] || [[ "$status_code" == "404" ]]; then
            log_success "Endpoint $endpoint is available (status: $status_code)"
        else
            log_warning "Endpoint $endpoint returned unexpected status: $status_code"
        fi
    done
}

# Main test function
main() {
    log_info "Starting Oriane Search API deployment tests..."
    log_info "Namespace: $K8S_NAMESPACE"
    log_info "API Key: ${API_KEY:0:8}***"
    
    # Set up cleanup trap
    trap cleanup_port_forward EXIT
    
    local exit_code=0
    
    # Setup port forwarding
    setup_port_forward || exit_code=1
    
    if [[ $exit_code -eq 0 ]]; then
        # Run tests
        test_health || exit_code=1
        test_root || exit_code=1
        test_debug_settings || exit_code=1
        test_auth || exit_code=1
        test_endpoints || exit_code=1
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "All tests passed! The search API is working correctly."
        log_info "You can now use the API endpoints for search operations."
    else
        log_error "Some tests failed. Please check the deployment and configuration."
    fi
    
    return $exit_code
}

# Run main function
main "$@"
