#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if ECR_URI is set
if [ -z "$ECR_URI" ]; then
    print_error "ECR_URI environment variable is not set"
    exit 1
fi

# Check if required files exist
if [ ! -f "Dockerfile" ]; then
    print_error "Dockerfile not found in current directory"
    exit 1
fi

if [ ! -f "deployment.yaml" ]; then
    print_error "deployment.yaml not found in current directory"
    exit 1
fi

# Build and push Docker image
print_status "Building and pushing Docker image to ECR..."
docker buildx build --platform=linux/amd64 --push -t $ECR_URI/pipeline-api:latest .

if [ $? -eq 0 ]; then
    print_status "Docker image built and pushed successfully"
else
    print_error "Failed to build and push Docker image"
    exit 1
fi

# Apply Kubernetes deployment
print_status "Applying Kubernetes deployment..."
kubectl apply -f deployment.yaml

if [ $? -eq 0 ]; then
    print_status "Kubernetes deployment applied successfully"
else
    print_error "Failed to apply Kubernetes deployment"
    exit 1
fi

# Verify rollout status
print_status "Verifying rollout status..."
kubectl rollout status deployment/pipeline-api

if [ $? -eq 0 ]; then
    print_status "Deployment rollout completed successfully"
else
    print_error "Deployment rollout failed"
    exit 1
fi

print_status "Deployment completed successfully!"
