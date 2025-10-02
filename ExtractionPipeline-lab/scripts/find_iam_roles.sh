#!/bin/bash

echo "=== Finding EKS Cluster IAM Roles ==="

# Method 1: List all EKS clusters first
echo "1. Listing EKS clusters:"
aws eks list-clusters --query 'clusters[]' --output table

# Method 2: Find IAM roles with EKS-related names
echo -e "\n2. Finding IAM roles with EKS/cluster-related names:"
aws iam list-roles --query 'Roles[?contains(RoleName, `eks`) || contains(RoleName, `cluster`) || contains(RoleName, `node`)].{RoleName:RoleName, Path:Path}' --output table

# Method 3: Find roles with specific service principals (EKS and EC2)
echo -e "\n3. Finding roles with EKS service principals:"
aws iam list-roles --query 'Roles[?contains(AssumeRolePolicyDocument, `eks.amazonaws.com`)].{RoleName:RoleName, Path:Path}' --output table

echo -e "\n4. Finding roles with EC2 service principals (likely node roles):"
aws iam list-roles --query 'Roles[?contains(AssumeRolePolicyDocument, `ec2.amazonaws.com`)].{RoleName:RoleName, Path:Path}' --output table

# Method 4: Get detailed cluster info if cluster name is known
echo -e "\n5. If you know your cluster name, run:"
echo "   aws eks describe-cluster --name YOUR_CLUSTER_NAME --query 'cluster.roleArn'"
echo "   aws eks describe-nodegroup --cluster-name YOUR_CLUSTER_NAME --nodegroup-name YOUR_NODEGROUP_NAME --query 'nodegroup.nodeRole'"

# Method 5: Check for managed policies attached to roles
echo -e "\n6. Common EKS managed policies to look for:"
echo "   - AmazonEKSClusterPolicy (attached to cluster role)"
echo "   - AmazonEKSWorkerNodePolicy (attached to node role)"
echo "   - AmazonEKS_CNI_Policy (attached to node role)"
echo "   - AmazonEC2ContainerRegistryReadOnly (attached to node role)"

echo -e "\n=== Instructions ==="
echo "After running this script, look for:"
echo "- Cluster Role: Usually has 'eks', 'cluster' in the name with EKS service principal"
echo "- Node Role: Usually has 'node', 'worker' in the name with EC2 service principal"
echo "- Policy Names: Check attached policies with 'aws iam list-attached-role-policies --role-name ROLE_NAME'"
