#!/bin/bash
# Script to fix IAM role and recreate EKS node groups

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
NODE_ROLE_NAME="AmazonEKSAutoNodeRole"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🔧 Fixing IAM Role and Recreating Node Groups"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Node Role: $NODE_ROLE_NAME"
echo "=========================================="

# Wait for node groups to be deleted
echo "📋 Waiting for node groups to be deleted..."
while true; do
    SYSTEM_STATUS=$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "system-nodes" --region "$REGION" --query 'nodegroup.status' --output text 2>/dev/null || echo "NOT_FOUND")
    GPU_STATUS=$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "gpu-nodes" --region "$REGION" --query 'nodegroup.status' --output text 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$SYSTEM_STATUS" = "NOT_FOUND" ] && [ "$GPU_STATUS" = "NOT_FOUND" ]; then
        echo "✅ Node groups deleted successfully"
        break
    fi
    
    echo "⏳ Still deleting... System: $SYSTEM_STATUS, GPU: $GPU_STATUS"
    sleep 30
done

# Ensure all required policies are attached
echo "📋 Ensuring IAM role has all required policies..."
aws iam attach-role-policy --role-name "$NODE_ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonEKSWorkerNodeMinimalPolicy" 2>/dev/null || echo "Policy already attached"
aws iam attach-role-policy --role-name "$NODE_ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy" 2>/dev/null || echo "Policy already attached"
aws iam attach-role-policy --role-name "$NODE_ROLE_NAME" --policy-arn "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPullOnly" 2>/dev/null || echo "Policy already attached"

echo "✅ IAM role policies updated"

# Get subnet and security group info
echo "📋 Getting VPC configuration..."
VPC_CONFIG=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.resourcesVpcConfig')
SUBNET_IDS=$(echo "$VPC_CONFIG" | jq -r '.subnetIds[]' | tr '\n' ' ')
NODE_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$NODE_ROLE_NAME"

echo "Subnets: $SUBNET_IDS"
echo "Node Role ARN: $NODE_ROLE_ARN"

# Create system node group
echo "📋 Creating system node group..."
aws eks create-nodegroup \
    --cluster-name "$CLUSTER_NAME" \
    --nodegroup-name "system-nodes" \
    --region "$REGION" \
    --subnets $SUBNET_IDS \
    --instance-types "t3.medium" "t3.large" \
    --node-role "$NODE_ROLE_ARN" \
    --scaling-config minSize=2,maxSize=4,desiredSize=2 \
    --disk-size 100 \
    --ami-type AL2023_x86_64_STANDARD \
    --labels "node-type=system"

echo "✅ System node group creation started"

# Create GPU node group
echo "📋 Creating GPU node group..."
aws eks create-nodegroup \
    --cluster-name "$CLUSTER_NAME" \
    --nodegroup-name "gpu-nodes" \
    --region "$REGION" \
    --subnets $SUBNET_IDS \
    --instance-types "g4dn.xlarge" "g4dn.2xlarge" \
    --node-role "$NODE_ROLE_ARN" \
    --scaling-config minSize=0,maxSize=5,desiredSize=1 \
    --disk-size 100 \
    --ami-type AL2023_x86_64_STANDARD \
    --labels "node-type=gpu,accelerator=nvidia-tesla-t4" \
    --taints "key=nvidia.com/gpu,value=true,effect=NO_SCHEDULE"

echo "✅ GPU node group creation started"

echo "📋 Monitoring node group creation..."
# Function to wait for node group to be ready
wait_for_nodegroup() {
    local NODEGROUP_NAME=$1
    echo "⏳ Waiting for node group $NODEGROUP_NAME to become ready..."
    
    while true; do
        STATUS=$(aws eks describe-nodegroup \
            --cluster-name "$CLUSTER_NAME" \
            --nodegroup-name "$NODEGROUP_NAME" \
            --region "$REGION" \
            --query 'nodegroup.status' \
            --output text)
        
        echo "  [$NODEGROUP_NAME] Status: $STATUS"
        
        if [ "$STATUS" = "ACTIVE" ]; then
            echo "✅ Node group $NODEGROUP_NAME is ready!"
            break
        elif [ "$STATUS" = "CREATE_FAILED" ]; then
            echo "❌ Node group $NODEGROUP_NAME failed to create!"
            aws eks describe-nodegroup \
                --cluster-name "$CLUSTER_NAME" \
                --nodegroup-name "$NODEGROUP_NAME" \
                --region "$REGION" \
                --query 'nodegroup.health.issues' \
                --output table
            break
        fi
        
        sleep 30
    done
}

# Wait for both node groups
wait_for_nodegroup "system-nodes"
wait_for_nodegroup "gpu-nodes"

echo "🎉 Node group creation completed!"
echo "=========================================="

# Update kubeconfig and check nodes
echo "📋 Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

echo "📋 Checking Kubernetes nodes..."
kubectl get nodes --show-labels

echo "📋 Your role configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodeMinimalPolicy"

echo "📋 Next steps:"
echo "1. Install NVIDIA device plugin: ./install_nvidia_plugin.sh"
echo "2. Deploy your applications"
echo "3. Test GPU functionality"

echo "✅ Setup completed successfully!"
