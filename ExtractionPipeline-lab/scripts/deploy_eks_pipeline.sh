#!/bin/bash
# Main deployment script for EKS pipeline service

set -e

echo "🚀 EKS Pipeline Deployment Script"
echo "=================================="

# Configuration
CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
NAMESPACE="pipeline"

echo "📋 Configuration:"
echo "- Cluster: $CLUSTER_NAME"
echo "- Region: $REGION"
echo "- Namespace: $NAMESPACE"
echo ""

# Check if cluster exists
echo "📋 Checking cluster status..."
if aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "✅ Cluster exists and is accessible"
else
    echo "❌ Cluster not found or not accessible"
    exit 1
fi

# Update kubeconfig
echo "📋 Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Check cluster connectivity
echo "📋 Testing cluster connectivity..."
if kubectl cluster-info >/dev/null 2>&1; then
    echo "✅ Cluster is accessible via kubectl"
else
    echo "❌ Cannot connect to cluster"
    exit 1
fi

# Create namespace
echo "📋 Creating namespace..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Deploy pipeline service
echo "📋 Deploying pipeline service..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: pipeline-config
  namespace: $NAMESPACE
data:
  CLUSTER_NAME: "$CLUSTER_NAME"
  REGION: "$REGION"
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  API_PORT: "8000"
  HEALTH_CHECK_PATH: "/health"
  METRICS_PATH: "/metrics"
  S3_BUCKET_VIDEOS: "oriane-videos"
  S3_BUCKET_FRAMES: "oriane-frames"
  PIPELINE_TIMEOUT: "300"
  MAX_PARALLEL_JOBS: "3"
---
apiVersion: v1
kind: Secret
metadata:
  name: pipeline-secrets
  namespace: $NAMESPACE
type: Opaque
stringData:
  API_KEY: "your-api-key-here"
  DATABASE_URL: "your-database-url"
  AWS_ACCESS_KEY_ID: "your-aws-access-key"
  AWS_SECRET_ACCESS_KEY: "your-aws-secret-key"
  QDRANT_URL: "https://your-qdrant-endpoint:6333"
  QDRANT_API_KEY: "your-qdrant-api-key"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pipeline-api
  namespace: $NAMESPACE
  labels:
    app: pipeline-api
    version: "1.0"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pipeline-api
  template:
    metadata:
      labels:
        app: pipeline-api
        version: "1.0"
    spec:
      containers:
      - name: pipeline-api
        image: nginx:alpine  # Replace with your actual image
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: metrics
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: CLUSTER_NAME
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: CLUSTER_NAME
        - name: REGION
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: REGION
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: pipeline-config
              key: LOG_LEVEL
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: pipeline-secrets
              key: API_KEY
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: pipeline-secrets
              key: DATABASE_URL
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: pipeline-secrets
              key: AWS_ACCESS_KEY_ID
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: pipeline-secrets
              key: AWS_SECRET_ACCESS_KEY
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
---
apiVersion: v1
kind: Service
metadata:
  name: pipeline-api-service
  namespace: $NAMESPACE
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
  - name: metrics
    port: 9090
    targetPort: 9090
    protocol: TCP
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: pipeline-api-network-policy
  namespace: $NAMESPACE
spec:
  podSelector:
    matchLabels:
      app: pipeline-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 8000
    - protocol: TCP
      port: 9090
  egress:
  - {}
EOF

echo "✅ Pipeline service deployed successfully!"

# Check deployment status
echo "📋 Checking deployment status..."
kubectl get deployments -n "$NAMESPACE"
kubectl get services -n "$NAMESPACE"
kubectl get pods -n "$NAMESPACE"

# Wait for deployment to be ready
echo "📋 Waiting for deployment to be ready..."
kubectl wait --for=condition=available deployment/pipeline-api -n "$NAMESPACE" --timeout=300s || {
    echo "⚠️  Deployment is taking longer than expected"
    echo "📋 Current status:"
    kubectl get pods -n "$NAMESPACE" -o wide
    echo "📋 Events:"
    kubectl get events -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp
    echo "📋 Pod logs:"
    kubectl logs -n "$NAMESPACE" deployment/pipeline-api --tail=50
}

echo "🎉 EKS Pipeline deployment completed!"
echo "====================================="

echo "📋 Your EKS Configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodeMinimalPolicy"

echo "📋 Service Information:"
echo "- Namespace: $NAMESPACE"
echo "- Service: pipeline-api-service"
echo "- Internal URL: http://pipeline-api-service.$NAMESPACE.svc.cluster.local"
echo "- Metrics URL: http://pipeline-api-service.$NAMESPACE.svc.cluster.local:9090/metrics"

echo "📋 Useful Commands:"
echo "- Port forward API: kubectl port-forward -n $NAMESPACE svc/pipeline-api-service 8080:80"
echo "- Port forward metrics: kubectl port-forward -n $NAMESPACE svc/pipeline-api-service 9090:9090"
echo "- Check pods: kubectl get pods -n $NAMESPACE"
echo "- Check logs: kubectl logs -n $NAMESPACE deployment/pipeline-api -f"
echo "- Scale up: kubectl scale deployment pipeline-api --replicas=3 -n $NAMESPACE"
echo "- Update config: kubectl edit configmap pipeline-config -n $NAMESPACE"
echo "- Delete all: kubectl delete namespace $NAMESPACE"

echo "📋 Next steps:"
echo "1. Update the Docker image in the deployment with your actual pipeline image"
echo "2. Update the secrets with your actual API keys and credentials"
echo "3. Test the service: kubectl port-forward -n $NAMESPACE svc/pipeline-api-service 8080:80"
echo "4. Monitor: ./monitor_eks_deployment.sh"

echo "✅ EKS Pipeline is ready for use!"
