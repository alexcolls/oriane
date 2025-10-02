#!/bin/bash

# =============================================================================
# Oriane Search API - Deployment Validation Script
# =============================================================================
# This script validates the deployment of the search API on EKS
# 
# Usage:
#   ./validate-deployment.sh [OPTIONS]
#
# Options:
#   -n, --namespace NS      Kubernetes namespace (default: search)
#   -h, --help             Show this help message
#
# =============================================================================

set -euo pipefail

# Default values
K8S_NAMESPACE=${K8S_NAMESPACE:-"search"}
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
Oriane Search API - Deployment Validation Script

Usage: $0 [OPTIONS]

Options:
  -n, --namespace NS      Kubernetes namespace (default: search)
  -h, --help             Show this help message

Examples:
  $0
  $0 -n search-prod
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            K8S_NAMESPACE="$2"
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

# Check if namespace exists
check_namespace() {
    log_info "Checking namespace '$K8S_NAMESPACE'..."
    
    if kubectl get namespace "$K8S_NAMESPACE" &> /dev/null; then
        log_success "Namespace '$K8S_NAMESPACE' exists"
    else
        log_error "Namespace '$K8S_NAMESPACE' does not exist"
        return 1
    fi
}

# Check deployment status
check_deployment() {
    log_info "Checking deployment status..."
    
    # Check if deployment exists
    if ! kubectl get deployment search-api -n "$K8S_NAMESPACE" &> /dev/null; then
        log_error "Deployment 'search-api' does not exist in namespace '$K8S_NAMESPACE'"
        return 1
    fi
    
    # Check deployment status
    local ready_replicas=$(kubectl get deployment search-api -n "$K8S_NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    local desired_replicas=$(kubectl get deployment search-api -n "$K8S_NAMESPACE" -o jsonpath='{.spec.replicas}')
    
    if [[ "$ready_replicas" == "$desired_replicas" ]]; then
        log_success "Deployment is ready ($ready_replicas/$desired_replicas replicas)"
    else
        log_warning "Deployment is not ready ($ready_replicas/$desired_replicas replicas)"
        return 1
    fi
}

# Check pod status
check_pods() {
    log_info "Checking pod status..."
    
    local pods=$(kubectl get pods -n "$K8S_NAMESPACE" -l app=search-api --no-headers)
    
    if [[ -z "$pods" ]]; then
        log_error "No pods found for search-api"
        return 1
    fi
    
    echo "$pods" | while read -r line; do
        local pod_name=$(echo "$line" | awk '{print $1}')
        local pod_status=$(echo "$line" | awk '{print $3}')
        
        if [[ "$pod_status" == "Running" ]]; then
            log_success "Pod $pod_name is running"
        else
            log_warning "Pod $pod_name is in status: $pod_status"
        fi
    done
}

# Check service status
check_service() {
    log_info "Checking service status..."
    
    if ! kubectl get service search-api-service -n "$K8S_NAMESPACE" &> /dev/null; then
        log_error "Service 'search-api-service' does not exist in namespace '$K8S_NAMESPACE'"
        return 1
    fi
    
    local service_type=$(kubectl get service search-api-service -n "$K8S_NAMESPACE" -o jsonpath='{.spec.type}')
    local cluster_ip=$(kubectl get service search-api-service -n "$K8S_NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    
    log_success "Service 'search-api-service' exists (type: $service_type, IP: $cluster_ip)"
}

# Check configmap
check_configmap() {
    log_info "Checking configmap..."
    
    if ! kubectl get configmap search-api-config -n "$K8S_NAMESPACE" &> /dev/null; then
        log_error "ConfigMap 'search-api-config' does not exist in namespace '$K8S_NAMESPACE'"
        return 1
    fi
    
    log_success "ConfigMap 'search-api-config' exists"
}

# Check secret
check_secret() {
    log_info "Checking secret..."
    
    if ! kubectl get secret search-api-secrets -n "$K8S_NAMESPACE" &> /dev/null; then
        log_error "Secret 'search-api-secrets' does not exist in namespace '$K8S_NAMESPACE'"
        return 1
    fi
    
    log_success "Secret 'search-api-secrets' exists"
}

# Test health endpoint
test_health_endpoint() {
    log_info "Testing health endpoint..."
    
    # Start port forward in background
    kubectl port-forward -n "$K8S_NAMESPACE" svc/search-api-service 8081:80 &
    PORT_FORWARD_PID=$!
    
    # Give it time to establish
    sleep 5
    
    # Test health endpoint
    if curl -f -s http://localhost:8081/health > /dev/null; then
        log_success "Health endpoint is responding"
        local health_response=$(curl -s http://localhost:8081/health)
        echo "Health response: $health_response"
    else
        log_error "Health endpoint is not responding"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        return 1
    fi
    
    # Clean up port forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
}

# Get deployment logs
get_deployment_logs() {
    log_info "Getting recent deployment logs..."
    
    local pods=$(kubectl get pods -n "$K8S_NAMESPACE" -l app=search-api --no-headers | awk '{print $1}')
    
    if [[ -n "$pods" ]]; then
        echo "$pods" | while read -r pod_name; do
            log_info "Logs for pod $pod_name:"
            kubectl logs -n "$K8S_NAMESPACE" "$pod_name" --tail=10 || true
            echo ""
        done
    else
        log_warning "No pods found to get logs from"
    fi
}

# Main validation function
main() {
    log_info "Starting Oriane Search API deployment validation..."
    log_info "Namespace: $K8S_NAMESPACE"
    
    local exit_code=0
    
    # Run all checks
    check_namespace || exit_code=1
    check_deployment || exit_code=1
    check_pods || exit_code=1
    check_service || exit_code=1
    check_configmap || exit_code=1
    check_secret || exit_code=1
    test_health_endpoint || exit_code=1
    
    # Always show logs for debugging
    get_deployment_logs
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "All validation checks passed!"
        log_info "The search API is successfully deployed and running."
        log_info "You can access it using:"
        log_info "  kubectl port-forward -n $K8S_NAMESPACE svc/search-api-service 8081:80"
        log_info "  curl http://localhost:8081/health"
    else
        log_error "Some validation checks failed. Please review the output above."
    fi
    
    return $exit_code
}

# Run main function
main "$@"
