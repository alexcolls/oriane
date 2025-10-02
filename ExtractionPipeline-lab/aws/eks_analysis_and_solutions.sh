#!/bin/bash

# EKS Cluster Analysis and Solutions Script
# Author: AI Assistant
# Date: 2025-07-11
# Purpose: Analyze the current EKS issues and provide specific solutions

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
FAILED_INSTANCE_ID="i-08fa7c98fcd3a8b03"
LOG_FILE="/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/eks_analysis_$(date +%Y%m%d_%H%M%S).log"

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

log "🚀 Starting EKS Cluster Analysis and Solutions"
log "Cluster: $CLUSTER_NAME"
log "Region: $REGION"
log "Failed Instance: $FAILED_INSTANCE_ID"

# 1. Check the failed instance details
log "📋 ANALYSIS 1: Failed Instance Details"
run_and_log "aws ec2 describe-instances --instance-ids $FAILED_INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].{InstanceId:InstanceId,State:State.Name,LaunchTime:LaunchTime,InstanceType:InstanceType,SubnetId:SubnetId,SecurityGroups:SecurityGroups,IamInstanceProfile:IamInstanceProfile,Tags:Tags}' --output json" "Checking failed instance details"

# 2. Check instance system logs
log "📋 ANALYSIS 2: Instance System Logs"
run_and_log "aws ec2 get-console-output --instance-id $FAILED_INSTANCE_ID --region $REGION --query 'Output' --output text | tail -50" "Getting console output for failed instance"

# 3. Check launch template details
log "📋 ANALYSIS 3: Launch Template Analysis"
LAUNCH_TEMPLATE_ID=$(aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name working-nodes-v2 --region $REGION --query 'nodegroup.launchTemplate.id' --output text)
if [ "$LAUNCH_TEMPLATE_ID" != "None" ] && [ "$LAUNCH_TEMPLATE_ID" != "" ]; then
    run_and_log "aws ec2 describe-launch-template-versions --launch-template-id $LAUNCH_TEMPLATE_ID --region $REGION --query 'LaunchTemplateVersions[0].LaunchTemplateData' --output json" "Checking launch template configuration"
fi

# 4. Check security group rules
log "📋 ANALYSIS 4: Security Group Rules"
SECURITY_GROUPS=$(aws ec2 describe-instances --instance-ids $FAILED_INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].SecurityGroups[].GroupId' --output text)
for sg_id in $SECURITY_GROUPS; do
    run_and_log "aws ec2 describe-security-groups --group-ids $sg_id --region $REGION --query 'SecurityGroups[0].{GroupId:GroupId,GroupName:GroupName,IngressRules:IpPermissions,EgressRules:IpPermissionsEgress}' --output json" "Checking security group $sg_id rules"
done

# 5. Check VPC endpoints
log "📋 ANALYSIS 5: VPC Endpoints"
VPC_ID=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.resourcesVpcConfig.vpcId' --output text)
run_and_log "aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=$VPC_ID --region $REGION --query 'VpcEndpoints[].{VpcEndpointId:VpcEndpointId,ServiceName:ServiceName,State:State}' --output json" "Checking VPC endpoints"

# 6. Check route tables
log "📋 ANALYSIS 6: Route Tables"
SUBNET_ID=$(aws ec2 describe-instances --instance-ids $FAILED_INSTANCE_ID --region $REGION --query 'Reservations[0].Instances[0].SubnetId' --output text)
run_and_log "aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=$SUBNET_ID --region $REGION --query 'RouteTables[0].Routes' --output json" "Checking route table for subnet $SUBNET_ID"

# 7. Check NAT Gateway (if any)
log "📋 ANALYSIS 7: NAT Gateway Configuration"
run_and_log "aws ec2 describe-nat-gateways --filter Name=vpc-id,Values=$VPC_ID --region $REGION --query 'NatGateways[].{NatGatewayId:NatGatewayId,State:State,SubnetId:SubnetId}' --output json" "Checking NAT gateways"

# 8. Check Internet Gateway
log "📋 ANALYSIS 8: Internet Gateway"
run_and_log "aws ec2 describe-internet-gateways --filters Name=attachment.vpc-id,Values=$VPC_ID --region $REGION --query 'InternetGateways[].{InternetGatewayId:InternetGatewayId,State:Attachments[0].State}' --output json" "Checking Internet Gateway"

# 9. Test connectivity to EKS endpoint
log "📋 ANALYSIS 9: EKS Endpoint Connectivity"
EKS_ENDPOINT=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.endpoint' --output text)
run_and_log "curl -I --connect-timeout 10 $EKS_ENDPOINT || echo 'EKS endpoint not reachable from this machine'" "Testing EKS endpoint connectivity"

# 10. Check EKS cluster configuration
log "📋 ANALYSIS 10: EKS Cluster Configuration"
run_and_log "aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.{EndpointConfig:endpointConfig,Logging:logging,ResourcesVpcConfig:resourcesVpcConfig}' --output json" "Checking EKS cluster configuration"

log "📋 SOLUTIONS GENERATION"
log "Based on the analysis, here are the recommended solutions:"

# Generate solutions based on common EKS node join issues
cat >> "$LOG_FILE" << 'EOF'

=========================================
🔧 RECOMMENDED SOLUTIONS
=========================================

Based on the analysis, here are the most likely causes and solutions:

1. SECURITY GROUP ISSUES:
   - Check if the cluster security group allows communication on port 443 (HTTPS)
   - Ensure node security group allows communication on ports 1025-65535
   - Verify DNS resolution (port 53)

2. IAM ROLE PERMISSIONS:
   - Verify the node IAM role has the correct trust policy
   - Check if the role can assume the correct permissions
   - Ensure the instance profile is correctly attached

3. NETWORK CONNECTIVITY:
   - Check if the subnet has a route to the internet (via IGW or NAT)
   - Verify DNS resolution works
   - Check if the EKS endpoint is reachable from the subnet

4. LAUNCH TEMPLATE ISSUES:
   - Check if the user data script is correct
   - Verify the AMI is compatible with the EKS version
   - Check if the instance type is supported

5. CLUSTER CONFIGURATION:
   - Verify the cluster endpoint access configuration
   - Check if the cluster version is compatible with the node group

IMMEDIATE ACTIONS TO TRY:
1. Delete the failed node group and create a new one with updated configuration
2. Check and fix security group rules
3. Create private subnets with NAT gateways for better networking
4. Enable EKS cluster logging for better debugging

EOF

log "🏁 Analysis completed"
log "Full analysis saved to: $LOG_FILE"
log "Review the solutions section for next steps"
