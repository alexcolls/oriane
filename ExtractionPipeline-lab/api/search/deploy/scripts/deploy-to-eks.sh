#!/bin/bash

# =============================================================================
# EKS Deployment Script for Search API
# =============================================================================
# This script deploys the search API to an existing EKS cluster
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLUSTER_NAME="gpu-test-cluster"
NAMESPACE="search-api"
SERVICE_NAME="search-api-service"
ECR_REPOSITORY="search-api"
AWS_REGION="us-west-2"

echo "=== EKS Deployment for Search API ==="
echo "Cluster: $CLUSTER_NAME"
echo "Namespace: $NAMESPACE"
echo "Region: $AWS_REGION"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
if ! command_exists aws; then
    echo "ERROR: AWS CLI is not installed"
    exit 1
fi

if ! command_exists kubectl; then
    echo "ERROR: kubectl is not installed"
    exit 1
fi

if ! command_exists docker; then
    echo "ERROR: Docker is not installed"
    exit 1
fi

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "ERROR: AWS credentials are not configured"
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "ECR URI: $ECR_URI"

# Update kubeconfig for EKS
echo "Updating kubeconfig for EKS cluster..."
aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"

# Check if cluster is accessible
echo "Checking cluster access..."
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "ERROR: Cannot access EKS cluster"
    exit 1
fi

# Create namespace if it doesn't exist
echo "Creating namespace..."
kubectl create namespace "$NAMESPACE" || echo "Namespace already exists"

# Create ECR repository if it doesn't exist
echo "Creating ECR repository..."
aws ecr create-repository --repository-name "$ECR_REPOSITORY" --region "$AWS_REGION" 2>/dev/null || echo "Repository already exists"

# Build and tag Docker image
echo "Building Docker image..."
cd "$PROJECT_ROOT"
docker build -f Dockerfile -t "$ECR_REPOSITORY:latest" .

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URI"

# Tag and push image to ECR
echo "Tagging and pushing image to ECR..."
docker tag "$ECR_REPOSITORY:latest" "$ECR_URI/$ECR_REPOSITORY:latest"
docker push "$ECR_URI/$ECR_REPOSITORY:latest"

# Create EKS-specific deployment with GPU support
echo "Creating EKS deployment manifest..."
cat > k8s/deployment-eks.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-api
  namespace: $NAMESPACE
  labels:
    app: search-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: search-api
  template:
    metadata:
      labels:
        app: search-api
    spec:
      containers:
      - name: search-api
        image: $ECR_URI/$ECR_REPOSITORY:latest
        imagePullPolicy: Always
        resources:
          requests:
            memory: "4Gi"
            cpu: "2000m"
            nvidia.com/gpu: 1
          limits:
            memory: "16Gi"
            cpu: "8000m"
            nvidia.com/gpu: 1
        env:
        - name: PYTHONPATH
          value: "/app:/app/api:/app/core/py/pipeline"
        - name: PYTHONUNBUFFERED
          value: "1"
        - name: NVIDIA_VISIBLE_DEVICES
          value: "all"
        - name: NVIDIA_DRIVER_CAPABILITIES
          value: "compute,utility,video"
        envFrom:
        - configMapRef:
            name: search-api-config
        - secretRef:
            name: search-api-secrets
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 120
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: temp-storage
          mountPath: /app/temp
        - name: output-storage
          mountPath: /app/output
        - name: logs-storage
          mountPath: /app/logs
        - name: models-storage
          mountPath: /app/models
      volumes:
      - name: temp-storage
        emptyDir:
          sizeLimit: 10Gi
      - name: output-storage
        emptyDir:
          sizeLimit: 5Gi
      - name: logs-storage
        emptyDir:
          sizeLimit: 2Gi
      - name: models-storage
        emptyDir:
          sizeLimit: 20Gi
      nodeSelector:
        kubernetes.io/arch: amd64
        # node.kubernetes.io/instance-type: g4dn.xlarge  # Uncomment for GPU nodes
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      restartPolicy: Always
      terminationGracePeriodSeconds: 60
EOF

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment-eks.yaml
kubectl apply -f k8s/service.yaml

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl rollout status deployment/search-api -n "$NAMESPACE" --timeout=600s

# Display deployment status
echo ""
echo "=== Deployment Status ==="
kubectl get all -n "$NAMESPACE"

# Get service information
echo ""
echo "=== Service Information ==="
kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o wide

# Display logs
echo ""
echo "=== Recent Logs ==="
kubectl logs -n "$NAMESPACE" deployment/search-api --tail=20

echo ""
echo "✓ EKS deployment complete!"
echo "Search API is deployed to EKS cluster: $CLUSTER_NAME"
echo "Namespace: $NAMESPACE"
echo ""
echo "To access the API:"
echo "  kubectl port-forward -n $NAMESPACE service/$SERVICE_NAME 8080:80"
echo "  curl http://localhost:8080/health"
