#!/bin/bash

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
NODEGROUP_NAME="fixed-nodes-20250711-153046"
REGION="us-east-1"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 Diagnosing node group: $NODEGROUP_NAME"

# Check node group status
echo "=== NODE GROUP STATUS ==="
aws eks describe-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NODEGROUP_NAME \
    --region $REGION \
    --output json

echo ""
echo "=== CLUSTER STATUS ==="
aws eks describe-cluster \
    --name $CLUSTER_NAME \
    --region $REGION \
    --query 'cluster.{Name:name,Status:status,Endpoint:endpoint,Version:version,PlatformVersion:platformVersion,NetworkConfig:resourcesVpcConfig}' \
    --output json

echo ""
echo "=== AUTO SCALING GROUPS ==="
aws autoscaling describe-auto-scaling-groups \
    --auto-scaling-group-names $(aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $NODEGROUP_NAME --region $REGION --query 'nodegroup.resources.autoScalingGroups[0].name' --output text) \
    --region $REGION \
    --query 'AutoScalingGroups[*].{Name:AutoScalingGroupName,DesiredCapacity:DesiredCapacity,MinSize:MinSize,MaxSize:MaxSize,Instances:Instances[*].{InstanceId:InstanceId,LifecycleState:LifecycleState,HealthStatus:HealthStatus}}' \
    --output json

echo ""
echo "=== EC2 INSTANCES ==="
aws ec2 describe-instances \
    --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
    --region $REGION \
    --query 'Reservations[*].Instances[*].{InstanceId:InstanceId,State:State.Name,LaunchTime:LaunchTime,InstanceType:InstanceType,SubnetId:SubnetId,SecurityGroups:SecurityGroups[*].GroupId,Tags:Tags}' \
    --output json

echo ""
echo "=== CHECKING CLUSTER NODES ==="
kubectl get nodes -o wide || echo "No nodes found in cluster"

echo ""
echo "=== CHECKING PENDING PODS ==="
kubectl get pods --all-namespaces --field-selector=status.phase=Pending || echo "No pending pods"

echo ""
echo "=== NODE GROUP HEALTH ==="
aws eks describe-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NODEGROUP_NAME \
    --region $REGION \
    --query 'nodegroup.health' \
    --output json

