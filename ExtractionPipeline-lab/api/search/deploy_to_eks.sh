#!/bin/bash

# =============================================================================
# Comprehensive Deployment Script for Oriane Search API to AWS EKS
# =============================================================================
# This script sets up an EKS cluster, configures node groups, and deploys 
# the Oriane Search API with scalable CPU and GPU support.
# =============================================================================

set -euo pipefail

# --- Configuration ---

CLUSTER_NAME="oriane-search-api-cluster"
AWS_REGION="us-east-1"
NODE_ROLE_NAME="AmazonEKSAutoNodeRole"
GPU_NODE_GROUP_NAME="oriane-search-worker-gpu-node"
CPU_NODE_GROUP_NAME="oriane-search-api-cpu-node"
IMAGE_NAME="oriane-search-api"
K8S_NAMESPACE="oriane-search-api"
TOROLERATIONS_KEY="node-type"

# Load environment variables from .env
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found. Please create one with the required configuration." >&2
    exit 1
fi
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# --- Functions ---

create_eks_cluster() {
    log "Creating EKS Cluster if not exists..."
    if ! eksctl get cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" 2>/dev/null; then
        # Use existing VPC to avoid hitting VPC limits
        EXISTING_VPC="vpc-0c3ab41805ec7bf44"
        
        # Get subnets for the existing VPC (excluding us-east-1e)
        SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$EXISTING_VPC" --query 'Subnets[?AvailabilityZone!=`us-east-1e`].SubnetId' --output text | tr '\t' ',')
        
        log "Using existing VPC: $EXISTING_VPC"
        log "Using subnets: $SUBNETS"
        
        eksctl create cluster \
            --name "$CLUSTER_NAME" \
            --region "$AWS_REGION" \
            --vpc-public-subnets "$SUBNETS" \
            --nodes 1 \
            --managed \
            --version 1.33
        success "EKS Cluster '$CLUSTER_NAME' created"
    else
        success "EKS Cluster '$CLUSTER_NAME' already exists"
    fi
}

create_node_groups() {
    # Check if CPU node group exists
    if ! eksctl get nodegroup --cluster "$CLUSTER_NAME" --name "$CPU_NODE_GROUP_NAME" --region "$AWS_REGION" 2>/dev/null; then
        log "Creating CPU node group..."
        eksctl create nodegroup \
            --cluster "$CLUSTER_NAME" \
            --name "$CPU_NODE_GROUP_NAME" \
            --node-type t3.large \
            --nodes 3 \
            --nodes-min 2 \
            --nodes-max 5 \
            --node-volume-size 50
        success "CPU node group '$CPU_NODE_GROUP_NAME' created"
    else
        success "CPU node group '$CPU_NODE_GROUP_NAME' already exists"
    fi

    # Check if GPU node group exists
    if ! eksctl get nodegroup --cluster "$CLUSTER_NAME" --name "$GPU_NODE_GROUP_NAME" --region "$AWS_REGION" 2>/dev/null; then
        log "Creating GPU node group..."
        eksctl create nodegroup \
            --cluster "$CLUSTER_NAME" \
            --name "$GPU_NODE_GROUP_NAME" \
            --node-type g4dn.large \
            --nodes 1 \
            --nodes-min 1 \
            --nodes-max 2 \
            --node-volume-size 150
        success "GPU node group '$GPU_NODE_GROUP_NAME' created"
    else
        success "GPU node group '$GPU_NODE_GROUP_NAME' already exists"
    fi
}

build_and_push_image() {
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    
    # Create image tag with version and timestamp
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    IMAGE_TAG="${API_VERSION}-${TIMESTAMP}"
    ECR_IMAGE_URI="${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    log "Building and pushing Docker image with tag: $IMAGE_TAG"
    docker build -t "$IMAGE_NAME:$IMAGE_TAG" -f deploy/docker/Dockerfile . --target prod
    aws ecr create-repository --repository-name $IMAGE_NAME --region "$AWS_REGION" || true
    docker tag "$IMAGE_NAME:$IMAGE_TAG" "$ECR_IMAGE_URI"
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
    docker push "$ECR_IMAGE_URI"
    success "Image pushed to ECR: $ECR_IMAGE_URI"
}

update_and_apply_manifests() {
    # Create namespace if it doesn't exist
    kubectl create namespace "$K8S_NAMESPACE" || true
    
    # Create ConfigMap and Secrets
    log "Creating ConfigMap and Secrets..."
    kubectl create configmap "${IMAGE_NAME}-config" --from-env-file=.env -n "$K8S_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    kubectl create secret generic "${IMAGE_NAME}-secrets" \
        --from-literal=DB_PASSWORD="${DB_PASSWORD}" \
        --from-literal=API_KEY="${API_KEY}" \
        --from-literal=QDRANT_KEY="${QDRANT_KEY}" \
        -n "$K8S_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Update image in deployment files
    sed -i "s|image:.*|image: $ECR_IMAGE_URI|g" deploy/kubernetes/deployment-cpu.yaml
    sed -i "s|image:.*|image: $ECR_IMAGE_URI|g" deploy/kubernetes/deployment-gpu.yaml

    log "Applying Kubernetes manifests..."
    kubectl apply -f "deploy/kubernetes/deployment-cpu.yaml"
    kubectl apply -f "deploy/kubernetes/deployment-gpu.yaml"
    kubectl apply -f "deploy/kubernetes/service.yaml" || true
    kubectl apply -f "deploy/kubernetes/hpa.yaml" || true
    success "Kubernetes deployments applied"
}

deploy_status() {
    log "Checking deployment status..."
    kubectl get deployments -n "$K8S_NAMESPACE"
    kubectl rollout status deployment/oriane-search-api -n "$K8S_NAMESPACE"
    kubectl rollout status deployment/oriane-search-worker -n "$K8S_NAMESPACE"
    success "Deployments are ready and running"
}

# --- Main Execution ---

main() {
    create_eks_cluster
    create_node_groups
    build_and_push_image
    update_and_apply_manifests
    deploy_status
    
    log "Deployment to EKS cluster '$CLUSTER_NAME' is complete!"
}

main "$@"

