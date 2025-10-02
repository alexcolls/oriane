#!/bin/bash


# =============================================================================
# AWS Load Balancer Controller Installation and Ingress Setup Script
# =============================================================================
# This script installs the AWS Load Balancer Controller and applies the 
# ingress configuration to expose the FastAPI docs at the specified domain.
# =============================================================================

set -euo pipefail

# Load environment variables
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] .env file not found. Please create one with the required configuration."
    exit 1
fi

source "$ENV_FILE"

# Set default values
CLUSTER_NAME="${CLUSTER_NAME:-oriane-pipeline-api-cluster}"
AWS_REGION="${AWS_REGION:-us-east-1}"
K8S_NAMESPACE="${K8S_NAMESPACE:-oriane-pipeline-api}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

# Check if AWS Load Balancer Controller is installed
check_alb_controller() {
    log "Checking AWS Load Balancer Controller..."
    if kubectl get deployment -n kube-system aws-load-balancer-controller >/dev/null 2>&1; then
        success "AWS Load Balancer Controller is already installed"
        return 0
    else
        log "AWS Load Balancer Controller not found. Installing..."
        return 1
    fi
}

# Install AWS Load Balancer Controller
install_alb_controller() {
    log "Installing AWS Load Balancer Controller..."
    
    # Get AWS Account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # Download IAM policy
    log "Downloading IAM policy..."
    curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json
    
    # Create IAM policy
    log "Creating IAM policy..."
    aws iam create-policy \
        --policy-name AWSLoadBalancerControllerIAMPolicy \
        --policy-document file://iam_policy.json \
        --region "$AWS_REGION" 2>/dev/null || true
    
    # Create IAM role and service account
    log "Creating IAM role and service account..."
    eksctl create iamserviceaccount \
        --cluster="$CLUSTER_NAME" \
        --namespace=kube-system \
        --name=aws-load-balancer-controller \
        --role-name AmazonEKSLoadBalancerControllerRole \
        --attach-policy-arn=arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
        --approve \
        --region "$AWS_REGION" || true
    
    # Install AWS Load Balancer Controller using Helm
    log "Installing AWS Load Balancer Controller using Helm..."
    
    # Add EKS Helm repository
    helm repo add eks https://aws.github.io/eks-charts
    helm repo update
    
    # Install AWS Load Balancer Controller
    helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName="$CLUSTER_NAME" \
        --set serviceAccount.create=false \
        --set serviceAccount.name=aws-load-balancer-controller \
        --set region="$AWS_REGION" \
        --set vpcId=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" --query 'cluster.resourcesVpcConfig.vpcId' --output text) || true
    
    # Wait for deployment to be ready
    log "Waiting for AWS Load Balancer Controller to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/aws-load-balancer-controller -n kube-system
    
    success "AWS Load Balancer Controller installed successfully"
    
    # Clean up
    rm -f iam_policy.json
}

# Apply ingress configuration
apply_ingress() {
    log "Applying ingress configuration..."
    
    # Apply the ingress
    kubectl apply -f "$SCRIPT_DIR/deploy/kubernetes/ingress.yaml"
    
    # Wait for ingress to be ready
    log "Waiting for ingress to be ready..."
    sleep 30
    
    # Get ingress address
    INGRESS_ADDRESS=""
    for i in {1..30}; do
        INGRESS_ADDRESS=$(kubectl get ingress oriane-pipeline-api-ingress -n "$K8S_NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
        if [[ -n "$INGRESS_ADDRESS" ]]; then
            break
        fi
        log "Waiting for ingress address... (attempt $i/30)"
        sleep 10
    done
    
    if [[ -n "$INGRESS_ADDRESS" ]]; then
        success "Ingress is ready!"
        echo ""
        echo "=== FastAPI Access URLs ==="
        echo "API Docs: https://pipeline.api.qdrant.admin.oriane.xyz/docs"
        echo "OpenAPI JSON: https://pipeline.api.qdrant.admin.oriane.xyz/openapi.json"
        echo "Load Balancer Address: $INGRESS_ADDRESS"
        echo ""
        echo "Note: Make sure your DNS is pointing pipeline.api.qdrant.admin.oriane.xyz to $INGRESS_ADDRESS"
    else
        error "Ingress address not available after 5 minutes. Check ingress status: kubectl get ingress -n $K8S_NAMESPACE"
    fi
}

# Main execution
main() {
    log "Setting up AWS Load Balancer Controller and Ingress..."
    
    if ! check_alb_controller; then
        install_alb_controller
    fi
    
    apply_ingress
    
    success "Setup complete!"
}

main "$@"
