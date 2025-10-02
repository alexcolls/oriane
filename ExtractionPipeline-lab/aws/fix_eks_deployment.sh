#!/bin/bash
# Script to fix EKS deployment with Fargate profile

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🔧 Fixing EKS Deployment with Fargate"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Account ID: $ACCOUNT_ID"
echo "======================================"

# Clean up any existing failed node groups
echo "📋 Cleaning up existing node groups..."
NODEGROUPS=$(aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --query 'nodegroups' --output text)
if [ ! -z "$NODEGROUPS" ]; then
    echo "Found existing node groups: $NODEGROUPS"
    for nodegroup in $NODEGROUPS; do
        echo "Deleting node group: $nodegroup"
        aws eks delete-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "$nodegroup" --region "$REGION" || true
    done
    
    # Wait for deletion
    echo "⏳ Waiting for node groups to be deleted..."
    while true; do
        REMAINING=$(aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --query 'nodegroups' --output text)
        if [ -z "$REMAINING" ]; then
            echo "✅ All node groups deleted"
            break
        fi
        echo "Still deleting: $REMAINING"
        sleep 30
    done
fi

# Create IAM role for Fargate
echo "📋 Creating IAM role for Fargate..."
FARGATE_ROLE_NAME="AmazonEKSFargatePodExecutionRole"

# Check if role exists
if aws iam get-role --role-name "$FARGATE_ROLE_NAME" >/dev/null 2>&1; then
    echo "✅ Fargate role already exists"
else
    echo "🔧 Creating Fargate IAM role..."
    
    # Create trust policy for Fargate
    cat > /tmp/fargate-trust-policy.json << EOF
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

    # Create IAM role
    aws iam create-role \
        --role-name "$FARGATE_ROLE_NAME" \
        --assume-role-policy-document file:///tmp/fargate-trust-policy.json
    
    # Attach required policy
    aws iam attach-role-policy \
        --policy-arn arn:aws:iam::aws:policy/AmazonEKSFargatePodExecutionRolePolicy \
        --role-name "$FARGATE_ROLE_NAME"
    
    echo "✅ Created Fargate IAM role"
fi

FARGATE_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$FARGATE_ROLE_NAME"

# Get private subnets for Fargate
echo "📋 Getting private subnets for Fargate..."
VPC_CONFIG=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.resourcesVpcConfig')
ALL_SUBNETS=$(echo "$VPC_CONFIG" | jq -r '.subnetIds[]')

# Find private subnets (those with route to NAT Gateway)
PRIVATE_SUBNETS=""
for subnet in $ALL_SUBNETS; do
    # Check if subnet is private by looking for NAT gateway routes
    ROUTE_TABLE=$(aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=$subnet" --region "$REGION" --query 'RouteTables[0].RouteTableId' --output text)
    if [ "$ROUTE_TABLE" != "None" ]; then
        NAT_ROUTES=$(aws ec2 describe-route-tables --route-table-ids "$ROUTE_TABLE" --region "$REGION" --query 'RouteTables[0].Routes[?GatewayId && starts_with(GatewayId, `nat-`)].GatewayId' --output text)
        if [ ! -z "$NAT_ROUTES" ]; then
            PRIVATE_SUBNETS="$PRIVATE_SUBNETS $subnet"
        fi
    fi
done

# If no private subnets found, use first two subnets
if [ -z "$PRIVATE_SUBNETS" ]; then
    PRIVATE_SUBNETS=$(echo "$ALL_SUBNETS" | head -2 | tr '\n' ' ')
    echo "⚠️  No private subnets detected, using first two subnets"
fi

echo "Private subnets for Fargate: $PRIVATE_SUBNETS"

# Create Fargate profile
echo "📋 Creating Fargate profile..."
aws eks create-fargate-profile \
    --fargate-profile-name default \
    --cluster-name "$CLUSTER_NAME" \
    --pod-execution-role-arn "$FARGATE_ROLE_ARN" \
    --subnets $PRIVATE_SUBNETS \
    --selectors namespace=default \
    --selectors namespace=kube-system \
    --selectors namespace=pipeline \
    --region "$REGION"

echo "✅ Fargate profile creation started"

# Wait for Fargate profile to be active
echo "📋 Waiting for Fargate profile to be active..."
while true; do
    STATUS=$(aws eks describe-fargate-profile --cluster-name "$CLUSTER_NAME" --fargate-profile-name default --region "$REGION" --query 'fargateProfile.status' --output text)
    echo "  [Fargate Profile] Status: $STATUS"
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ Fargate profile is active!"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "❌ Fargate profile failed to create!"
        exit 1
    fi
    
    sleep 30
done

# Update kubeconfig
echo "📋 Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Test deployment
echo "📋 Testing deployment with a simple pod..."
kubectl apply -f - << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: pipeline
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
  namespace: pipeline
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: test-container
        image: nginx:latest
        ports:
        - containerPort: 80
EOF

echo "✅ Test deployment created"

# Wait for pods to be ready
echo "📋 Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=test-app -n pipeline --timeout=300s

echo "📋 Checking pods..."
kubectl get pods -n pipeline -o wide

echo "🎉 EKS deployment fixed successfully!"
echo "======================================"

echo "📋 Your EKS configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "FARGATE_ROLE_NAME=AmazonEKSFargatePodExecutionRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "FARGATE_POLICY_NAME=AmazonEKSFargatePodExecutionRolePolicy"

echo "📋 EKS is now ready for deployment!"
echo "- Cluster: $CLUSTER_NAME"
echo "- Region: $REGION"
echo "- Compute: AWS Fargate"
echo "- Namespaces: default, kube-system, pipeline"

echo "📋 Next steps:"
echo "1. Deploy your pipeline application to the 'pipeline' namespace"
echo "2. All pods will run on Fargate serverless compute"
echo "3. No need for GPU nodes - Fargate handles compute automatically"

# Clean up temp files
rm -f /tmp/fargate-trust-policy.json

echo "✅ EKS service fixed and ready!"
