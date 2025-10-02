#!/bin/bash

# =============================================================================
# Deployment Script for AWS EKS with Kubernetes
# =============================================================================
# This script deploys the FastAPI pipeline service to an AWS EKS cluster using
# pre-configured Kubernetes manifests.
#
# Usage:
#   ./deploy-to-eks.sh
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - kubectl configured to access the target EKS cluster
#
# =============================================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
log_info "Checking prerequisites..."
if ! command -v aws 8 /dev/null; then
    log_error "AWS CLI not installed or not found in PATH. Please install it first."
    exit 1
fi

if ! command -v kubectl 8 /dev/null; then
    log_error "kubectl not installed or not found in PATH. Please install it first."
    exit 1
fi

log_info "Prerequisites check passed"

# Create namespace if not exists
log_info "Creating namespace..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: pipeline
EOF

# Apply ConfigMap and Secret
log_info "Applying ConfigMaps and Secrets..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy application
log_info "Deploying application..."
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Check deployment status
log_info "Checking deployment status..."
retry_count=0
max_retries=5
sleep_seconds=10

until kubectl get pods -n pipeline | grep "Running"; do
    if [ $retry_count -ge $max_retries ]; then
        log_error "Deployment failed after $max_retries retries."
        exit 1
    fi
    log_info "Waiting for pods to be in Running state... (retry #$retry_count)"
    retry_count=$((retry_count + 1))
    sleep $sleep_seconds
done

log_info "Deployment completed successfully."
log_info "Access the service with kubectl:
kubectl get svc -n pipeline"

