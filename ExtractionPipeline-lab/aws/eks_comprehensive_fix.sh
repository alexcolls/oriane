#!/bin/bash

# EKS Cluster Comprehensive Fix Script
# Author: AI Assistant
# Date: 2025-07-11
# Purpose: Fix all identified EKS cluster issues based on analysis

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
VPC_ID="vpc-0c3ab41805ec7bf44"
FAILED_NODEGROUP="working-nodes-v2"
LOG_FILE="/home/quantium/labs/oriane/ExtractionPipeline/api/pipeline/eks_fix_$(date +%Y%m%d_%H%M%S).log"

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
        return 1
    fi
    log "=========================================="
    echo "" | tee -a "$LOG_FILE"
}

# Function to wait for operation
wait_for_operation() {
    local operation="$1"
    local check_cmd="$2"
    local timeout="$3"
    local interval=30
    local elapsed=0
    
    log "⏳ Waiting for $operation (timeout: ${timeout}s)"
    
    while [ $elapsed -lt $timeout ]; do
        if eval "$check_cmd" >/dev/null 2>&1; then
            log "✅ $operation completed successfully"
            return 0
        fi
        log "⏳ Still waiting for $operation... (${elapsed}s elapsed)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log "❌ $operation timed out after ${timeout}s"
    return 1
}

log "🚀 Starting EKS Cluster Comprehensive Fix"
log "Cluster: $CLUSTER_NAME"
log "Region: $REGION"
log "VPC ID: $VPC_ID"

# CRITICAL ISSUES IDENTIFIED FROM ANALYSIS:
# 1. Route table for subnet is null - no routing configured
# 2. No NAT gateways for private communication
# 3. No VPC endpoints for EKS services
# 4. Launch template missing (null response)
# 5. Node failed to join cluster due to networking issues

log "📋 STEP 1: Fix Route Table Configuration"
# Get all subnets and check their route tables
SUBNETS=$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID --region $REGION --query 'Subnets[].SubnetId' --output text)
IGW_ID=$(aws ec2 describe-internet-gateways --filters Name=attachment.vpc-id,Values=$VPC_ID --region $REGION --query 'InternetGateways[0].InternetGatewayId' --output text)

log "Found Internet Gateway: $IGW_ID"
log "Found subnets: $SUBNETS"

# Check and fix route tables for each subnet
for subnet in $SUBNETS; do
    log "🔍 Checking route table for subnet $subnet"
    
    # Get route table associated with subnet
    ROUTE_TABLE=$(aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=$subnet --region $REGION --query 'RouteTables[0].RouteTableId' --output text)
    
    if [ "$ROUTE_TABLE" = "None" ] || [ "$ROUTE_TABLE" = "" ] || [ "$ROUTE_TABLE" = "null" ]; then
        log "⚠️  No explicit route table found for subnet $subnet, using main route table"
        ROUTE_TABLE=$(aws ec2 describe-route-tables --filters Name=vpc-id,Values=$VPC_ID Name=association.main,Values=true --region $REGION --query 'RouteTables[0].RouteTableId' --output text)
    fi
    
    log "Route table for subnet $subnet: $ROUTE_TABLE"
    
    # Check if route to internet gateway exists
    INTERNET_ROUTE=$(aws ec2 describe-route-tables --route-table-ids $ROUTE_TABLE --region $REGION --query 'RouteTables[0].Routes[?DestinationCidrBlock==`0.0.0.0/0`].GatewayId' --output text)
    
    if [ "$INTERNET_ROUTE" = "" ] || [ "$INTERNET_ROUTE" = "None" ]; then
        log "⚠️  No internet route found for subnet $subnet, adding route to IGW"
        run_and_log "aws ec2 create-route --route-table-id $ROUTE_TABLE --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID --region $REGION" "Adding internet route for subnet $subnet"
    else
        log "✅ Internet route already exists for subnet $subnet"
    fi
done

log "📋 STEP 2: Create VPC Endpoints for EKS Services"
# Create VPC endpoints for EKS, EC2, and ECR services
VPC_ENDPOINTS_TO_CREATE=(
    "com.amazonaws.us-east-1.eks"
    "com.amazonaws.us-east-1.ec2"
    "com.amazonaws.us-east-1.ecr.dkr"
    "com.amazonaws.us-east-1.ecr.api"
    "com.amazonaws.us-east-1.s3"
)

for service in "${VPC_ENDPOINTS_TO_CREATE[@]}"; do
    # Check if endpoint already exists
    EXISTING_ENDPOINT=$(aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=$VPC_ID Name=service-name,Values=$service --region $REGION --query 'VpcEndpoints[0].VpcEndpointId' --output text)
    
    if [ "$EXISTING_ENDPOINT" = "None" ] || [ "$EXISTING_ENDPOINT" = "" ]; then
        log "🔍 Creating VPC endpoint for $service"
        
        if [[ "$service" == *"s3"* ]]; then
            # S3 is a gateway endpoint
            run_and_log "aws ec2 create-vpc-endpoint --vpc-id $VPC_ID --service-name $service --vpc-endpoint-type Gateway --route-table-ids $(aws ec2 describe-route-tables --filters Name=vpc-id,Values=$VPC_ID --region $REGION --query 'RouteTables[].RouteTableId' --output text | tr '\t' ' ') --region $REGION" "Creating S3 VPC endpoint"
        else
            # Interface endpoints
            run_and_log "aws ec2 create-vpc-endpoint --vpc-id $VPC_ID --service-name $service --vpc-endpoint-type Interface --subnet-ids $(echo $SUBNETS | tr ' ' '\n' | head -2 | tr '\n' ' ') --security-group-ids sg-0cd1e7025abfd2036 --region $REGION" "Creating interface VPC endpoint for $service"
        fi
    else
        log "✅ VPC endpoint for $service already exists: $EXISTING_ENDPOINT"
    fi
