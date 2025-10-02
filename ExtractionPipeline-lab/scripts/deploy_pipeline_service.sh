#!/bin/bash
# Script to deploy pipeline service using current EKS setup

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"

echo "🚀 Deploying Pipeline Service to EKS"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "=================================="

# Update kubeconfig
echo "📋 Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Create namespace
echo "📋 Creating pipeline namespace..."
kubectl create namespace pipeline --dry-run=client -o yaml | kubectl apply -f -

# Create pipeline service deployment
echo "📋 Creating pipeline service deployment..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pipeline-api
  namespace: pipeline
  labels:
    app: pipeline-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pipeline-api
  template:
    metadata:
      labels:
        app: pipeline-api
    spec:
      containers:
      - name: pipeline-api
        image: nginx:latest  # Replace with your actual pipeline image
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: CLUSTER_NAME
          value: "$CLUSTER_NAME"
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: pipeline-api-service
  namespace: pipeline
  labels:
    app: pipeline-api
spec:
  selector:
    app: pipeline-api
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: pipeline-config
  namespace: pipeline
data:
  API_ENV: "production"
  CLUSTER_NAME: "$CLUSTER_NAME"
  REGION: "$REGION"
  LOG_LEVEL: "INFO"
---
apiVersion: v1
kind: Secret
metadata:
  name: pipeline-secrets
  namespace: pipeline
type: Opaque
data:
  # Base64 encoded secrets - replace with actual values
  API_KEY: $(echo -n "your-api-key" | base64)
  DATABASE_URL: $(echo -n "your-database-url" | base64)
EOF

# Check deployment status
echo "📋 Checking deployment status..."
kubectl get deployments -n pipeline

# Wait for deployment (with timeout)
echo "📋 Waiting for deployment to be ready..."
kubectl wait --for=condition=available deployment/pipeline-api -n pipeline --timeout=300s || {
    echo "⚠️  Deployment is taking longer than expected. Current status:"
    kubectl get pods -n pipeline -o wide
    kubectl describe deployment pipeline-api -n pipeline
    echo "📋 Events:"
    kubectl get events -n pipeline --sort-by=.metadata.creationTimestamp
}

# Check pods
echo "📋 Checking pod status..."
kubectl get pods -n pipeline -o wide

# Check services
echo "📋 Checking services..."
kubectl get services -n pipeline

# Show cluster info
echo "📋 Cluster information:"
kubectl cluster-info

echo "🎉 Pipeline service deployment completed!"
echo "=================================="

echo "📋 Your EKS Configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"
echo "FARGATE_ROLE_NAME=AmazonEKSFargatePodExecutionRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodeMinimalPolicy"

echo "📋 Service URLs:"
echo "- Internal: http://pipeline-api-service.pipeline.svc.cluster.local"
echo "- Port Forward: kubectl port-forward -n pipeline svc/pipeline-api-service 8080:80"

echo "📋 Useful Commands:"
echo "- Check pods: kubectl get pods -n pipeline"
echo "- Check logs: kubectl logs -n pipeline deployment/pipeline-api"
echo "- Scale deployment: kubectl scale deployment pipeline-api --replicas=3 -n pipeline"
echo "- Delete deployment: kubectl delete namespace pipeline"

echo "✅ EKS Pipeline Service is ready!"
