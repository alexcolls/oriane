# Oriane Search API - EKS Deployment Guide

This document provides comprehensive instructions for deploying the Oriane Search API to Amazon EKS.

## Prerequisites

Before deploying the search API, ensure you have the following:

1. **AWS CLI** configured with appropriate permissions
2. **kubectl** installed and configured
3. **Docker** installed and running
4. **Amazon EKS cluster** already created
5. **ECR repository** access (will be created automatically if needed)

## Quick Start

For a quick deployment with default settings:

```bash
# Set required environment variables
export AWS_ACCOUNT_ID="YOUR_AWS_ACCOUNT_ID"
export EKS_CLUSTER_NAME="YOUR_EKS_CLUSTER_NAME"

# Deploy the search API
./deploy-eks.sh -a $AWS_ACCOUNT_ID -c $EKS_CLUSTER_NAME
```

## Detailed Deployment

### 1. Environment Setup

Set the following environment variables:

```bash
export AWS_REGION="us-east-1"                    # AWS region
export AWS_ACCOUNT_ID="123456789012"             # Your AWS account ID
export EKS_CLUSTER_NAME="my-eks-cluster"         # Your EKS cluster name
export K8S_NAMESPACE="search"                    # Kubernetes namespace
export IMAGE_TAG="latest"                        # Docker image tag
```

### 2. Deploy Using Script

The deployment script handles all necessary steps:

```bash
./deploy-eks.sh \
  --region $AWS_REGION \
  --account $AWS_ACCOUNT_ID \
  --cluster $EKS_CLUSTER_NAME \
  --namespace $K8S_NAMESPACE \
  --tag $IMAGE_TAG
```

### 3. Manual Deployment Steps

If you prefer manual deployment:

#### Step 1: Configure kubectl
```bash
aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME
```

#### Step 2: Create ECR Repository
```bash
aws ecr create-repository \
  --region $AWS_REGION \
  --repository-name search-api \
  --image-scanning-configuration scanOnPush=true
```

#### Step 3: Build and Push Docker Image
```bash
# Build the image
docker build -f Dockerfile -t search-api:$IMAGE_TAG .

# Tag for ECR
docker tag search-api:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/search-api:$IMAGE_TAG

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/search-api:$IMAGE_TAG
```

#### Step 4: Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace $K8S_NAMESPACE

# Apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/search-api -n $K8S_NAMESPACE
```

## Validation

After deployment, validate the setup:

```bash
# Using validation script
./validate-deployment.sh -n $K8S_NAMESPACE

# Manual validation
kubectl get pods -n $K8S_NAMESPACE
kubectl get svc -n $K8S_NAMESPACE
kubectl logs -n $K8S_NAMESPACE -l app=search-api
```

## Accessing the API

### Port Forwarding
```bash
kubectl port-forward -n $K8S_NAMESPACE svc/search-api-service 8081:80
curl http://localhost:8081/health
```

### Load Balancer (Optional)
To expose the service externally, modify the service type:

```yaml
# k8s/service.yaml
spec:
  type: LoadBalancer  # Change from ClusterIP
```

## Configuration

### Environment Variables

The API is configured through a ConfigMap and Secret:

**ConfigMap (k8s/configmap.yaml):**
- `API_HOST`: Host address (default: 0.0.0.0)
- `API_PORT`: Port number (default: 8000)
- `API_NAME`: API name for documentation
- `LOG_LEVEL`: Logging level (info, debug, error)
- `CORS_ORIGINS`: CORS allowed origins

**Secret (k8s/secret.yaml):**
- `API_KEY`: API authentication key
- `API_PASSWORD`: Admin password

### Resource Limits

Default resource allocation:
- **Requests**: 2Gi memory, 1000m CPU
- **Limits**: 8Gi memory, 4000m CPU

Modify in `k8s/deployment.yaml` as needed.

## GPU Support

To enable GPU acceleration:

1. Ensure your EKS cluster has GPU nodes
2. Uncomment GPU lines in `k8s/deployment.yaml`:
```yaml
resources:
  requests:
    nvidia.com/gpu: 1
  limits:
    nvidia.com/gpu: 1
```

## Monitoring

### Health Checks

The deployment includes health checks:
- **Liveness Probe**: `/health` endpoint
- **Readiness Probe**: `/health` endpoint

### Logging

View application logs:
```bash
kubectl logs -n $K8S_NAMESPACE -l app=search-api -f
```

### Metrics

Access deployment metrics:
```bash
kubectl top pods -n $K8S_NAMESPACE
kubectl describe deployment search-api -n $K8S_NAMESPACE
```

## Troubleshooting

### Common Issues

1. **Image Pull Errors**
   - Verify ECR repository exists
   - Check AWS credentials and permissions
   - Ensure image tag matches deployment

2. **Pod Startup Issues**
   - Check resource limits
   - Verify environment variables
   - Review application logs

3. **Service Connection Issues**
   - Verify service selector matches pod labels
   - Check port configuration
   - Test with port-forward

### Debug Commands

```bash
# Check pod status
kubectl get pods -n $K8S_NAMESPACE -l app=search-api

# Describe problematic pod
kubectl describe pod <pod-name> -n $K8S_NAMESPACE

# Check events
kubectl get events -n $K8S_NAMESPACE --sort-by=.metadata.creationTimestamp

# Port forward for testing
kubectl port-forward -n $K8S_NAMESPACE svc/search-api-service 8081:80
```

## Security

### API Authentication

The API uses API key authentication. Update the secret:

```bash
echo -n "your-new-api-key" | base64
kubectl patch secret search-api-secrets -n $K8S_NAMESPACE -p '{"data":{"API_KEY":"<base64-encoded-key>"}}'
```

### Network Policies

Consider implementing network policies to restrict traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: search-api-network-policy
  namespace: search
spec:
  podSelector:
    matchLabels:
      app: search-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from: []
    ports:
    - protocol: TCP
      port: 8000
```

## Scaling

### Horizontal Pod Autoscaler

Enable automatic scaling:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: search-api-hpa
  namespace: search
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: search-api
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Manual Scaling

```bash
kubectl scale deployment search-api --replicas=3 -n $K8S_NAMESPACE
```

## Cleanup

To remove the deployment:

```bash
kubectl delete namespace $K8S_NAMESPACE
aws ecr delete-repository --repository-name search-api --force --region $AWS_REGION
```

## Support

For issues or questions:
1. Check application logs
2. Review Kubernetes events
3. Validate configuration
4. Consult troubleshooting section

## Files Structure

```
api/search/
├── deploy-eks.sh              # Main deployment script
├── validate-deployment.sh     # Validation script
├── EKS-DEPLOYMENT.md         # This documentation
├── k8s/
│   ├── namespace.yaml        # Namespace configuration
│   ├── configmap.yaml        # Application configuration
│   ├── secret.yaml           # Secrets (API keys, passwords)
│   ├── service.yaml          # Kubernetes service
│   └── deployment.yaml       # Deployment specification
├── Dockerfile                # Docker image definition
└── requirements.txt          # Python dependencies
```
