#!/bin/bash

# Check AWS Service Quotas for EC2 instances
# This script will show current quotas for EC2 instances in your AWS account

set -e

REGION="us-east-1"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 Checking EC2 service quotas in region: $REGION"

# Check general EC2 quotas
echo "================================================"
echo "EC2 SERVICE QUOTAS"
echo "================================================"

# Get all EC2 quotas
aws service-quotas list-service-quotas \
    --service-code ec2 \
    --region $REGION \
    --query 'Quotas[*].{QuotaName:QuotaName,Value:Value,Unit:Unit}' \
    --output table

echo ""
echo "================================================"
echo "SPECIFIC INSTANCE TYPE QUOTAS"
echo "================================================"

# Check specific instance types we're using
INSTANCE_TYPES=("t3.medium" "g5.xlarge" "g4dn.xlarge")

for INSTANCE_TYPE in "${INSTANCE_TYPES[@]}"; do
    echo "Checking quota for $INSTANCE_TYPE..."
    
    # Get quota code for this instance type
    QUOTA_CODE=$(aws service-quotas list-service-quotas \
        --service-code ec2 \
        --region $REGION \
        --query "Quotas[?contains(QuotaName, '$INSTANCE_TYPE')].QuotaCode" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$QUOTA_CODE" ]; then
        aws service-quotas get-service-quota \
            --service-code ec2 \
            --quota-code $QUOTA_CODE \
            --region $REGION \
            --query 'Quota.{QuotaName:QuotaName,Value:Value,Unit:Unit}' \
            --output table
    else
        echo "No specific quota found for $INSTANCE_TYPE"
    fi
    echo ""
done

echo "================================================"
echo "RUNNING INSTANCES USAGE"
echo "================================================"

# Check current running instances
echo "Current running instances:"
aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].{InstanceId:InstanceId,InstanceType:InstanceType,State:State.Name,LaunchTime:LaunchTime}' \
    --output table

echo ""
echo "================================================"
echo "SPOT INSTANCE LIMITS"
echo "================================================"

# Check spot instance limits
echo "Spot instance limits:"
aws service-quotas list-service-quotas \
    --service-code ec2 \
    --region $REGION \
    --query 'Quotas[?contains(QuotaName, `Spot`)].{QuotaName:QuotaName,Value:Value,Unit:Unit}' \
    --output table

echo ""
echo "================================================"
echo "INSTANCE FAMILY QUOTAS"
echo "================================================"

# Check instance family quotas
echo "Instance family quotas (vCPUs):"
aws service-quotas list-service-quotas \
    --service-code ec2 \
    --region $REGION \
    --query 'Quotas[?contains(QuotaName, `vCPU`)].{QuotaName:QuotaName,Value:Value,Unit:Unit}' \
    --output table

echo ""
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Service quota check completed!"
