#!/bin/bash

# Check specific quotas for instances we need
set -e

REGION="us-east-1"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 Checking specific instance quotas for our requirements"

echo "================================================"
echo "KEY INSTANCE QUOTAS"
echo "================================================"

# Check standard instances quota (covers t3.medium)
echo "1. Standard instances (t3.medium falls under this):"
aws service-quotas get-service-quota \
    --service-code ec2 \
    --quota-code L-1216C47A \
    --region $REGION \
    --query 'Quota.{Name:QuotaName,Value:Value,Unit:Unit}' \
    --output table

echo ""
echo "2. G and VT instances (g5.xlarge and g4dn.xlarge):"
aws service-quotas get-service-quota \
    --service-code ec2 \
    --quota-code L-DB2E81BA \
    --region $REGION \
    --query 'Quota.{Name:QuotaName,Value:Value,Unit:Unit}' \
    --output table

echo ""
echo "================================================"
echo "CURRENT USAGE"
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
echo "CURRENT QUOTAS BY INSTANCE FAMILY"
echo "================================================"

# Check specific instance type quotas
echo "T3 instances (includes t3.medium):"
aws service-quotas list-service-quotas \
    --service-code ec2 \
    --region $REGION \
    --query 'Quotas[?contains(QuotaName, `Standard`) && contains(QuotaName, `instances`)].{QuotaName:QuotaName,Value:Value,Unit:Unit}' \
    --output table

echo ""
echo "G instances (includes g5.xlarge and g4dn.xlarge):"
aws service-quotas list-service-quotas \
    --service-code ec2 \
    --region $REGION \
    --query 'Quotas[?contains(QuotaName, `G and VT`) && contains(QuotaName, `instances`)].{QuotaName:QuotaName,Value:Value,Unit:Unit}' \
    --output table

echo ""
echo "================================================"
echo "AVAILABILITY ZONES CHECK"
echo "================================================"

# Check availability zones for our instances
echo "Available zones for t3.medium:"
aws ec2 describe-reserved-instances-offerings \
    --instance-type t3.medium \
    --region $REGION \
    --query 'ReservedInstancesOfferings[*].AvailabilityZone' \
    --output table 2>/dev/null || echo "No reserved instance data available"

echo ""
echo "Available zones for g5.xlarge:"
aws ec2 describe-reserved-instances-offerings \
    --instance-type g5.xlarge \
    --region $REGION \
    --query 'ReservedInstancesOfferings[*].AvailabilityZone' \
    --output table 2>/dev/null || echo "No reserved instance data available"

echo ""
echo "Available zones for g4dn.xlarge:"
aws ec2 describe-reserved-instances-offerings \
    --instance-type g4dn.xlarge \
    --region $REGION \
    --query 'ReservedInstancesOfferings[*].AvailabilityZone' \
    --output table 2>/dev/null || echo "No reserved instance data available"

echo ""
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Quota check completed!"
