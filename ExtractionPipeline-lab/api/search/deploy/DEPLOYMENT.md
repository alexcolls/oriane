# Search API Deployment Guide

This guide provides scripts and instructions for deploying the Visual Search API to both KinD (local testing) and EKS (production) environments.

## Prerequisites

- Docker installed and running
- kubectl installed and configured
- AWS CLI installed and configured (for EKS deployment)
- KinD installed (for local testing)
- NVIDIA GPU drivers (optional, for GPU acceleration)

## Quick Start

### Option 1: Interactive Menu
```bash
./scripts/run-all.sh
```

### Option 2: Manual Steps

1. **Setup KinD Cluster**
   ```bash
   ./scripts/setup-kind-cluster.sh
   ```

2. **Build and Deploy to KinD**
   ```bash
   ./scripts/build-and-deploy.sh
   ```

3. **Test the Deployment**
   ```bash
   ./scripts/test-search-api.sh
   ```

4. **Deploy to EKS (Optional)**
   ```bash
   ./scripts/deploy-to-eks.sh
   ```

5. **Cleanup KinD Cluster**
   ```bash
   ./scripts/cleanup-kind-cluster.sh
   ```

## Scripts Overview

### `setup-kind-cluster.sh`
- Creates a KinD cluster with GPU support if available
- Installs NVIDIA device plugin for GPU workloads
- Creates the `search-api` namespace
- Configures cluster for testing

### `build-and-deploy.sh`
- Builds the search API Docker image
- Loads the image into the KinD cluster
- Applies Kubernetes manifests (ConfigMap, Secret, Deployment, Service)
- Waits for deployment to be ready
- Performs basic health checks

### `test-search-api.sh`
- Runs comprehensive integration tests
- Tests health, root, and debug endpoints
- Validates service connectivity
- Reports test results

### `deploy-to-eks.sh`
- Builds and pushes Docker image to ECR
- Creates EKS-specific deployment with GPU support
- Deploys to existing EKS cluster
- Configures GPU node selection and tolerations

### `cleanup-kind-cluster.sh`
- Removes the KinD cluster
- Cleans up Docker images
- Removes configuration files
- Resets kubectl contexts

### `run-all.sh`
- Interactive menu for all operations
- Handles error checking and script execution
- Provides guided workflow

## Deployment Explanation

### Kubernetes Objects

The Kubernetes manifests provided in the `k8s` directory facilitate deploying the Search API into a Kubernetes cluster. Here's a breakdown of how these manifests work:

- **Namespace (`namespace.yaml`)**: Sets up a dedicated namespace called `search` for the application's resources, providing isolation within the cluster.

- **Deployment (`deployment.yaml`)**: This manages the creation and scaling of Pods. It specifies crucial parameters like the number of desired replicas (using `replicas`), the Docker image (`509399609859.dkr.ecr.us-east-1.amazonaws.com/search-api:latest`), and environmental configurations from a ConfigMap and a Secret.

  - Upon applying the deployment, Kubernetes creates a ReplicaSet to maintain the desired number of running Pods at all times.
  - Each Pod consists of one or more containers, in this case, the Search API Docker container pulled from the specified ECR repository.

- **Service (`service.yaml`)**: Exposes the application's Pods internally within the Kubernetes cluster. It's defined as a `ClusterIP` type by default, but can be changed to `LoadBalancer` for external access by modifying its type. It routes traffic to the Pods based on the selectors matching the labels specified in the Pods.

- **ConfigMap (`configmap.yaml`)**: Supplies configuration data for the application, allowing dynamic adjustment without altering container images.

- **Secret (`secret.yaml`)**: Stores sensitive data like API keys and passwords, accessed by the Pods as needed.

- **Ingress (`ingress.yaml`)**: Manages external access to the services, associating them with specific hosts and paths. It creates an external ALB for handling incoming requests.

### ECR Image

The deployment uses the ECR image `509399609859.dkr.ecr.us-east-1.amazonaws.com/search-api:latest`. The Kubernetes cluster pulls this image as specified in the `image` field of the deployment manifest.

- The `imagePullPolicy: IfNotPresent` ensures the image is pulled only if it's not already present on the node.

### Application → Cluster Linkage

The deployment follows this sequence:

