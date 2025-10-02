#!/bin/bash
# Script to deploy EKS service using AWS Fargate

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

FARGATE_ROLE_NAME="AmazonEKSFargatePodExecutionRole"

# Create IAM role for Fargate
if ! aws iam get-role --role-name "$FARGATE_ROLE_NAME"; then
  cat <<EOF > /tmp/fargate-role-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks-fargate-pods.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
  aws iam create-role --role-name "$FARGATE_ROLE_NAME" --assume-role-policy-document file:///tmp/fargate-role-policy.json
  aws iam attach-role-policy --role-name "$FARGATE_ROLE_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonEKSFargatePodExecutionRolePolicy
  echo "Fargate role created."
else
  echo "Fargate role already exists."
fi

# Create Fargate profile
if ! aws eks describe-fargate-profile --cluster-name "$CLUSTER_NAME" --region "$REGION" --fargate-profile-name "fargate-default"; then
  VPC_CONFIG=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.resourcesVpcConfig')
  SUBNET_IDS=$(echo "$VPC_CONFIG" | jq -r '.subnetIds[]' | tr '\n' ' ')
  FARGATE_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$FARGATE_ROLE_NAME"

  aws eks create-fargate-profile --cluster-name "$CLUSTER_NAME" --fargate-profile-name "fargate-default" \
    --pod-execution-role-arn "$FARGATE_ROLE_ARN" \
    --subnets $SUBNET_IDS \
    --selectors namespace=default --selectors namespace=kube-system --selectors namespace=pipeline
  echo "Fargate profile creation initiated."
else
  echo "Fargate profile already exists."
fi

# Update kubeconfig
echo "Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Deploy a test application
echo "Deploying a test application..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: pipeline
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: pipeline
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
EOF

# Wait for deployment
echo "Waiting for the application to be ready..."
kubectl wait --for=condition=ready pod -l app=nginx -n pipeline --timeout=300s

# Check pods
echo "Checking pod status..."
kubectl get pods -n pipeline -o wide

# Clean up temp files
rm -f /tmp/fargate-role-policy.json

echo "Fargate deployment completed."
