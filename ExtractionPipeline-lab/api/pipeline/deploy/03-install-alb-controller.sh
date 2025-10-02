#!/bin/bash

# Script: 03-install-alb-controller.sh
# Description: Installs/updates the AWS Load Balancer Controller via Helm


set -e

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

# Check required environment variables
if [ -z "$K8S_NAMESPACE" ]; then
    echo "Error: K8S_NAMESPACE environment variable is not set"
    exit 1
fi

if [ -z "$CLUSTER_NAME" ]; then
    echo "Error: CLUSTER_NAME environment variable is not set"
    exit 1
fi

if [ -z "$AWS_REGION" ]; then
    echo "Error: AWS_REGION environment variable is not set"
    exit 1
fi

if [ -z "$ALB_VERSION" ]; then
    echo "Error: ALB_VERSION environment variable is not set"
    exit 1
fi

echo "Installing/updating AWS Load Balancer Controller..."
echo "Cluster: $CLUSTER_NAME"
echo "Namespace: $K8S_NAMESPACE"
echo "Region: $AWS_REGION"
echo "ALB Version: $ALB_VERSION"

# Add the EKS Helm repository
echo "Adding EKS Helm repository..."
helm repo add eks https://aws.github.io/eks-charts

# Update Helm repositories
echo "Updating Helm repositories..."
helm repo update

# Install/upgrade the AWS Load Balancer Controller
echo "Installing/upgrading AWS Load Balancer Controller..."
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace $K8S_NAMESPACE \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=$AWS_REGION \
  --version $ALB_VERSION

# Wait for deployment rollout
echo "Waiting for deployment rollout..."
kubectl rollout status deployment/aws-load-balancer-controller -n $K8S_NAMESPACE

echo "AWS Load Balancer Controller installation/update completed successfully!"
