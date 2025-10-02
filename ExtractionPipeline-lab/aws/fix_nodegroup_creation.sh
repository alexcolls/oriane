#!/bin/bash

# Fix nodegroup creation with proper subnet specification
# This script addresses the subnet ID format issue in the previous attempt

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
NODEGROUP_NAME="fixed-nodes-$(date +%Y%m%d-%H%M%S)"
NODE_ROLE="arn:aws:iam::509399609859:role/AmazonEKSAutoNodeRole"

echo "🚀 Creating EKS NodeGroup with Fixed Configuration"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "NodeGroup: $NODEGROUP_NAME"

# Wait for any existing nodegroup deletion to complete
echo "⏳ Waiting for any existing nodegroup deletion to complete..."
while true; do
    NODEGROUPS=$(aws eks list-nodegroups --cluster-name $CLUSTER_NAME --region $REGION --query 'nodegroups' --output text)
    if [ -z "$NODEGROUPS" ] || [ "$NODEGROUPS" = "None" ]; then
        echo "✅ No existing nodegroups found, proceeding with creation"
        break
    fi
    echo "⏳ Still waiting for nodegroup deletion... (found: $NODEGROUPS)"
    sleep 30
done

# Get cluster subnets
echo "🔍 Getting cluster subnets..."
SUBNETS=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.resourcesVpcConfig.subnetIds' --output text)
echo "Available subnets: $SUBNETS"

# Convert to array and select first two subnets
SUBNET_ARRAY=($SUBNETS)
SUBNET1=${SUBNET_ARRAY[0]}
SUBNET2=${SUBNET_ARRAY[1]}

echo "Selected subnets: $SUBNET1, $SUBNET2"

# Create nodegroup with proper subnet specification
echo "🔍 Creating nodegroup with proper configuration..."
aws eks create-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NODEGROUP_NAME \
    --subnets $SUBNET1 $SUBNET2 \
    --instance-types t3.medium \
    --ami-type AL2023_x86_64_STANDARD \
    --node-role $NODE_ROLE \
    --scaling-config minSize=1,maxSize=3,desiredSize=2 \
    --disk-size 20 \
    --capacity-type ON_DEMAND \
    --update-config maxUnavailable=1 \
    --region $REGION

echo "✅ NodeGroup creation initiated: $NODEGROUP_NAME"
echo "⏳ Waiting for nodegroup to become active (this may take 10-15 minutes)..."

# Wait for nodegroup to be active
TIMEOUT=900  # 15 minutes
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    STATUS=$(aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $NODEGROUP_NAME --region $REGION --query 'nodegroup.status' --output text)
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ NodeGroup is now ACTIVE!"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "❌ NodeGroup creation failed!"
        aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $NODEGROUP_NAME --region $REGION --query 'nodegroup.health.issues'
        exit 1
    else
        echo "⏳ NodeGroup status: $STATUS (${ELAPSED}s elapsed)"
        sleep 30
        ELAPSED=$((ELAPSED + 30))
    fi
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "❌ NodeGroup creation timed out after ${TIMEOUT}s"
    exit 1
fi

# Check nodes
echo "🔍 Checking cluster nodes..."
kubectl get nodes

echo "✅ NodeGroup creation completed successfully!"