1. **Deployment → ReplicaSet → Pods**: 
   - The Deployment manifest (`deployment.yaml`) creates a ReplicaSet that ensures the desired number of Pods (replicas: 1) are running.
   - Each Pod contains a single container running the Search API image.

2. **Service → ClusterIP/LoadBalancer**:
   - The Service (`service.yaml`) creates a ClusterIP endpoint that routes traffic to the Pods based on label selectors.
   - The Ingress (`ingress.yaml`) creates an AWS Application Load Balancer (ALB) for external access.

3. **Container Image Pull**:
   - Kubernetes pulls the Docker image `509399609859.dkr.ecr.us-east-1.amazonaws.com/search-api:latest` from the ECR repository.
   - The cluster authenticates with ECR using the node's IAM role or service account credentials.
   - The image is cached on the node for faster subsequent Pod starts.

### CloudFormation Template

A CloudFormation template exists to deploy the Search API to an existing EKS cluster. Here's how it works:

- **cluster-template.yaml**: This template defines parameters like `ClusterName` and `EcrImageUri`, and resources like deployments and services as `AWS::EKS::Manifest`. These resources are deployed to the specified EKS cluster, allowing tight integration with AWS infrastructure.
- The template creates a LoadBalancer service instead of ClusterIP for direct external access.
- It uses the same ECR image but allows the URI to be parameterized for different environments.

## Configuration

### Environment Variables
The search API uses the following environment variables (configured in `k8s/configmap.yaml`):

- `API_HOST`: Host to bind to (default: 0.0.0.0)
- `API_PORT`: Port to listen on (default: 8000)
- `API_NAME`: Service name (default: Visual Search API)
- `ENVIRONMENT`: Environment type (default: development)
- `NVIDIA_VISIBLE_DEVICES`: GPU visibility (default: all)
- `CORS_ORIGINS`: CORS allowed origins (default: *)

### Secrets
API credentials are stored in `k8s/secret.yaml`:
- `API_KEY`: Base64 encoded API key
- `API_PASSWORD`: Base64 encoded API password

## GPU Support

### KinD Cluster
- Automatically detects NVIDIA GPUs
- Mounts GPU devices and drivers
- Installs NVIDIA device plugin
- Configures GPU resource allocation

### EKS Cluster
- Uses GPU-enabled instance types (g4dn.xlarge)
- Configures node selectors for GPU nodes
- Sets GPU resource requests and limits
- Handles GPU-specific tolerations

## Troubleshooting

### Common Issues

1. **KinD cluster creation fails**
   - Check Docker is running
   - Verify GPU drivers are installed
   - Ensure no port conflicts

2. **Image build fails**
   - Check Dockerfile syntax
   - Verify dependencies are available
   - Ensure sufficient disk space

3. **Deployment fails**
   - Check resource limits
   - Verify namespace exists
   - Review pod logs for errors

4. **EKS deployment fails**
   - Verify AWS credentials
   - Check EKS cluster exists
   - Ensure ECR permissions

### Debugging Commands

```bash
# Check cluster status
kubectl get nodes
kubectl get pods -n search-api

# View logs
kubectl logs -n search-api deployment/search-api

# Check resource usage
kubectl top pods -n search-api

# Port forward for testing
kubectl port-forward -n search-api service/search-api-service 8080:80

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/debug/settings
```

## Architecture

### KinD Deployment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Docker Host   │    │   KinD Cluster  │    │   Search API    │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │  Docker   │  │    │  │   Node    │  │    │  │    Pod    │  │
│  │  Engine   │  │    │  │           │  │    │  │           │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │   GPU     │  │    │  │  Service  │  │    │  │  FastAPI  │  │
│  │ Drivers   │  │    │  │           │  │    │  │   Server  │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### EKS Deployment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      AWS        │    │   EKS Cluster   │    │      ECR        │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │    EC2    │  │    │  │  GPU Node │  │    │  │  Docker   │  │
│  │ Instances │  │    │  │           │  │    │  │  Registry │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │                 │
│  │    IAM    │  │    │  │  Search   │  │    │                 │
│  │   Roles   │  │    │  │    API    │  │    │                 │
│  └───────────┘  │    │  └───────────┘  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Next Steps

1. Test the deployment locally with KinD
2. Validate GPU acceleration (if available)
3. Deploy to EKS for production use
4. Configure monitoring and logging
5. Set up CI/CD pipeline for automated deployments

For more information, see the main README.md file.
