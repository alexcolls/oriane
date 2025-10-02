#!/bin/bash
# Script to monitor EKS deployment and troubleshoot issues

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"

echo "🔍 Monitoring EKS Deployment"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "==========================="

# Update kubeconfig
echo "📋 Updating kubeconfig..."
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

# Check cluster status
echo "📋 1. Cluster Status:"
aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.{Status:status,Version:version,Endpoint:endpoint}' --output table

# Check node groups
echo "📋 2. Node Groups:"
aws eks list-nodegroups --cluster-name "$CLUSTER_NAME" --region "$REGION" --output table

# Check nodes
echo "📋 3. Kubernetes Nodes:"
kubectl get nodes -o wide || echo "No nodes available"

# Check system pods
echo "📋 4. System Pods:"
kubectl get pods -n kube-system || echo "Cannot retrieve system pods"

# Check all namespaces
echo "📋 5. All Namespaces:"
kubectl get namespaces

# Check pipeline namespace
echo "📋 6. Pipeline Namespace Resources:"
kubectl get all -n pipeline 2>/dev/null || echo "Pipeline namespace not found or empty"

# Check events
echo "📋 7. Recent Events:"
kubectl get events --all-namespaces --sort-by=.metadata.creationTimestamp | tail -20

# Check if we can schedule a simple pod
echo "📋 8. Testing Pod Scheduling:"
kubectl run test-pod --image=nginx --restart=Never --dry-run=client -o yaml | kubectl apply -f - || echo "Cannot create test pod"

# Wait a bit and check test pod
sleep 10
kubectl get pod test-pod -o wide 2>/dev/null || echo "Test pod not found"

# Check pod events
kubectl describe pod test-pod 2>/dev/null | grep -A10 "Events:" || echo "No events for test pod"

# Clean up test pod
kubectl delete pod test-pod 2>/dev/null || echo "Test pod cleanup not needed"

# Check EKS add-ons
echo "📋 9. EKS Add-ons:"
aws eks list-addons --cluster-name "$CLUSTER_NAME" --region "$REGION" --output table

# Check security groups
echo "📋 10. Security Groups:"
aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.resourcesVpcConfig.{ClusterSecurityGroupId:clusterSecurityGroupId,SecurityGroupIds:securityGroupIds}' --output table

# Check endpoint access
echo "📋 11. Endpoint Access:"
aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query 'cluster.resourcesVpcConfig.{PublicAccess:endpointConfigResponse.publicAccess,PrivateAccess:endpointConfigResponse.privateAccess}' --output table

# Summary
echo "📋 12. Summary:"
echo "=============="

# Count resources
NODES=$(kubectl get nodes --no-headers 2>/dev/null | wc -l)
PODS=$(kubectl get pods --all-namespaces --no-headers 2>/dev/null | wc -l)
SERVICES=$(kubectl get services --all-namespaces --no-headers 2>/dev/null | wc -l)

echo "- Nodes: $NODES"
echo "- Pods: $PODS"
echo "- Services: $SERVICES"

if [ "$NODES" -eq 0 ]; then
    echo "❌ No nodes available - pods cannot be scheduled"
    echo "   Recommendation: Fix node group issues or use Fargate"
else
    echo "✅ Nodes available - cluster is functional"
fi

if [ "$PODS" -gt 0 ]; then
    echo "✅ Pods are running"
else
    echo "⚠️  No pods running"
fi

echo "📋 Troubleshooting Steps:"
echo "1. If no nodes: Check node group status with AWS console"
echo "2. If pods pending: Check events and resource constraints"
echo "3. If networking issues: Verify security groups and VPC config"
echo "4. Alternative: Use Fargate for serverless compute"

echo "📋 Your EKS Configuration:"
echo "CLUSTER_ROLE_NAME=AmazonEKSAutoClusterRole"
echo "NODE_ROLE_NAME=AmazonEKSAutoNodeRole"
echo "CLUSTER_POLICY_NAME=PipelineApiPolicy"
echo "NODE_POLICY_NAME=AmazonEKSWorkerNodeMinimalPolicy"

echo "✅ Monitoring completed!"
