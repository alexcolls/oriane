#!/bin/bash

# =============================================================================
# KinD Cluster Setup Script with GPU Support
# =============================================================================
# This script sets up a KinD cluster with NVIDIA device plugin support
# for testing the pipeline API before deploying to EKS
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLUSTER_NAME="pipeline-test"
KIND_VERSION="v0.20.0"

echo "=== KinD Cluster Setup ==="
echo "Project root: $PROJECT_ROOT"
echo "Cluster name: $CLUSTER_NAME"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."
if ! command_exists docker; then
    echo "ERROR: Docker is not installed or not in PATH"
    exit 1
fi

if ! command_exists kubectl; then
    echo "ERROR: kubectl is not installed or not in PATH"
    exit 1
fi

# Install KinD if not already installed
if ! command_exists kind; then
    echo "Installing KinD..."
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/${KIND_VERSION}/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind || {
        echo "Cannot install to /usr/local/bin, installing to ~/.local/bin instead"
        mkdir -p ~/.local/bin
        mv ./kind ~/.local/bin/kind
        export PATH="$HOME/.local/bin:$PATH"
    }
else
    echo "KinD already installed: $(kind version)"
fi

# Check for GPU support
echo "Checking for GPU support..."
if command_exists nvidia-smi; then
    echo "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    GPU_SUPPORT=true
else
    echo "No NVIDIA GPU detected, proceeding with CPU-only setup"
    GPU_SUPPORT=false
fi

# Create KinD configuration
echo "Creating KinD cluster configuration..."
if [ "$GPU_SUPPORT" = true ]; then
    cat > "$PROJECT_ROOT/kind-config.yaml" << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraMounts:
  - hostPath: /dev/nvidia0
    containerPath: /dev/nvidia0
  - hostPath: /dev/nvidiactl
    containerPath: /dev/nvidiactl
  - hostPath: /dev/nvidia-uvm
    containerPath: /dev/nvidia-uvm
  - hostPath: /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1
    containerPath: /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1
  - hostPath: /usr/bin/nvidia-smi
    containerPath: /usr/bin/nvidia-smi
- role: worker
  extraMounts:
  - hostPath: /dev/nvidia0
    containerPath: /dev/nvidia0
  - hostPath: /dev/nvidiactl
    containerPath: /dev/nvidiactl
  - hostPath: /dev/nvidia-uvm
    containerPath: /dev/nvidia-uvm
  - hostPath: /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1
    containerPath: /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1
  - hostPath: /usr/bin/nvidia-smi
    containerPath: /usr/bin/nvidia-smi
EOF
else
    cat > "$PROJECT_ROOT/kind-config.yaml" << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
EOF
fi

# Delete existing cluster if it exists
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
    echo "Deleting existing cluster: $CLUSTER_NAME"
    kind delete cluster --name "$CLUSTER_NAME"
fi

# Create new cluster
echo "Creating KinD cluster: $CLUSTER_NAME"
cd "$PROJECT_ROOT"
kind create cluster --name "$CLUSTER_NAME" --config kind-config.yaml

# Wait for cluster to be ready
echo "Waiting for cluster nodes to be ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=300s

# Install NVIDIA device plugin if GPU support is available
if [ "$GPU_SUPPORT" = true ]; then
    echo "Installing NVIDIA device plugin..."
    kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.1/nvidia-device-plugin.yml
    
    # Wait for device plugin to be ready
    echo "Waiting for NVIDIA device plugin to be ready..."
    kubectl wait --for=condition=Ready pod -l name=nvidia-device-plugin-ds -n kube-system --timeout=300s
fi

# Create pipeline namespace
echo "Creating pipeline namespace..."
kubectl create namespace pipeline || echo "Namespace already exists"

# Display cluster information
echo ""
echo "=== Cluster Information ==="
echo "Cluster name: $CLUSTER_NAME"
echo "Nodes:"
kubectl get nodes -o wide
echo ""
echo "GPU support: $GPU_SUPPORT"
if [ "$GPU_SUPPORT" = true ]; then
    echo "NVIDIA device plugin status:"
    kubectl get pods -n kube-system | grep nvidia || echo "No NVIDIA pods found"
fi

echo ""
echo "✓ KinD cluster setup complete!"
echo "  - Cluster name: $CLUSTER_NAME"
echo "  - GPU support: $GPU_SUPPORT"
echo "  - Namespace 'pipeline' created"
echo ""
echo "Next steps:"
echo "  1. Run './scripts/build-and-deploy.sh' to build and deploy the application"
echo "  2. Run './scripts/test-pipeline.sh' to run integration tests"