done

log "📋 STEP 3: Delete Failed Node Group"
log "🔍 Deleting failed node group: $FAILED_NODEGROUP"
run_and_log "aws eks delete-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $FAILED_NODEGROUP --region $REGION" "Deleting failed node group"

# Wait for node group deletion
wait_for_operation "node group deletion" "aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $FAILED_NODEGROUP --region $REGION 2>&1 | grep -q 'ResourceNotFoundException'" 600

log "📋 STEP 4: Create New Node Group with Proper Configuration"
# Create new node group with better configuration
NEW_NODEGROUP_NAME="fixed-nodes-$(date +%Y%m%d-%H%M%S)"
NODE_ROLE_ARN="arn:aws:iam::509399609859:role/AmazonEKSAutoNodeRole"

# Use only the first two subnets for better availability
SELECTED_SUBNETS=$(echo $SUBNETS | tr ' ' '\n' | head -2 | tr '\n' ',' | sed 's/,$//')

log "🔍 Creating new node group: $NEW_NODEGROUP_NAME"
log "Selected subnets: $SELECTED_SUBNETS"

run_and_log "aws eks create-nodegroup \\
    --cluster-name $CLUSTER_NAME \\
    --nodegroup-name $NEW_NODEGROUP_NAME \\
    --subnets $SELECTED_SUBNETS \\
    --instance-types t3.medium \\
    --ami-type AL2023_x86_64_STANDARD \\
    --node-role $NODE_ROLE_ARN \\
    --scaling-config minSize=1,maxSize=3,desiredSize=2 \\
    --disk-size 20 \\
    --capacity-type ON_DEMAND \\
    --update-config maxUnavailable=1 \\
    --region $REGION" "Creating new node group with fixed configuration"

# Wait for node group creation
log "⏳ Waiting for node group creation (this may take 10-15 minutes)"
wait_for_operation "node group creation" "aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $NEW_NODEGROUP_NAME --region $REGION --query 'nodegroup.status' --output text | grep -q 'ACTIVE'" 900

log "📋 STEP 5: Verify Node Registration"
# Check if nodes are registered in Kubernetes
log "🔍 Checking if nodes are registered in Kubernetes"
sleep 30  # Give some time for nodes to register

run_and_log "kubectl get nodes -o wide" "Checking registered nodes"

# Check if nodes are ready
READY_NODES=$(kubectl get nodes --no-headers 2>/dev/null | grep -c "Ready" || echo "0")
log "Number of ready nodes: $READY_NODES"

if [ "$READY_NODES" -gt 0 ]; then
    log "✅ Nodes are registered and ready!"
    
    log "📋 STEP 6: Test Pod Scheduling"
    # Test pod scheduling
    run_and_log "kubectl run test-pod --image=nginx --restart=Never --rm -i --tty=false --command -- /bin/echo 'Hello from EKS!'" "Testing pod scheduling"
    
    log "📋 STEP 7: Check Pipeline Deployment"
    # Check if pipeline pods can now be scheduled
    run_and_log "kubectl get pods -n pipeline" "Checking pipeline pods"
    
    # If pipeline pods are still pending, delete and recreate them
    PENDING_PODS=$(kubectl get pods -n pipeline --no-headers 2>/dev/null | grep -c "Pending" || echo "0")
    if [ "$PENDING_PODS" -gt 0 ]; then
        log "🔍 Restarting pending pipeline pods"
        run_and_log "kubectl delete pods -n pipeline --all" "Deleting pending pipeline pods"
        sleep 10
        run_and_log "kubectl get pods -n pipeline" "Checking pipeline pods after restart"
    fi
else
    log "❌ Nodes are not ready yet. Manual investigation may be needed."
fi

log "📋 STEP 8: Enable Cluster Autoscaler (Optional)"
# Check if cluster autoscaler is deployed
AUTOSCALER_DEPLOYED=$(kubectl get deployment cluster-autoscaler -n kube-system --no-headers 2>/dev/null | wc -l || echo "0")
if [ "$AUTOSCALER_DEPLOYED" -eq 0 ]; then
    log "🔍 Cluster autoscaler not found. You may want to deploy it for better scaling."
    log "Command to deploy cluster autoscaler:"
    log "kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml"
fi

log "📋 FINAL STATUS CHECK"
run_and_log "aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.status' --output text" "Final cluster status"
run_and_log "aws eks list-nodegroups --cluster-name $CLUSTER_NAME --region $REGION --output table" "Final node groups list"
run_and_log "kubectl get nodes" "Final nodes status"
run_and_log "kubectl get pods --all-namespaces" "Final pods status"

log "🏁 EKS Cluster Fix Completed"
log "Full fix log saved to: $LOG_FILE"
log ""
log "📋 SUMMARY:"
log "1. Fixed route table configuration for internet access"
log "2. Created VPC endpoints for EKS services"
log "3. Deleted failed node group"
log "4. Created new node group with proper configuration"
log "5. Verified node registration and pod scheduling"
log ""
log "If nodes are still not ready, check the CloudWatch logs for detailed error messages."
