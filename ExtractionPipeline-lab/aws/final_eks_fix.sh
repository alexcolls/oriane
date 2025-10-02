#!/bin/bash
# Final fix for EKS deployment with managed node groups

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🔧 Final EKS Deployment Fix"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Account ID: $ACCOUNT_ID"
echo "============================"

# Use the older AMI type that works with public subnets
echo "📋 Creating working node group with AL2 AMI..."

# Get subnet info
VPC_CONFIG=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.resourcesVpcConfig')
SUBNET_IDS=$(echo "$VPC_CONFIG" | jq -r '.subnetIds[]' | tr '\n' ' ')
NODE_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/AmazonEKSAutoNodeRole"

echo "Subnets: $SUBNET_IDS"
echo "Node Role: $NODE_ROLE_ARN"

# Create a simple working node group with AL2 AMI
echo "📋 Creating basic node group..."
aws eks create-nodegroup \
    --cluster-name "$CLUSTER_NAME" \
    --nodegroup-name "basic-nodes" \
    --region "$REGION" \
    --subnets $SUBNET_IDS \
    --instance-types "t3.medium" \
    --node-role "$NODE_ROLE_ARN" \
    --scaling-config minSize=1,maxSize=3,desiredSize=2 \
    --disk-size 20 \
    --ami-type AL2_x86_64 \
    --remote-access ec2SshKey=your-key-name,sourceSecurityGroups=sg-12345678

echo "✅ Basic node group creation started"

# Wait for node group to be active
echo "📋 Waiting for node group to be active..."
while true; do
    STATUS=$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "basic-nodes" --region "$REGION" --query 'nodegroup.status' --output text)
    echo "  [basic-nodes] Status: $STATUS"
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ Node group is active!"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "❌ Node group failed to create!"
        aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "basic-nodes" --region "$REGION" --query 'nodegroup.health.issues' --output table
        exit 1
    fi
    
    sleep 30
done

# Update kubeconfig
echo "📋 Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Test the deployment
echo "📋 Testing deployment..."
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
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
EOF

echo "✅ Test deployment created"

# Wait for pods to be ready
echo "📋 Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=test-app -n pipeline --timeout=300s

echo "📋 Checking deployment..."
kubectl get nodes -o wide
kubectl get pods -n pipeline -o wide

echo "🎉 EKS deployment fixed successfully!"
echo "============================"

echo "📋 Your EKS configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodeMinimalPolicy"

echo "📋 EKS is now ready for deployment!"
echo "- Cluster: $CLUSTER_NAME"
echo "- Region: $REGION"
echo "- Compute: Managed Node Groups"
echo "- Namespace: pipeline"

echo "✅ EKS service fixed and ready!"
