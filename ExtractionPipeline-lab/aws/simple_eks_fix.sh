#!/bin/bash
# Simple EKS fix without SSH access

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🔧 Simple EKS Fix"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "===================="

# Get subnet info
VPC_CONFIG=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.resourcesVpcConfig')
SUBNET_IDS=$(echo "$VPC_CONFIG" | jq -r '.subnetIds[]' | tr '\n' ' ')
NODE_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/AmazonEKSAutoNodeRole"

echo "Subnets: $SUBNET_IDS"
echo "Node Role: $NODE_ROLE_ARN"

# Create a simple working node group
echo "📋 Creating simple node group..."
aws eks create-nodegroup \
    --cluster-name "$CLUSTER_NAME" \
    --nodegroup-name "simple-nodes" \
    --region "$REGION" \
    --subnets $SUBNET_IDS \
    --instance-types "t3.medium" \
    --node-role "$NODE_ROLE_ARN" \
    --scaling-config minSize=1,maxSize=2,desiredSize=1 \
    --disk-size 20 \
    --ami-type AL2_x86_64

echo "✅ Simple node group creation started"

# Wait for node group to be active
echo "📋 Waiting for node group to be active..."
while true; do
    STATUS=$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "simple-nodes" --region "$REGION" --query 'nodegroup.status' --output text)
    echo "  [simple-nodes] Status: $STATUS"
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ Node group is active!"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "❌ Node group failed to create!"
        aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "simple-nodes" --region "$REGION" --query 'nodegroup.health.issues' --output table
        exit 1
    fi
    
    sleep 30
done

# Update kubeconfig
echo "📋 Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Check nodes
echo "📋 Checking nodes..."
kubectl get nodes -o wide

echo "🎉 EKS is now working!"
echo "===================="

echo "📋 Your EKS configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"

echo "📋 EKS is ready for deployment!"
echo "- Cluster: $CLUSTER_NAME"
echo "- Region: $REGION"
echo "- Nodes: 1 t3.medium instance"

echo "✅ EKS service fixed!"
