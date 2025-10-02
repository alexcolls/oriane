#!/bin/bash

# Final EKS Node Group Fix Script
# This script creates a working node group with proper security group configuration

set -e

echo "=== Final EKS Node Group Fix ==="
echo "Starting at $(date)"

# Configuration
CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"

echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo

# Step 1: Get cluster information
echo "=== Step 1: Gathering cluster information ==="
CLUSTER_INFO=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION)
CLUSTER_ENDPOINT=$(echo $CLUSTER_INFO | jq -r '.cluster.endpoint')
CLUSTER_VERSION=$(echo $CLUSTER_INFO | jq -r '.cluster.version')
VPC_ID=$(echo $CLUSTER_INFO | jq -r '.cluster.resourcesVpcConfig.vpcId')
SUBNET_IDS=$(echo $CLUSTER_INFO | jq -r '.cluster.resourcesVpcConfig.subnetIds[]' | tr '\n' ' ')
CLUSTER_SECURITY_GROUP_ID=$(echo $CLUSTER_INFO | jq -r '.cluster.resourcesVpcConfig.clusterSecurityGroupId')

echo "Cluster Endpoint: $CLUSTER_ENDPOINT"
echo "Cluster Version: $CLUSTER_VERSION"
echo "VPC ID: $VPC_ID"
echo "Subnet IDs: $SUBNET_IDS"
echo "Cluster Security Group ID: $CLUSTER_SECURITY_GROUP_ID"
echo

# Step 2: Create IAM role for nodes
echo "=== Step 2: Setting up IAM role for nodes ==="
NODE_ROLE_NAME="EKS-Final-NodeGroup-Role-$(date +%s)"
ASSUME_ROLE_POLICY_DOCUMENT='{
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
}'

# Create IAM role
echo "Creating IAM role: $NODE_ROLE_NAME"
aws iam create-role \
    --role-name $NODE_ROLE_NAME \
    --assume-role-policy-document "$ASSUME_ROLE_POLICY_DOCUMENT" || echo "Role might already exist"

# Attach required policies
echo "Attaching required policies to IAM role..."
aws iam attach-role-policy \
    --role-name $NODE_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy

aws iam attach-role-policy \
    --role-name $NODE_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy

aws iam attach-role-policy \
    --role-name $NODE_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

# Additional policy for SSM (for debugging)
aws iam attach-role-policy \
    --role-name $NODE_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore

echo "✓ IAM role setup completed"
echo

# Step 3: Wait for IAM propagation
echo "=== Step 3: Waiting for IAM propagation ==="
echo "Waiting 60 seconds for IAM changes to propagate..."
sleep 60

# Step 4: Create new node group with proper security group
echo "=== Step 4: Creating new node group with proper security group ==="
NEW_NODE_GROUP_NAME="final-nodes-$(date +%Y%m%d-%H%M%S)"

# Get node role ARN
NODE_ROLE_ARN=$(aws iam get-role --role-name $NODE_ROLE_NAME --query 'Role.Arn' --output text)

echo "Creating node group: $NEW_NODE_GROUP_NAME"
echo "Node Role ARN: $NODE_ROLE_ARN"
echo "Using cluster security group: $CLUSTER_SECURITY_GROUP_ID"

# Create node group using just the first 2 subnets and the cluster security group
aws eks create-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NEW_NODE_GROUP_NAME \
    --scaling-config minSize=1,maxSize=3,desiredSize=2 \
    --instance-types t3.medium \
    --ami-type AL2023_x86_64_STANDARD \
    --node-role $NODE_ROLE_ARN \
    --subnets $(echo $SUBNET_IDS | tr ' ' '\n' | head -2 | tr '\n' ' ') \
    --region $REGION

echo "✓ Node group creation initiated"
echo

# Step 5: Wait for node group to be active
echo "=== Step 5: Waiting for node group to become active ==="
echo "This may take 10-15 minutes..."

# Monitor the node group creation
echo "Monitoring node group creation..."
for i in {1..30}; do
    STATUS=$(aws eks describe-nodegroup \
        --cluster-name $CLUSTER_NAME \
        --nodegroup-name $NEW_NODE_GROUP_NAME \
        --region $REGION \
        --query 'nodegroup.status' \
        --output text)
    
    echo "Attempt $i: Node group status: $STATUS"
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✓ Node group is now active"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "✗ Node group creation failed. Checking details..."
        aws eks describe-nodegroup \
            --cluster-name $CLUSTER_NAME \
            --nodegroup-name $NEW_NODE_GROUP_NAME \
            --region $REGION \
            --query 'nodegroup.health.issues'
        exit 1
    elif [ "$STATUS" = "DELETING" ]; then
        echo "✗ Node group is being deleted"
        exit 1
    fi
    
    sleep 30
done

if [ "$STATUS" != "ACTIVE" ]; then
    echo "✗ Node group did not become active within expected time"
    exit 1
fi

echo

# Step 6: Update kubeconfig
echo "=== Step 6: Updating kubeconfig ==="
aws eks update-kubeconfig \
    --region $REGION \
    --name $CLUSTER_NAME

echo "✓ Kubeconfig updated"
echo

# Step 7: Verify nodes joined the cluster
echo "=== Step 7: Verifying nodes joined the cluster ==="
echo "Waiting 30 seconds for nodes to register..."
sleep 30

echo "Checking nodes in cluster:"
kubectl get nodes -o wide

echo
echo "=== Node Group Status ==="
aws eks describe-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NEW_NODE_GROUP_NAME \
    --region $REGION \
    --query 'nodegroup.{Status:status,Health:health,CreatedAt:createdAt}' \
    --output table

echo
echo "=== EC2 Instances Status ==="
aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
    --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,Type:InstanceType,LaunchTime:LaunchTime}' \
    --output table

echo
echo "=== Pods Status ==="
kubectl get pods --all-namespaces -o wide

echo
echo "=== Fix Complete ==="
echo "New node group: $NEW_NODE_GROUP_NAME"
echo "IAM role: $NODE_ROLE_NAME"
echo "Cluster security group: $CLUSTER_SECURITY_GROUP_ID"
echo

echo "If nodes still don't join, check:"
echo "1. VPC DNS resolution and DNS hostnames are enabled ✓"
echo "2. Subnets have internet access (via IGW or NAT) ✓"
echo "3. Security groups allow required traffic ✓"
echo "4. IAM roles have correct policies ✓"
echo "5. Consider using a launch template for more control"
echo
echo "Completed at $(date)"
