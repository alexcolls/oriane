#!/bin/bash
# Master script to set up complete EKS environment with node groups and GPU support

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"

echo "🎯 Complete EKS Node Group Setup"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Script Directory: $SCRIPT_DIR"
echo "=========================================="

# Make scripts executable
chmod +x "$SCRIPT_DIR/create_eks_nodegroups.sh"
chmod +x "$SCRIPT_DIR/install_nvidia_plugin.sh"

# Step 1: Create node groups
echo "📋 Step 1: Creating EKS node groups..."
"$SCRIPT_DIR/create_eks_nodegroups.sh"

# Step 2: Install NVIDIA device plugin
echo "📋 Step 2: Installing NVIDIA device plugin..."
"$SCRIPT_DIR/install_nvidia_plugin.sh"

# Step 3: Verify the setup
echo "📋 Step 3: Verifying complete setup..."
echo "----------------------------------------"

# Update kubeconfig
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Show all nodes
echo "📋 All nodes in cluster:"
kubectl get nodes --show-labels

# Show node groups
echo "📋 Node groups:"
aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --output table

# Show GPU availability
echo "📋 GPU resources:"
kubectl get nodes -o custom-columns=NAME:.metadata.name,GPU:.status.capacity.nvidia\\.com/gpu

# Show system pods
echo "📋 System pods status:"
kubectl get pods -n kube-system | grep -E "(nvidia|device-plugin)"

echo "🎉 Complete EKS setup finished!"
echo "=========================================="
echo "📋 Next steps:"
echo "1. Deploy your applications to the cluster"
echo "2. Test GPU functionality with:"
echo "   kubectl run gpu-test --image=nvidia/cuda:11.0-base --rm -it --restart=Never --limits=nvidia.com/gpu=1 -- nvidia-smi"
echo "3. Deploy your pipeline using the k8s manifests"
echo ""
echo "📋 Your role names for configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodePolicy"
