#!/bin/bash

# Fix and Create Node Group Script
# This script will properly identify subnets and create a new node group

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
VPC_ID="vpc-0c3ab41805ec7bf44"
NODE_ROLE="arn:aws:iam::509399609859:role/AmazonEKSAutoNodeRole"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 Checking available subnets in VPC..."

# Get all subnets in the VPC
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --region $REGION --query 'Subnets[*].SubnetId' --output text)
echo "Available subnets: $SUBNETS"

# Convert to array
SUBNET_ARRAY=($SUBNETS)

if [ ${#SUBNET_ARRAY[@]} -lt 2 ]; then
    echo "❌ Need at least 2 subnets for node group creation"
    exit 1
fi

# Use first two subnets
SUBNET1=${SUBNET_ARRAY[0]}
SUBNET2=${SUBNET_ARRAY[1]}

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 Selected subnets: $SUBNET1, $SUBNET2"

# Generate unique node group name
NODEGROUP_NAME="fixed-nodes-$(date +%Y%m%d-%H%M%S)"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Creating node group: $NODEGROUP_NAME"

# Create the node group with proper subnet specification
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

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Node group creation initiated"

# Wait for node group to become active
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⏳ Waiting for node group to become active (this may take 10-15 minutes)..."

TIMEOUT=900  # 15 minutes
START_TIME=$(date +%s)

while true; do
    STATUS=$(aws eks describe-nodegroup \
        --cluster-name $CLUSTER_NAME \
        --nodegroup-name $NODEGROUP_NAME \
        --region $REGION \
        --query 'nodegroup.status' \
        --output text 2>/dev/null || echo "NOT_FOUND")
    
    ELAPSED_TIME=$(($(date +%s) - $START_TIME))
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Node group is now ACTIVE!"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Node group creation failed"
        # Get failure details
        aws eks describe-nodegroup \
            --cluster-name $CLUSTER_NAME \
            --nodegroup-name $NODEGROUP_NAME \
            --region $REGION \
            --query 'nodegroup.health.issues'
        exit 1
    elif [ $ELAPSED_TIME -ge $TIMEOUT ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Node group creation timed out after ${TIMEOUT}s"
        exit 1
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⏳ Node group status: $STATUS (${ELAPSED_TIME}s elapsed)"
        sleep 30
    fi
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🎉 Node group creation completed successfully!"

# Check nodes in the cluster
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 Checking nodes in the cluster..."
kubectl get nodes --show-labels

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 Checking node group details..."
aws eks describe-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NODEGROUP_NAME \
    --region $REGION \
    --query 'nodegroup.{Name:nodegroupName,Status:status,DesiredSize:scalingConfig.desiredSize,InstanceTypes:instanceTypes,Subnets:subnets}'

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📋 Node group creation process complete!"
