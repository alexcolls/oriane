#!/bin/bash

# Get the script directory and project root
SCRIPT_DIR="$(dirname "$(realpath "$0")")" 
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")" 

# Vars
DOCKER_IMAGE="pipeline-api:latest"
K8S_NAMESPACE="pipeline"

# Build Docker Image
echo "Building Docker Image..."
docker build -t $DOCKER_IMAGE -f "$PROJECT_ROOT/deploy/docker/Dockerfile" "$PROJECT_ROOT"

# Run Docker Container
echo "Running Docker Container..."
docker run -d --rm --name pipeline-api-test -p 8000:8000 $DOCKER_IMAGE

# Verify Local Health
echo "Checking Local Health..."
curl -sf http://localhost:8000/health || { echo "Health check failed!"; exit 1; }

# Cleanup Docker
echo "Stopping Docker Container..."
docker stop pipeline-api-test

# Deploy to Kubernetes
echo "Deploying to Kubernetes..."
kubectl apply -f "$PROJECT_ROOT/deploy/kubernetes/configmap.yaml" -n $K8S_NAMESPACE
kubectl apply -f "$PROJECT_ROOT/deploy/kubernetes/secret.yaml" -n $K8S_NAMESPACE
kubectl apply -f "$PROJECT_ROOT/deploy/kubernetes/deployment.yaml" -n $K8S_NAMESPACE
kubectl apply -f "$PROJECT_ROOT/deploy/kubernetes/service.yaml" -n $K8S_NAMESPACE

# Wait for Deployment
echo "Waiting for Deployment..."
kubectl rollout status deployment/pipeline-api -n $K8S_NAMESPACE

# Verify Kubernetes Service
echo "Checking Kubernetes Health..."
K8S_URL=$(kubectl get service pipeline-api-service -n $K8S_NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -sf http://$K8S_URL/health || { echo "Kubernetes health check failed!"; exit 1; }

echo "All tests passed."

