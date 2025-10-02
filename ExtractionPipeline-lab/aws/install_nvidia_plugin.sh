#!/bin/bash
# Script to install NVIDIA device plugin for GPU nodes in EKS

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"

echo "🚀 Installing NVIDIA Device Plugin for GPU Nodes"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "----------------------------------------"

# Update kubeconfig
echo "📋 Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Check if GPU nodes are available
echo "📋 Checking for GPU nodes..."
GPU_NODES=$(kubectl get nodes -l node-type=gpu --no-headers 2>/dev/null | wc -l)
if [ "$GPU_NODES" -eq 0 ]; then
    echo "⚠️  No GPU nodes found. Make sure GPU node groups are created and active."
    echo "📋 Current nodes:"
    kubectl get nodes --show-labels
    exit 1
fi

echo "✅ Found $GPU_NODES GPU nodes"

# Install NVIDIA device plugin
echo "📋 Installing NVIDIA device plugin..."
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# Wait for the plugin to be ready
echo "⏳ Waiting for NVIDIA device plugin to be ready..."
kubectl rollout status daemonset/nvidia-device-plugin-daemonset -n kube-system --timeout=300s

# Verify GPU resources are available
echo "📋 Verifying GPU resources..."
sleep 10
GPU_CAPACITY=$(kubectl get nodes -l node-type=gpu -o jsonpath='{.items[*].status.capacity.nvidia\.com/gpu}' | tr ' ' '\n' | grep -v '^$' | wc -l)

if [ "$GPU_CAPACITY" -gt 0 ]; then
    echo "✅ GPU resources detected: $GPU_CAPACITY GPUs available"
    echo "📋 GPU node details:"
    kubectl get nodes -l node-type=gpu -o custom-columns=NAME:.metadata.name,GPU:.status.capacity.nvidia\\.com/gpu
else
    echo "⚠️  No GPU resources detected. Checking plugin status..."
    kubectl get pods -n kube-system -l name=nvidia-device-plugin-ds
    kubectl logs -n kube-system -l name=nvidia-device-plugin-ds --tail=50
fi

echo "✅ NVIDIA device plugin installation completed!"
echo "----------------------------------------"
echo "📋 To test GPU access, create a test pod:"
echo "kubectl run gpu-test --image=nvidia/cuda:11.0-base --rm -it --restart=Never --limits=nvidia.com/gpu=1 -- nvidia-smi"
