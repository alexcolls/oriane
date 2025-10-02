#!/bin/bash
# Script to get EKS cluster and node role names from AWS CLI

set -e

# Set your variables
CLUSTER_NAME="oriane-pipeline-api-cluster"  # Update with your cluster name
REGION="us-east-1"                      # Update with your region

echo "🔍 Fetching EKS cluster and node information for: $CLUSTER_NAME"
echo "Region: $REGION"
echo "----------------------------------------"

# Describe the cluster to get the cluster role name
echo "📋 Getting cluster role ARN..."
CLUSTER_ROLE_ARN=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.roleArn' --output text)
CLUSTER_ROLE_NAME=$(basename "$CLUSTER_ROLE_ARN")

echo "Cluster Role ARN: $CLUSTER_ROLE_ARN"
echo "Cluster Role Name: $CLUSTER_ROLE_NAME"
echo ""

# List node groups to find the node role names
echo "📋 Getting node group information..."
NODE_GROUPS=$(aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --query 'nodegroups' --output text)

if [ -z "$NODE_GROUPS" ]; then
    echo "No node groups found for cluster: $CLUSTER_NAME"
else
    echo "Node groups found: $NODE_GROUPS"
    echo ""
    
    for nodegroup in $NODE_GROUPS; do
        echo "NodeGroup: $nodegroup"
        NODE_ROLE_ARN=$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "$nodegroup" --region "$REGION" --query 'nodegroup.nodeRole' --output text)
        NODE_ROLE_NAME=$(basename "$NODE_ROLE_ARN")
        echo "  Node Role ARN: $NODE_ROLE_ARN"
        echo "  Node Role Name: $NODE_ROLE_NAME"
        echo ""
    done
fi

echo "✅ Summary - Use these values in your configuration:"
echo "CLUSTER_ROLE_NAME=$CLUSTER_ROLE_NAME"
if [ ! -z "$NODE_GROUPS" ]; then
    # Get the first node group's role name for the summary
    FIRST_NODEGROUP=$(echo $NODE_GROUPS | cut -d' ' -f1)
    FIRST_NODE_ROLE_ARN=$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "$FIRST_NODEGROUP" --region "$REGION" --query 'nodegroup.nodeRole' --output text)
    FIRST_NODE_ROLE_NAME=$(basename "$FIRST_NODE_ROLE_ARN")
    echo "NODE_ROLE_NAME=$FIRST_NODE_ROLE_NAME"
fi
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodePolicy"
