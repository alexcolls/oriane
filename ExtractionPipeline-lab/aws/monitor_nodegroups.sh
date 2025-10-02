#!/bin/bash
# Script to monitor EKS node group creation progress

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"

echo "📋 Monitoring EKS Node Group Creation Progress"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "=========================================="

# Function to check node group status
check_nodegroup_status() {
    local NODEGROUP_NAME=$1
    
    STATUS=$(aws eks describe-nodegroup \
        --cluster-name "$CLUSTER_NAME" \
        --nodegroup-name "$NODEGROUP_NAME" \
        --region "$REGION" \
        --query 'nodegroup.status' \
        --output text)
    
    echo "[$NODEGROUP_NAME] Status: $STATUS"
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ $NODEGROUP_NAME is ready!"
        return 0
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "❌ $NODEGROUP_NAME failed to create!"
        return 1
    else
        echo "⏳ $NODEGROUP_NAME is still creating..."
        return 2
    fi
}

# Monitor both node groups
echo "📋 Initial status check:"
check_nodegroup_status "system-nodes"
SYSTEM_STATUS=$?
check_nodegroup_status "gpu-nodes"
GPU_STATUS=$?

echo ""
echo "📋 Monitoring progress (checking every 30 seconds)..."
echo "Press Ctrl+C to stop monitoring"

while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Checking node group status..."
    
    # Check system nodes
    if [ $SYSTEM_STATUS -eq 2 ]; then
        check_nodegroup_status "system-nodes"
        SYSTEM_STATUS=$?
    fi
    
    # Check GPU nodes  
    if [ $GPU_STATUS -eq 2 ]; then
        check_nodegroup_status "gpu-nodes"
        GPU_STATUS=$?
    fi
    
    # If both are done (success or failure), break
    if [ $SYSTEM_STATUS -ne 2 ] && [ $GPU_STATUS -ne 2 ]; then
        echo ""
        echo "🎉 Node group creation completed!"
        break
    fi
    
    echo "----------------------------------------"
    sleep 30
done

echo ""
echo "📋 Final Status Summary:"
echo "System Nodes: $(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "system-nodes" --region "$REGION" --query 'nodegroup.status' --output text)"
echo "GPU Nodes: $(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "gpu-nodes" --region "$REGION" --query 'nodegroup.status' --output text)"

echo ""
echo "📋 Updating kubeconfig and checking nodes..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Wait a bit for nodes to register
sleep 10

echo "📋 Kubernetes nodes:"
kubectl get nodes --show-labels || echo "⚠️  kubectl not configured or nodes not ready yet"

echo ""
echo "📋 Next steps:"
echo "1. Install NVIDIA device plugin: ./install_nvidia_plugin.sh"
echo "2. Deploy your applications"
echo "3. Test GPU functionality"

echo ""
echo "📋 Your final role configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodePolicy"
