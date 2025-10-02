#!/bin/bash

# Comprehensive diagnostic script for EKS node joining issues

set -e

CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"

echo "🔍 EKS Node Joining Diagnostics"
echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "================================"

# Check cluster status
echo "📊 1. Cluster Status:"
aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.{Status:status,Version:version,Endpoint:endpoint,PlatformVersion:platformVersion}' --output table
echo ""

# Check cluster endpoint accessibility
echo "📊 2. Cluster Endpoint Accessibility:"
ENDPOINT=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.endpoint' --output text)
echo "Cluster endpoint: $ENDPOINT"
echo "Testing connectivity..."
curl -k -s --max-time 5 $ENDPOINT/healthz && echo "✅ Endpoint accessible" || echo "❌ Endpoint not accessible"
echo ""

# Check current nodegroups
echo "📊 3. Current NodeGroups:"
aws eks list-nodegroups --cluster-name $CLUSTER_NAME --region $REGION --query 'nodegroups' --output table
echo ""

# Check failed nodegroup details
NODEGROUPS=$(aws eks list-nodegroups --cluster-name $CLUSTER_NAME --region $REGION --query 'nodegroups' --output text)
for ng in $NODEGROUPS; do
    echo "📊 4. NodeGroup Details: $ng"
    aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $ng --region $REGION --query 'nodegroup.{Status:status,Health:health,CreatedAt:createdAt,Instances:resources.autoScalingGroups[0].name}' --output table
    echo ""
done

# Check VPC configuration
echo "📊 5. VPC Configuration:"
VPC_ID=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.resourcesVpcConfig.vpcId' --output text)
echo "VPC ID: $VPC_ID"

# Check subnets
echo "📊 6. Subnet Configuration:"
aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.resourcesVpcConfig.subnetIds' --output table
echo ""

# Check subnet route tables
echo "📊 7. Subnet Route Tables:"
SUBNETS=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.resourcesVpcConfig.subnetIds' --output text)
for subnet in $SUBNETS; do
    echo "Subnet: $subnet"
    RT_ID=$(aws ec2 describe-route-tables --filters "Name=association.subnet-id,Values=$subnet" --region $REGION --query 'RouteTables[0].RouteTableId' --output text)
    if [ "$RT_ID" = "None" ]; then
        RT_ID=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_ID" "Name=association.main,Values=true" --region $REGION --query 'RouteTables[0].RouteTableId' --output text)
        echo "  Using main route table: $RT_ID"
    else
        echo "  Route table: $RT_ID"
    fi
    aws ec2 describe-route-tables --route-table-ids $RT_ID --region $REGION --query 'RouteTables[0].Routes[*].[DestinationCidrBlock,GatewayId]' --output table
    echo ""
done

# Check security groups
echo "📊 8. Security Groups:"
aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query 'cluster.resourcesVpcConfig.securityGroupIds' --output table
echo ""

# Check IAM role
echo "📊 9. Node IAM Role:"
NODE_ROLE="AmazonEKSAutoNodeRole"
echo "Role: $NODE_ROLE"
aws iam list-attached-role-policies --role-name $NODE_ROLE --query 'AttachedPolicies[*].PolicyName' --output table
echo ""

# Check VPC endpoints
echo "📊 10. VPC Endpoints:"
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=$VPC_ID" --region $REGION --query 'VpcEndpoints[*].{ServiceName:ServiceName,State:State,VpcEndpointId:VpcEndpointId}' --output table
echo ""

# Check DNS resolution for cluster endpoint
echo "📊 11. DNS Resolution:"
ENDPOINT_HOST=$(echo $ENDPOINT | sed 's|https://||')
echo "Resolving: $ENDPOINT_HOST"
nslookup $ENDPOINT_HOST || echo "❌ DNS resolution failed"
echo ""

# Check if nodes can reach cluster endpoint
echo "📊 12. Node Instance Status:"
if [ -n "$NODEGROUPS" ]; then
    for ng in $NODEGROUPS; do
        echo "NodeGroup: $ng"
        ASG_NAME=$(aws eks describe-nodegroup --cluster-name $CLUSTER_NAME --nodegroup-name $ng --region $REGION --query 'nodegroup.resources.autoScalingGroups[0].name' --output text 2>/dev/null)
        if [ "$ASG_NAME" != "None" ] && [ -n "$ASG_NAME" ]; then
            echo "  Auto Scaling Group: $ASG_NAME"
            INSTANCES=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names $ASG_NAME --region $REGION --query 'AutoScalingGroups[0].Instances[*].InstanceId' --output text)
            echo "  Instances: $INSTANCES"
            for instance in $INSTANCES; do
                echo "    Instance: $instance"
                aws ec2 describe-instances --instance-ids $instance --region $REGION --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress,PrivateIpAddress]' --output table
            done
        fi
        echo ""
    done
fi

# Check kubectl connectivity
echo "📊 13. kubectl Connectivity:"
if command -v kubectl &> /dev/null; then
    echo "Testing kubectl connectivity..."
    kubectl get nodes --request-timeout=10s && echo "✅ kubectl working" || echo "❌ kubectl not working"
else
    echo "❌ kubectl not found"
fi
echo ""

# Recommendations
echo "🔧 RECOMMENDATIONS:"
echo "1. Verify that subnets have proper route tables with internet gateway routes"
echo "2. Check security group allows traffic between nodes and control plane"
echo "3. Ensure IAM role has all required policies attached"
echo "4. Verify VPC endpoints are configured correctly"
echo "5. Check if cluster endpoint is accessible from node subnets"
echo "6. Consider using private subnets with NAT gateway for better security"
echo ""

echo "✅ Diagnostics complete!"
