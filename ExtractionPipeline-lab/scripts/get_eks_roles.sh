#!/bin/bash
# Script to retrieve EKS cluster and node role names from AWS

set -e

CLUSTER_NAME="oriane-pipeline-cluster"  # Update with your cluster name
REGION="us-east-1"                      # Update with your region

echo "🔍 Fetching EKS cluster and node information..."

# Get cluster info
echo "📋 Cluster Information:"
aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.roleArn' --output text

# Get node groups
echo "📋 Node Groups:"
aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --query 'nodegroups' --output table

# Get specific nodegroup roles
echo "📋 Node Group Roles:"
NODE_GROUPS=$(aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --query 'nodegroups' --output text)

for nodegroup in $NODE_GROUPS; do
    echo "NodeGroup: $nodegroup"
    aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "$nodegroup" --region "$REGION" --query 'nodegroup.nodeRole' --output text
done

# Get IAM roles that match EKS patterns
echo "📋 Related IAM Roles:"
aws iam list-roles --query 'Roles[?contains(RoleName, `eks`) || contains(RoleName, `EKS`) || contains(RoleName, `node`) || contains(RoleName, `cluster`)].RoleName' --output table

# Get policies attached to cluster service role
CLUSTER_ROLE_ARN=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.roleArn' --output text)
CLUSTER_ROLE_NAME=$(basename "$CLUSTER_ROLE_ARN")

echo "📋 Policies attached to cluster role ($CLUSTER_ROLE_NAME):"
aws iam list-attached-role-policies --role-name "$CLUSTER_ROLE_NAME" --query 'AttachedPolicies[].PolicyName' --output table

echo "✅ Done! Use these values in your configuration:"
echo "CLUSTER_ROLE_NAME=$CLUSTER_ROLE_NAME"
echo "NODE_ROLE_NAME=<check the node group roles above>"
echo "CLUSTER_POLICY_NAME=<check the attached policies above>"
echo "NODE_POLICY_NAME=<typically AmazonEKSWorkerNodePolicy, AmazonEKS_CNI_Policy, etc>"
