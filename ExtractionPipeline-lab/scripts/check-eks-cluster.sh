#!/bin/bash

# =============================================================================
# EKS Cluster Status Check Script
# =============================================================================
# This script checks the status of EKS clusters and provides detailed information
# =============================================================================

set -e

echo "=== EKS Cluster Status Check ==="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if AWS CLI is installed
if ! command_exists aws; then
    echo "ERROR: AWS CLI is not installed"
    exit 1
fi

# Check AWS credentials
echo "Checking AWS credentials..."
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "ERROR: AWS credentials are not configured"
    exit 1
fi

# Display AWS identity
echo "AWS Identity:"
aws sts get-caller-identity

# List all EKS clusters
echo ""
echo "=== EKS Clusters ==="
CLUSTERS=$(aws eks list-clusters --query 'clusters' --output text)

if [ -z "$CLUSTERS" ]; then
    echo "No EKS clusters found"
    exit 0
fi

echo "Found clusters: $CLUSTERS"

# Check each cluster
for cluster in $CLUSTERS; do
    echo ""
    echo "=== Cluster: $cluster ==="
    
    # Get cluster details
    echo "Cluster details:"
    aws eks describe-cluster --name "$cluster" --query 'cluster.{Status:status,Version:version,Endpoint:endpoint,CreatedAt:createdAt}' --output table
    
    # Get node groups
    echo ""
    echo "Node groups:"
    NODEGROUPS=$(aws eks list-nodegroups --cluster-name "$cluster" --query 'nodegroups' --output text)
    
    if [ -z "$NODEGROUPS" ]; then
        echo "No node groups found"
    else
        for nodegroup in $NODEGROUPS; do
            echo "  - $nodegroup"
            aws eks describe-nodegroup --cluster-name "$cluster" --nodegroup-name "$nodegroup" --query 'nodegroup.{Status:status,InstanceTypes:instanceTypes,DesiredSize:scalingConfig.desiredSize}' --output table
        done
    fi
    
    # Check if cluster is accessible via kubectl
    echo ""
    echo "Checking kubectl access..."
    if kubectl cluster-info --context "arn:aws:eks:$(aws configure get region):$(aws sts get-caller-identity --query Account --output text):cluster/$cluster" >/dev/null 2>&1; then
        echo "✓ Cluster is accessible via kubectl"
        
        # Get nodes
        echo "Nodes:"
        kubectl get nodes --context "arn:aws:eks:$(aws configure get region):$(aws sts get-caller-identity --query Account --output text):cluster/$cluster" -o wide
        
        # Get running pods
        echo ""
        echo "Running pods:"
        kubectl get pods --all-namespaces --context "arn:aws:eks:$(aws configure get region):$(aws sts get-caller-identity --query Account --output text):cluster/$cluster"
        
    else
        echo "✗ Cluster is not accessible via kubectl"
        echo "Run: aws eks update-kubeconfig --name $cluster"
    fi
done

echo ""
echo "=== Current kubectl context ==="
kubectl config current-context

echo ""
echo "=== Available contexts ==="
kubectl config get-contexts
