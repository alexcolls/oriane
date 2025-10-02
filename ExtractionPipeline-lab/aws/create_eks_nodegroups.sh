#!/bin/bash
# Script to create EKS node groups for oriane-pipeline-api-cluster
# This script creates both regular and GPU node groups

set -e

# Configuration
CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🚀 Creating EKS Node Groups"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Account ID: $ACCOUNT_ID"
echo "----------------------------------------"

# Check if cluster exists and is active
echo "📋 Checking cluster status..."
CLUSTER_STATUS=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.status' --output text)
if [ "$CLUSTER_STATUS" != "ACTIVE" ]; then
    echo "❌ Cluster is not active. Status: $CLUSTER_STATUS"
    exit 1
fi
echo "✅ Cluster is active"

# Get VPC and subnet information
echo "📋 Getting VPC and subnet information..."
VPC_CONFIG=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.resourcesVpcConfig')
SUBNET_IDS=$(echo "$VPC_CONFIG" | jq -r '.subnetIds[]' | tr '\n' ' ')
SECURITY_GROUP_IDS=$(echo "$VPC_CONFIG" | jq -r '.clusterSecurityGroupId')

echo "Subnets: $SUBNET_IDS"
echo "Security Group: $SECURITY_GROUP_IDS"

# Create IAM role for node groups if it doesn't exist
echo "📋 Creating/checking IAM role for node groups..."
NODE_ROLE_NAME="AmazonEKSAutoNodeRole"

# Check if role exists
if aws iam get-role --role-name "$NODE_ROLE_NAME" >/dev/null 2>&1; then
    echo "✅ Node role $NODE_ROLE_NAME already exists"
else
    echo "🔧 Creating IAM role for node groups..."
    
    # Create trust policy for EC2
    cat > /tmp/node-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create IAM role
    aws iam create-role \
        --role-name "$NODE_ROLE_NAME" \
        --assume-role-policy-document file:///tmp/node-trust-policy.json
    
    # Attach required policies
    aws iam attach-role-policy \
        --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy \
        --role-name "$NODE_ROLE_NAME"
    
    aws iam attach-role-policy \
        --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy \
        --role-name "$NODE_ROLE_NAME"
    
    aws iam attach-role-policy \
        --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly \
        --role-name "$NODE_ROLE_NAME"
    
    echo "✅ Created IAM role: $NODE_ROLE_NAME"
fi

NODE_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$NODE_ROLE_NAME"

# Function to create node group
create_nodegroup() {
    local NODEGROUP_NAME=$1
    local INSTANCE_TYPES=$2
    local MIN_SIZE=$3
    local MAX_SIZE=$4
    local DESIRED_SIZE=$5
    local LABELS=$6
    local TAINTS=$7
    
    echo "🔧 Creating node group: $NODEGROUP_NAME"
    
    # Build the command
    local CMD="aws eks create-nodegroup \
        --cluster-name $CLUSTER_NAME \
        --nodegroup-name $NODEGROUP_NAME \
        --region $REGION \
        --subnets $SUBNET_IDS \
        --instance-types $INSTANCE_TYPES \
        --node-role $NODE_ROLE_ARN \
        --scaling-config minSize=$MIN_SIZE,maxSize=$MAX_SIZE,desiredSize=$DESIRED_SIZE \
        --disk-size 100 \
        --ami-type AL2023_x86_64_STANDARD"
    
    # Add labels if provided
    if [ ! -z "$LABELS" ]; then
        CMD="$CMD --labels $LABELS"
    fi
    
    # Add taints if provided
    if [ ! -z "$TAINTS" ]; then
        CMD="$CMD --taints $TAINTS"
    fi
    
    # Execute the command
    eval $CMD
    
    echo "✅ Started creating node group: $NODEGROUP_NAME"
}

# Create system node group (for regular workloads)
echo "📋 Creating system node group..."
create_nodegroup \
    "system-nodes" \
    "t3.medium t3.large" \
    2 \
    4 \
    2 \
    "node-type=system"

# Create GPU node group (for GPU workloads)
echo "📋 Creating GPU node group..."
create_nodegroup \
    "gpu-nodes" \
    "g4dn.xlarge g4dn.2xlarge g5.xlarge" \
    0 \
    5 \
    1 \
    "node-type=gpu,accelerator=nvidia-tesla-t4" \
    "key=nvidia.com/gpu,value=true,effect=NO_SCHEDULE"

echo "🎉 Node group creation initiated!"
echo "----------------------------------------"
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
        
        echo "  Status: $STATUS"
        
        if [ "$STATUS" = "ACTIVE" ]; then
            echo "✅ Node group $NODEGROUP_NAME is ready!"
            break
        elif [ "$STATUS" = "CREATE_FAILED" ]; then
            echo "❌ Node group $NODEGROUP_NAME failed to create!"
            break
        fi
        
        sleep 30
    done
}

# Wait for both node groups
wait_for_nodegroup "system-nodes"
wait_for_nodegroup "gpu-nodes"

echo "🎉 All node groups created successfully!"
echo "----------------------------------------"
echo "📋 Node group summary:"

# List all node groups
aws eks list-nodegroups \
    --cluster-name "$CLUSTER_NAME" \
    --region "$REGION" \
    --query 'nodegroups' \
    --output table

echo "📋 To verify nodes are ready, run:"
echo "kubectl get nodes --show-labels"

echo "📋 To install NVIDIA device plugin for GPU nodes, run:"
echo "kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml"

# Clean up temp files
rm -f /tmp/node-trust-policy.json

echo "✅ Script completed successfully!"
