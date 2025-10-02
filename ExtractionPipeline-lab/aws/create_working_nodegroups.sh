#!/bin/bash
# Simple script to create working EKS node groups

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🔧 Creating Working EKS Node Groups"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Account ID: $ACCOUNT_ID"
echo "=================================="

# Wait for any existing node groups to be deleted
echo "📋 Waiting for existing node groups to be deleted..."
while true; do
    NODEGROUPS=$(aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --query 'nodegroups' --output text)
    if [ -z "$NODEGROUPS" ]; then
        echo "✅ No existing node groups found"
        break
    fi
    echo "⏳ Still deleting existing node groups: $NODEGROUPS"
    sleep 30
done

# Get VPC info
echo "📋 Getting VPC configuration..."
VPC_CONFIG=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.resourcesVpcConfig')
SUBNET_IDS=$(echo "$VPC_CONFIG" | jq -r '.subnetIds[]' | tr '\n' ' ')
NODE_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/AmazonEKSAutoNodeRole"

echo "Subnets: $SUBNET_IDS"
echo "Node Role: $NODE_ROLE_ARN"

# Create system node group with minimal configuration
echo "📋 Creating system node group..."
aws eks create-nodegroup \
    --cluster-name "$CLUSTER_NAME" \
    --nodegroup-name "system-nodes" \
    --region "$REGION" \
    --subnets $SUBNET_IDS \
    --instance-types "t3.medium" \
    --node-role "$NODE_ROLE_ARN" \
    --scaling-config minSize=1,maxSize=3,desiredSize=2 \
    --disk-size 50 \
    --ami-type AL2023_x86_64_STANDARD

echo "✅ System node group creation started"

# Wait for system nodes to be active before creating GPU nodes
echo "📋 Waiting for system nodes to be active..."
while true; do
    STATUS=$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "system-nodes" --region "$REGION" --query 'nodegroup.status' --output text)
    echo "  [system-nodes] Status: $STATUS"
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ System nodes are active!"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "❌ System nodes failed to create!"
        aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "system-nodes" --region "$REGION" --query 'nodegroup.health.issues' --output table
        exit 1
    fi
    
    sleep 30
done

# Create GPU node group
echo "📋 Creating GPU node group..."
aws eks create-nodegroup \
    --cluster-name "$CLUSTER_NAME" \
    --nodegroup-name "gpu-nodes" \
    --region "$REGION" \
    --subnets $SUBNET_IDS \
    --instance-types "g4dn.xlarge" \
    --node-role "$NODE_ROLE_ARN" \
    --scaling-config minSize=0,maxSize=3,desiredSize=1 \
    --disk-size 50 \
    --ami-type AL2023_x86_64_STANDARD \
    --labels "node-type=gpu"

echo "✅ GPU node group creation started"

# Wait for GPU nodes
echo "📋 Waiting for GPU nodes to be active..."
while true; do
    STATUS=$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "gpu-nodes" --region "$REGION" --query 'nodegroup.status' --output text)
    echo "  [gpu-nodes] Status: $STATUS"
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ GPU nodes are active!"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "❌ GPU nodes failed to create!"
        aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "gpu-nodes" --region "$REGION" --query 'nodegroup.health.issues' --output table
        exit 1
    fi
    
    sleep 30
done

echo "🎉 Node groups created successfully!"
echo "=================================="

# Update kubeconfig and check nodes
echo "📋 Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

echo "📋 Checking Kubernetes nodes..."
kubectl get nodes -o wide

echo "📋 Node group summary:"
aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --output table

echo "📋 Your role configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodeMinimalPolicy"

echo "📋 Next steps:"
echo "1. Install NVIDIA device plugin: ./install_nvidia_plugin.sh"
echo "2. Deploy your applications"

echo "✅ Setup completed successfully!"
