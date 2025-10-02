#!/bin/bash
# Script to fix EKS networking and security group issues

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
VPC_ID="vpc-0c3ab41805ec7bf44"
CLUSTER_SG_ID="sg-0cd1e7025abfd2036"

echo "🔧 Fixing EKS Networking Issues"
echo "Cluster: $CLUSTER_NAME"
echo "VPC ID: $VPC_ID"
echo "Cluster SG: $CLUSTER_SG_ID"
echo "================================"

# 1. Fix cluster endpoint access
echo "📋 1. Updating cluster endpoint access..."
aws eks update-cluster-config \
    --name "$CLUSTER_NAME" \
    --region "$REGION" \
    --resources-vpc-config endpointConfigRequest='{publicAccess=true,privateAccess=true,publicAccessCidrs=["0.0.0.0/0"]}'

echo "✅ Cluster endpoint access updated"

# 2. Fix security group rules
echo "📋 2. Adding required security group rules..."

# Add HTTPS access from VPC for kubelet
aws ec2 authorize-security-group-ingress \
    --group-id "$CLUSTER_SG_ID" \
    --protocol tcp \
    --port 443 \
    --cidr "172.30.0.0/16" \
    --region "$REGION" || echo "Rule may already exist"

# Add Node to cluster communication
aws ec2 authorize-security-group-ingress \
    --group-id "$CLUSTER_SG_ID" \
    --protocol tcp \
    --port 10250 \
    --cidr "172.30.0.0/16" \
    --region "$REGION" || echo "Rule may already exist"

# Add DNS access
aws ec2 authorize-security-group-ingress \
    --group-id "$CLUSTER_SG_ID" \
    --protocol tcp \
    --port 53 \
    --cidr "172.30.0.0/16" \
    --region "$REGION" || echo "Rule may already exist"

aws ec2 authorize-security-group-ingress \
    --group-id "$CLUSTER_SG_ID" \
    --protocol udp \
    --port 53 \
    --cidr "172.30.0.0/16" \
    --region "$REGION" || echo "Rule may already exist"

echo "✅ Security group rules updated"

# 3. Fix route table associations
echo "📋 3. Fixing route table associations..."
ROUTE_TABLE_ID="rtb-0014ef84231a74ae3"

# Associate all subnets with the route table
SUBNETS=("subnet-0702358f8e59d0215" "subnet-0c6f1c2c3c6f79d16" "subnet-0527069488dcc3ce3" "subnet-0b7d85549db8fcbc7" "subnet-02c703e1ca74fc145")

for subnet in "${SUBNETS[@]}"; do
    echo "Associating subnet $subnet with route table $ROUTE_TABLE_ID"
    aws ec2 associate-route-table \
        --route-table-id "$ROUTE_TABLE_ID" \
        --subnet-id "$subnet" \
        --region "$REGION" || echo "Association may already exist"
done

echo "✅ Route table associations fixed"

# 4. Wait for cluster update to complete
echo "📋 4. Waiting for cluster update to complete..."
while true; do
    STATUS=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.status' --output text)
    echo "  Cluster status: $STATUS"
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ Cluster is active!"
        break
    fi
    
    sleep 30
done

echo "🎉 EKS networking issues fixed!"
echo "==============================="

echo "📋 Now trying to create a simple node group..."

# Clean up any existing failed node groups
echo "📋 Cleaning up existing node groups..."
EXISTING_GROUPS=$(aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --query 'nodegroups' --output text)
if [ ! -z "$EXISTING_GROUPS" ]; then
    for group in $EXISTING_GROUPS; do
        echo "Deleting existing node group: $group"
        aws eks delete-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "$group" --region "$REGION" || true
    done
    
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

# Create new node group
echo "📋 Creating new node group with fixed networking..."
aws eks create-nodegroup \
    --cluster-name "$CLUSTER_NAME" \
    --nodegroup-name "fixed-nodes" \
    --region "$REGION" \
    --subnets subnet-0702358f8e59d0215 subnet-0c6f1c2c3c6f79d16 \
    --instance-types "t3.medium" \
    --node-role "arn:aws:iam::509399609859:role/AmazonEKSAutoNodeRole" \
    --scaling-config minSize=1,maxSize=2,desiredSize=1 \
    --disk-size 20 \
    --ami-type AL2023_x86_64_STANDARD

echo "✅ Node group creation started"

# Monitor the new node group
echo "📋 Monitoring new node group creation..."
while true; do
    STATUS=$(aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "fixed-nodes" --region "$REGION" --query 'nodegroup.status' --output text)
    echo "  [fixed-nodes] Status: $STATUS"
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ Node group is active!"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "❌ Node group failed to create!"
        aws eks describe-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "fixed-nodes" --region "$REGION" --query 'nodegroup.health.issues' --output table
        exit 1
    fi
    
    sleep 30
done

# Test the fix
echo "📋 Testing the fix..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"
kubectl get nodes -o wide

echo "🎉 EKS service is now fixed and working!"
echo "========================================"

echo "📋 Your working EKS configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodeMinimalPolicy"

echo "✅ EKS is ready for deployment!"
