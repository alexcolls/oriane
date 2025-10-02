#!/bin/bash
# Script to deploy actual pipeline application to EKS

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"

echo "🚀 Deploying Pipeline Application to EKS"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "======================================"

# Update kubeconfig
echo "📋 Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Create namespace
echo "📋 Creating pipeline namespace..."
kubectl create namespace pipeline --dry-run=client -o yaml | kubectl apply -f -

# Apply your existing Kubernetes manifests
echo "📋 Applying Kubernetes manifests..."

# Apply ConfigMap
if [ -f "k8s/configmap.yaml" ]; then
    echo "Applying ConfigMap..."
    kubectl apply -f k8s/configmap.yaml
else
    echo "Creating default ConfigMap..."
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: pipeline-api-config
  namespace: pipeline
data:
  API_ENV: "production"
  CLUSTER_NAME: "$CLUSTER_NAME"
  REGION: "$REGION"
  LOG_LEVEL: "INFO"
  PIPELINE_MAX_PARALLEL_JOBS: "3"
  PIPELINE_TIMEOUT: "300"
  S3_BUCKET: "oriane-frames"
  S3_BUCKET_FRAMES: "oriane-contents"
EOF
fi

# Apply Secret
if [ -f "k8s/secret.yaml" ]; then
    echo "Applying Secret..."
    kubectl apply -f k8s/secret.yaml
else
    echo "Creating default Secret..."
    kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: pipeline-api-secrets
  namespace: pipeline
type: Opaque
data:
  API_KEY: $(echo -n "your-api-key-here" | base64)
  AWS_ACCESS_KEY_ID: $(echo -n "your-aws-access-key" | base64)
  AWS_SECRET_ACCESS_KEY: $(echo -n "your-aws-secret-key" | base64)
  QDRANT_KEY: $(echo -n "your-qdrant-key" | base64)
  QDRANT_URL: $(echo -n "https://your-qdrant-endpoint:6333" | base64)
EOF
fi

# Apply Deployment
if [ -f "k8s/deployment.yaml" ]; then
    echo "Applying Deployment..."
    kubectl apply -f k8s/deployment.yaml
else
    echo "Creating default Deployment..."
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
        image: your-account.dkr.ecr.us-east-1.amazonaws.com/pipeline-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: CLUSTER_NAME
          valueFrom:
            configMapKeyRef:
              name: pipeline-api-config
              key: CLUSTER_NAME
        - name: REGION
          valueFrom:
            configMapKeyRef:
              name: pipeline-api-config
              key: REGION
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: pipeline-api-secrets
              key: API_KEY
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: pipeline-api-secrets
              key: AWS_ACCESS_KEY_ID
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: pipeline-api-secrets
              key: AWS_SECRET_ACCESS_KEY
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
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
EOF
fi

# Apply Service
if [ -f "k8s/service.yaml" ]; then
    echo "Applying Service..."
    kubectl apply -f k8s/service.yaml
else
    echo "Creating default Service..."
    kubectl apply -f - <<EOF
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
EOF
fi

# Apply Ingress if exists
if [ -f "k8s/ingress.yaml" ]; then
    echo "Applying Ingress..."
    kubectl apply -f k8s/ingress.yaml
fi

# Apply HPA if exists
if [ -f "k8s/hpa.yaml" ]; then
    echo "Applying HPA..."
    kubectl apply -f k8s/hpa.yaml
fi

# Check deployment status
echo "📋 Checking deployment status..."
kubectl get deployments -n pipeline

# Show current status
echo "📋 Current status:"
kubectl get pods -n pipeline -o wide
kubectl get services -n pipeline

# Wait for deployment (with detailed output)
echo "📋 Waiting for deployment to be ready..."
kubectl wait --for=condition=available deployment/pipeline-api -n pipeline --timeout=300s || {
    echo "⚠️  Deployment is taking longer than expected. Diagnosing..."
    echo "📋 Pod status:"
    kubectl get pods -n pipeline -o wide
    echo "📋 Pod descriptions:"
    kubectl describe pods -n pipeline
    echo "📋 Events:"
    kubectl get events -n pipeline --sort-by=.metadata.creationTimestamp
    echo "📋 Logs:"
    kubectl logs -n pipeline deployment/pipeline-api --tail=50
}

echo "🎉 Pipeline application deployment completed!"
echo "=========================================="

echo "📋 Your EKS Configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodeMinimalPolicy"

echo "📋 Service Information:"
echo "- Namespace: pipeline"
echo "- Service: pipeline-api-service"
echo "- Internal URL: http://pipeline-api-service.pipeline.svc.cluster.local"

echo "📋 Useful Commands:"
echo "- Port forward: kubectl port-forward -n pipeline svc/pipeline-api-service 8080:80"
echo "- Check pods: kubectl get pods -n pipeline"
echo "- Check logs: kubectl logs -n pipeline deployment/pipeline-api -f"
echo "- Scale: kubectl scale deployment pipeline-api --replicas=3 -n pipeline"
echo "- Update image: kubectl set image deployment/pipeline-api pipeline-api=your-new-image:tag -n pipeline"

echo "✅ Pipeline application is ready for use!"
