#!/bin/bash

# Fix EKS Security Group Rules for Node Communication
# This script updates the security group rules to allow proper node-to-control-plane communication

set -e

echo "=== EKS Security Group Rules Fix Script ==="
echo "Starting at $(date)"

# Configuration
CLUSTER_NAME="oriane-extraction-pipeline"
REGION="us-east-1"
SECURITY_GROUP_ID="sg-0cd1e7025abfd2036"

echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Security Group ID: $SECURITY_GROUP_ID"
echo

# Get VPC ID for the security group
echo "Getting VPC ID for security group..."
VPC_ID=$(aws ec2 describe-security-groups \
    --group-ids $SECURITY_GROUP_ID \
    --region $REGION \
    --query 'SecurityGroups[0].VpcId' \
    --output text)

echo "VPC ID: $VPC_ID"
echo

# Get VPC CIDR block
echo "Getting VPC CIDR block..."
VPC_CIDR=$(aws ec2 describe-vpcs \
    --vpc-ids $VPC_ID \
    --region $REGION \
    --query 'Vpcs[0].CidrBlock' \
    --output text)

echo "VPC CIDR: $VPC_CIDR"
echo

# Function to add security group rule if it doesn't exist
add_rule_if_not_exists() {
    local rule_type=$1
    local protocol=$2
    local port=$3
    local source=$4
    local description=$5
    
    echo "Checking if $rule_type rule exists: $protocol:$port from $source"
    
    if [ "$rule_type" == "ingress" ]; then
        existing=$(aws ec2 describe-security-groups \
            --group-ids $SECURITY_GROUP_ID \
            --region $REGION \
            --query "SecurityGroups[0].IpPermissions[?IpProtocol=='$protocol' && FromPort==\`$port\` && ToPort==\`$port\`]" \
            --output text)
    else
        existing=$(aws ec2 describe-security-groups \
            --group-ids $SECURITY_GROUP_ID \
            --region $REGION \
            --query "SecurityGroups[0].IpPermissionsEgress[?IpProtocol=='$protocol' && FromPort==\`$port\` && ToPort==\`$port\`]" \
            --output text)
    fi
    
    if [ -z "$existing" ]; then
        echo "Adding $rule_type rule: $protocol:$port from $source"
        if [ "$rule_type" == "ingress" ]; then
            if [[ $source == sg-* ]]; then
                aws ec2 authorize-security-group-ingress \
                    --group-id $SECURITY_GROUP_ID \
                    --protocol $protocol \
                    --port $port \
                    --source-group $source \
                    --region $REGION
            else
                aws ec2 authorize-security-group-ingress \
                    --group-id $SECURITY_GROUP_ID \
                    --protocol $protocol \
                    --port $port \
                    --cidr $source \
                    --region $REGION
            fi
        else
            if [[ $source == sg-* ]]; then
                aws ec2 authorize-security-group-egress \
                    --group-id $SECURITY_GROUP_ID \
                    --protocol $protocol \
                    --port $port \
                    --source-group $source \
                    --region $REGION
            else
                aws ec2 authorize-security-group-egress \
                    --group-id $SECURITY_GROUP_ID \
                    --protocol $protocol \
                    --port $port \
                    --cidr $source \
                    --region $REGION
            fi
        fi
        echo "✓ Rule added successfully"
    else
        echo "✓ Rule already exists"
    fi
    echo
}

# Function to add port range rule if it doesn't exist
add_port_range_rule() {
    local rule_type=$1
    local protocol=$2
    local from_port=$3
    local to_port=$4
    local source=$5
    local description=$6
    
    echo "Checking if $rule_type rule exists: $protocol:$from_port-$to_port from $source"
    
    if [ "$rule_type" == "ingress" ]; then
        existing=$(aws ec2 describe-security-groups \
            --group-ids $SECURITY_GROUP_ID \
            --region $REGION \
            --query "SecurityGroups[0].IpPermissions[?IpProtocol=='$protocol' && FromPort==\`$from_port\` && ToPort==\`$to_port\`]" \
            --output text)
    else
        existing=$(aws ec2 describe-security-groups \
            --group-ids $SECURITY_GROUP_ID \
            --region $REGION \
            --query "SecurityGroups[0].IpPermissionsEgress[?IpProtocol=='$protocol' && FromPort==\`$from_port\` && ToPort==\`$to_port\`]" \
            --output text)
    fi
    
    if [ -z "$existing" ]; then
        echo "Adding $rule_type rule: $protocol:$from_port-$to_port from $source"
        if [ "$rule_type" == "ingress" ]; then
            if [[ $source == sg-* ]]; then
                aws ec2 authorize-security-group-ingress \
                    --group-id $SECURITY_GROUP_ID \
                    --protocol $protocol \
                    --port $from_port-$to_port \
                    --source-group $source \
                    --region $REGION
            else
                aws ec2 authorize-security-group-ingress \
                    --group-id $SECURITY_GROUP_ID \
                    --protocol $protocol \
                    --port $from_port-$to_port \
                    --cidr $source \
                    --region $REGION
            fi
        else
            if [[ $source == sg-* ]]; then
                aws ec2 authorize-security-group-egress \
                    --group-id $SECURITY_GROUP_ID \
                    --protocol $protocol \
                    --port $from_port-$to_port \
                    --source-group $source \
                    --region $REGION
            else
                aws ec2 authorize-security-group-egress \
                    --group-id $SECURITY_GROUP_ID \
                    --protocol $protocol \
                    --port $from_port-$to_port \
                    --cidr $source \
                    --region $REGION
            fi
        fi
        echo "✓ Rule added successfully"
    else
        echo "✓ Rule already exists"
    fi
    echo
}

