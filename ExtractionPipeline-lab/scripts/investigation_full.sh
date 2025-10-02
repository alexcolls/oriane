#!/bin/bash

# EKS Cluster Full Investigation Script
# Author: AI Assistant
# Date: 2025-07-11
# Purpose: Complete investigation of EKS cluster issues with detailed documentation

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
NODEGROUP_NAME="working-nodes-v2"
LOG_FILE="/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/investigation_$(date +%Y%m%d_%H%M%S).log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to run command and log output
run_and_log() {
    local cmd="$1"
    local description="$2"
    
    log "🔍 $description"
    log "Command: $cmd"
    log "----------------------------------------"
    
    if eval "$cmd" 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Command completed successfully"
    else
        log "❌ Command failed with exit code $?"
    fi
    log "=========================================="
    echo "" | tee -a "$LOG_FILE"
}

log "🚀 Starting EKS Cluster Full Investigation"
log "Cluster: $CLUSTER_NAME"
log "Region: $REGION"
log "Node Group: $NODEGROUP_NAME"
log "Log File: $LOG_FILE"

# 1. Cluster Status
run_and_log "aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.{Name:name,Status:status,Version:version,Endpoint:endpoint,Platform:platformVersion}' --output json" "Checking cluster basic status"

# 2. Node Group Status
run_and_log "aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $NODEGROUP_NAME --region $REGION --output json" "Checking node group detailed status"

# 3. All Node Groups
run_and_log "aws eks list-nodegroups --cluster-name $CLUSTER_NAME --region $REGION --output json" "Listing all node groups"

# 4. Kubernetes Configuration
run_and_log "kubectl config current-context" "Checking current kubectl context"

# 5. Kubernetes Nodes
run_and_log "kubectl get nodes -o wide" "Checking registered Kubernetes nodes"

# 6. Kubernetes Events
run_and_log "kubectl get events --sort-by=.metadata.creationTimestamp -A" "Checking Kubernetes events"

# 7. Pod Status
run_and_log "kubectl get pods -A" "Checking all pods status"

# 8. Check VPC Configuration
VPC_CONFIG=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.resourcesVpcConfig' --output json)
SUBNET_IDS=$(echo "$VPC_CONFIG" | jq -r '.subnetIds[]')
VPC_ID=$(echo "$VPC_CONFIG" | jq -r '.vpcId')

log "🔍 VPC Configuration Analysis"
log "VPC ID: $VPC_ID"
log "Subnet IDs: $SUBNET_IDS"

# 9. Check Subnets
for subnet_id in $SUBNET_IDS; do
    run_and_log "aws ec2 describe-subnets --subnet-ids $subnet_id --region $REGION --query 'Subnets[0].{SubnetId:SubnetId,VpcId:VpcId,CidrBlock:CidrBlock,AvailabilityZone:AvailabilityZone,MapPublicIpOnLaunch:MapPublicIpOnLaunch}' --output json" "Checking subnet $subnet_id"
done

# 10. Check Security Groups
SECURITY_GROUPS=$(echo "$VPC_CONFIG" | jq -r '.securityGroupIds[]')
for sg_id in $SECURITY_GROUPS; do
    run_and_log "aws ec2 describe-security-groups --group-ids $sg_id --region $REGION --query 'SecurityGroups[0].{GroupId:GroupId,GroupName:GroupName,Description:Description}' --output json" "Checking security group $sg_id"
done

# 11. Check IAM Role for Node Group
NODE_ROLE=$(aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $NODEGROUP_NAME --region $REGION --query 'nodegroup.nodeRole' --output text)
run_and_log "aws iam get-role --role-name $(basename $NODE_ROLE) --query 'Role.{RoleName:RoleName,Arn:Arn}' --output json" "Checking node group IAM role"

# 12. Check attached policies
run_and_log "aws iam list-attached-role-policies --role-name $(basename $NODE_ROLE) --output json" "Checking attached policies for node role"

# 13. Check Auto Scaling Group
ASG_NAME=$(aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $NODEGROUP_NAME --region $REGION --query 'nodegroup.resources.autoScalingGroups[0].name' --output text)
if [ "$ASG_NAME" != "None" ] && [ "$ASG_NAME" != "" ]; then
    run_and_log "aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names $ASG_NAME --region $REGION --query 'AutoScalingGroups[0].{GroupName:AutoScalingGroupName,MinSize:MinSize,MaxSize:MaxSize,DesiredCapacity:DesiredCapacity,Instances:Instances}' --output json" "Checking Auto Scaling Group"
fi

# 14. Check CloudWatch Logs
log "🔍 Checking CloudWatch Log Groups"
run_and_log "aws logs describe-log-groups --log-group-name-prefix /aws/eks/$CLUSTER_NAME --region $REGION --query 'logGroups[].logGroupName' --output json" "Listing EKS log groups"

# 15. Check recent CloudWatch logs
LOG_GROUPS=$(aws logs describe-log-groups --log-group-name-prefix /aws/eks/$CLUSTER_NAME --region $REGION --query 'logGroups[].logGroupName' --output text)
for log_group in $LOG_GROUPS; do
    log "📋 Recent logs from $log_group"
    run_and_log "aws logs describe-log-streams --log-group-name $log_group --region $REGION --order-by LastEventTime --descending --max-items 3 --query 'logStreams[].logStreamName' --output text | head -1 | xargs -I {} aws logs get-log-events --log-group-name $log_group --log-stream-name {} --region $REGION --limit 50 --query 'events[].message' --output text | tail -20" "Latest 20 log entries from $log_group"
done

# 16. Check EC2 Instances
run_and_log "aws ec2 describe-instances --filters 'Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned' --region $REGION --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,LaunchTime:LaunchTime,InstanceType:InstanceType,SubnetId:SubnetId}' --output json" "Checking EC2 instances for the cluster"

# 17. Check Launch Template
LAUNCH_TEMPLATE=$(aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $NODEGROUP_NAME --region $REGION --query 'nodegroup.launchTemplate.{Id:id,Version:version}' --output json)
if [ "$LAUNCH_TEMPLATE" != "null" ]; then
    TEMPLATE_ID=$(echo "$LAUNCH_TEMPLATE" | jq -r '.Id')
    run_and_log "aws ec2 describe-launch-templates --launch-template-ids $TEMPLATE_ID --region $REGION --query 'LaunchTemplates[0].{LaunchTemplateId:LaunchTemplateId,LaunchTemplateName:LaunchTemplateName,DefaultVersionNumber:DefaultVersionNumber}' --output json" "Checking launch template"
fi

log "🏁 Investigation completed"
log "Full log saved to: $LOG_FILE"
log "Summary of findings will be generated next..."
