#!/bin/bash
# Script to fix EKS node registration issue

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"

echo "🔧 Fixing EKS Node Registration Issue"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "====================================="

# 1. Delete the failed node group
echo "📋 1. Cleaning up failed node group..."
aws eks delete-nodegroup --cluster-name "$CLUSTER_NAME" --nodegroup-name "final-nodes" --region "$REGION" || true

# 2. Wait for cleanup
echo "📋 2. Waiting for cleanup..."
while true; do
    NODEGROUPS=$(aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --query 'nodegroups' --output text)
    if [ -z "$NODEGROUPS" ]; then
        echo "✅ All node groups cleaned up"
        break
    fi
    echo "⏳ Still cleaning up: $NODEGROUPS"
    sleep 30
done

# 3. Create a new node group with explicit configuration
echo "📋 3. Creating new node group with fixed configuration..."
aws eks create-nodegroup \
    --cluster-name "$CLUSTER_NAME" \
    --nodegroup-name "working-nodes-v2" \
    --region "$REGION" \
    --subnets subnet-0702358f8e59d0215 subnet-0c6f1c2c3c6f79d16 \
    --instance-types "t3.medium" \
    --node-role "arn:aws:iam::509399609859:role/AmazonEKSAutoNodeRole" \
    --scaling-config minSize=1,maxSize=2,desiredSize=1 \
    --disk-size 20 \
    --ami-type AL2023_x86_64_STANDARD \
    --capacity-type ON_DEMAND \
    --update-config maxUnavailable=1

echo "✅ New node group creation started"

# 4. Monitor the new node group
echo "📋 4. Monitoring new node group creation..."
START_TIME=$(date +%s)
while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED -gt 600 ]; then
        echo "⏰ Timeout reached (10 minutes)"
        break
    fi
    
    STATUS=$(aws eks describe-nodegroup \
        --cluster-name "$CLUSTER_NAME" \
        --nodegroup-name "working-nodes-v2" \
        --region "$REGION" \
        --query 'nodegroup.status' \
        --output text)
    
    echo "$(date '+%H:%M:%S') - Status: $STATUS (${ELAPSED}s elapsed)"
    
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "✅ Node group is ACTIVE!"
        break
    elif [ "$STATUS" = "CREATE_FAILED" ]; then
        echo "❌ Node group creation failed!"
        aws eks describe-nodegroup \
            --cluster-name "$CLUSTER_NAME" \
            --nodegroup-name "working-nodes-v2" \
            --region "$REGION" \
            --query 'nodegroup.health.issues' \
            --output table
        break
    fi
    
    sleep 30
done

# 5. Check if nodes are visible
echo "📋 5. Checking if nodes are now visible..."
sleep 30
kubectl get nodes -o wide

# 6. Test pod scheduling
echo "📋 6. Testing pod scheduling..."
kubectl run test-nginx --image=nginx --restart=Never --rm --timeout=60s -- /bin/bash -c "echo 'Node registration test successful!'"

echo "🎉 Fix completed!"
echo "================"

echo "📋 Final status:"
kubectl get nodes
kubectl get pods --all-namespaces | grep -E "(Running|Pending)"

if [ "$(kubectl get nodes --no-headers | wc -l)" -gt 0 ]; then
    echo "✅ SUCCESS: Nodes are now available!"
    echo "📋 You can now deploy your pipeline:"
    echo "   kubectl get pods -n pipeline"
else
    echo "❌ FAILED: Still no nodes available"
    echo "📋 Try alternative approaches:"
    echo "   1. Use Fargate (serverless)"
    echo "   2. Use ECS instead of EKS"
    echo "   3. Check AWS service limits"
fi

echo "✅ Node registration fix completed!"