echo "=== Current Security Group Rules ==="
aws ec2 describe-security-groups \
    --group-ids $SECURITY_GROUP_ID \
    --region $REGION \
    --query 'SecurityGroups[0].{InboundRules:IpPermissions,OutboundRules:IpPermissionsEgress}' \
    --output table
echo

echo "=== Adding Required Inbound Rules ==="

# HTTPS/API Server communication (control plane to nodes)
add_rule_if_not_exists "ingress" "tcp" "443" "0.0.0.0/0" "HTTPS API Server"

# Kubelet API (control plane to nodes)
add_rule_if_not_exists "ingress" "tcp" "10250" "$VPC_CIDR" "Kubelet API"

# Node-to-node communication (inter-node communication)
add_rule_if_not_exists "ingress" "tcp" "0" "$SECURITY_GROUP_ID" "Node-to-node communication"
add_rule_if_not_exists "ingress" "udp" "0" "$SECURITY_GROUP_ID" "Node-to-node communication UDP"

# NodePort services range
add_port_range_rule "ingress" "tcp" "30000" "32767" "$VPC_CIDR" "NodePort services"

# DNS resolution
add_rule_if_not_exists "ingress" "tcp" "53" "$VPC_CIDR" "DNS TCP"
add_rule_if_not_exists "ingress" "udp" "53" "$VPC_CIDR" "DNS UDP"

# Container networking (CNI)
add_port_range_rule "ingress" "tcp" "1025" "65535" "$SECURITY_GROUP_ID" "Container networking"

# SSH access (if needed for debugging)
add_rule_if_not_exists "ingress" "tcp" "22" "$VPC_CIDR" "SSH access"

echo "=== Adding Required Outbound Rules ==="

# Remove default all-traffic egress rule first to be more specific
echo "Checking for overly permissive egress rules..."
aws ec2 describe-security-groups \
    --group-ids $SECURITY_GROUP_ID \
    --region $REGION \
    --query 'SecurityGroups[0].IpPermissionsEgress[]' \
    --output table

# HTTPS/API Server communication (nodes to control plane)
add_rule_if_not_exists "egress" "tcp" "443" "0.0.0.0/0" "HTTPS outbound"

# HTTP for package downloads, registry access
add_rule_if_not_exists "egress" "tcp" "80" "0.0.0.0/0" "HTTP outbound"

# DNS resolution
add_rule_if_not_exists "egress" "tcp" "53" "0.0.0.0/0" "DNS TCP outbound"
add_rule_if_not_exists "egress" "udp" "53" "0.0.0.0/0" "DNS UDP outbound"

# Node-to-node communication
add_rule_if_not_exists "egress" "tcp" "0" "$SECURITY_GROUP_ID" "Node-to-node outbound"
add_rule_if_not_exists "egress" "udp" "0" "$SECURITY_GROUP_ID" "Node-to-node outbound UDP"

# Container registry access (ECR uses 443, but Docker Hub may use other ports)
add_port_range_rule "egress" "tcp" "1025" "65535" "0.0.0.0/0" "Container registry access"

# NTP for time synchronization
add_rule_if_not_exists "egress" "udp" "123" "0.0.0.0/0" "NTP"

echo "=== Updated Security Group Rules ==="
aws ec2 describe-security-groups \
    --group-ids $SECURITY_GROUP_ID \
    --region $REGION \
    --query 'SecurityGroups[0].{InboundRules:IpPermissions,OutboundRules:IpPermissionsEgress}' \
    --output table
echo

echo "=== Checking Node Group Status ==="
aws eks describe-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name oriane-extraction-pipeline-nodegroup \
    --region $REGION \
    --query 'nodegroup.{Status:status,Health:health,CreatedAt:createdAt,ModifiedAt:modifiedAt}' \
    --output table

echo
echo "=== Checking EC2 Instances Status ==="
aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
    --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,Type:InstanceType,LaunchTime:LaunchTime}' \
    --output table

echo
echo "=== Checking if Nodes Join Cluster ==="
echo "Waiting 30 seconds for nodes to register..."
sleep 30

kubectl get nodes -o wide

echo
echo "=== Security Group Fix Complete ==="
echo "If nodes still don't join after a few minutes, try:"
echo "1. Terminate existing EC2 instances to force recreation"
echo "2. Check CloudWatch logs for the node group"
echo "3. Verify IAM roles and policies"
echo "4. Check VPC endpoints for private subnets"
echo
echo "Completed at $(date)"
