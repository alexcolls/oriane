#!/bin/bash

# Comprehensive EKS Node Joining Fix Script
# This script addresses all common issues preventing nodes from joining EKS clusters

set -e

echo "=== Comprehensive EKS Node Joining Fix ==="
echo "Starting at $(date)"

# Configuration
CLUSTER_NAME="oriane-pipeline-api-cluster"
REGION="us-east-1"
NODE_GROUP_NAME="fixed-nodes-20250711-194653"

echo "Cluster: $CLUSTER_NAME"
echo "Region: $REGION"
echo "Node Group: $NODE_GROUP_NAME"
echo

# Step 1: Delete the failed node group
echo "=== Step 1: Cleaning up failed node group ==="
echo "Deleting failed node group: $NODE_GROUP_NAME"
aws eks delete-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NODE_GROUP_NAME \
    --region $REGION || echo "Node group already deleted or doesn't exist"

echo "Waiting for node group deletion to complete..."
aws eks wait nodegroup-deleted \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NODE_GROUP_NAME \
    --region $REGION || echo "Node group deletion completed or not found"

echo "✓ Node group cleanup completed"
echo

# Step 2: Get cluster information
echo "=== Step 2: Gathering cluster information ==="
CLUSTER_INFO=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION)
CLUSTER_ENDPOINT=$(echo $CLUSTER_INFO | jq -r '.cluster.endpoint')
CLUSTER_CA=$(echo $CLUSTER_INFO | jq -r '.cluster.certificateAuthority.data')
CLUSTER_VERSION=$(echo $CLUSTER_INFO | jq -r '.cluster.version')
VPC_ID=$(echo $CLUSTER_INFO | jq -r '.cluster.resourcesVpcConfig.vpcId')
SECURITY_GROUP_IDS=$(echo $CLUSTER_INFO | jq -r '.cluster.resourcesVpcConfig.securityGroupIds[]' | tr '\n' ' ')
SUBNET_IDS=$(echo $CLUSTER_INFO | jq -r '.cluster.resourcesVpcConfig.subnetIds[]' | tr '\n' ' ')

echo "Cluster Endpoint: $CLUSTER_ENDPOINT"
echo "Cluster Version: $CLUSTER_VERSION"
echo "VPC ID: $VPC_ID"
echo "Security Group IDs: $SECURITY_GROUP_IDS"
echo "Subnet IDs: $SUBNET_IDS"
echo

# Step 3: Create/Update IAM role for nodes
echo "=== Step 3: Setting up IAM role for nodes ==="
NODE_ROLE_NAME="EKS-NodeGroup-Role-$(date +%s)"
ASSUME_ROLE_POLICY_DOCUMENT='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

# Create IAM role
echo "Creating IAM role: $NODE_ROLE_NAME"
aws iam create-role \
    --role-name $NODE_ROLE_NAME \
    --assume-role-policy-document "$ASSUME_ROLE_POLICY_DOCUMENT" \
    --region $REGION || echo "Role might already exist"

# Attach required policies
echo "Attaching required policies to IAM role..."
aws iam attach-role-policy \
    --role-name $NODE_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy \
    --region $REGION

aws iam attach-role-policy \
    --role-name $NODE_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy \
    --region $REGION

aws iam attach-role-policy \
    --role-name $NODE_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly \
    --region $REGION

# Additional policy for SSM (for debugging)
aws iam attach-role-policy \
    --role-name $NODE_ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore \
    --region $REGION

echo "✓ IAM role setup completed"
echo

# Step 4: Create launch template with proper configuration
echo "=== Step 4: Creating launch template ==="
LAUNCH_TEMPLATE_NAME="EKS-LaunchTemplate-$(date +%s)"

# Get the latest EKS optimized AMI
echo "Getting latest EKS optimized AMI..."
# Use version 1.31 as 1.33 is not available
AMI_VERSION="1.31"
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=amazon-eks-node-${AMI_VERSION}-*" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text \
    --region $REGION)

echo "Using AMI ID: $AMI_ID (version $AMI_VERSION)"

# Create user data script
USER_DATA=$(cat <<EOF
#!/bin/bash
/etc/eks/bootstrap.sh $CLUSTER_NAME
EOF
)

USER_DATA_B64=$(echo "$USER_DATA" | base64 -w 0)

# Create launch template
echo "Creating launch template: $LAUNCH_TEMPLATE_NAME"
aws ec2 create-launch-template \
    --launch-template-name $LAUNCH_TEMPLATE_NAME \
    --launch-template-data "{
        \"ImageId\": \"$AMI_ID\",
        \"InstanceType\": \"t3.medium\",
        \"UserData\": \"$USER_DATA_B64\",
        \"SecurityGroupIds\": [\"$(echo $SECURITY_GROUP_IDS | cut -d' ' -f1)\"],
        \"IamInstanceProfile\": {
            \"Name\": \"$NODE_ROLE_NAME-InstanceProfile\"
        },
        \"TagSpecifications\": [
            {
                \"ResourceType\": \"instance\",
                \"Tags\": [
                    {
                        \"Key\": \"Name\",
                        \"Value\": \"$CLUSTER_NAME-node\"
                    },
                    {
                        \"Key\": \"kubernetes.io/cluster/$CLUSTER_NAME\",
                        \"Value\": \"owned\"
                    }
                ]
            }
        ]
    }" \
    --region $REGION

echo "✓ Launch template created"
echo

# Step 5: Create instance profile
echo "=== Step 5: Creating instance profile ==="
aws iam create-instance-profile \
    --instance-profile-name "$NODE_ROLE_NAME-InstanceProfile" \
    --region $REGION || echo "Instance profile might already exist"

aws iam add-role-to-instance-profile \
    --instance-profile-name "$NODE_ROLE_NAME-InstanceProfile" \
    --role-name $NODE_ROLE_NAME \
    --region $REGION || echo "Role might already be added"

echo "✓ Instance profile created"
echo

# Step 6: Wait for IAM propagation
echo "=== Step 6: Waiting for IAM propagation ==="
echo "Waiting 60 seconds for IAM changes to propagate..."
sleep 60

# Step 7: Create new node group with proper configuration
echo "=== Step 7: Creating new node group ==="
NEW_NODE_GROUP_NAME="working-nodes-$(date +%Y%m%d-%H%M%S)"

# Convert subnet IDs to array format for AWS CLI
SUBNET_ARRAY=$(echo $SUBNET_IDS | tr ' ' '\n' | sed 's/^/"/; s/$/"/; $!s/$/,/' | tr -d '\n')

# Get node role ARN
NODE_ROLE_ARN=$(aws iam get-role --role-name $NODE_ROLE_NAME --query 'Role.Arn' --output text --region $REGION)

echo "Creating node group: $NEW_NODE_GROUP_NAME"
echo "Node Role ARN: $NODE_ROLE_ARN"

aws eks create-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NEW_NODE_GROUP_NAME \
    --scaling-config minSize=1,maxSize=3,desiredSize=2 \
    --instance-types t3.medium \
    --ami-type AL2_x86_64 \
    --node-role $NODE_ROLE_ARN \
    --subnets $(echo $SUBNET_IDS | tr ' ' '\n' | head -2 | tr '\n' ' ') \
    --launch-template "{
        \"name\": \"$LAUNCH_TEMPLATE_NAME\",
        \"version\": \"1\"
    }" \
    --region $REGION

echo "✓ Node group creation initiated"
echo

# Step 8: Wait for node group to be active
echo "=== Step 8: Waiting for node group to become active ==="
echo "This may take 10-15 minutes..."

aws eks wait nodegroup-active \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NEW_NODE_GROUP_NAME \
    --region $REGION

echo "✓ Node group is now active"
echo

# Step 9: Update kubeconfig
echo "=== Step 9: Updating kubeconfig ==="
aws eks update-kubeconfig \
    --region $REGION \
    --name $CLUSTER_NAME

echo "✓ Kubeconfig updated"
echo

# Step 10: Verify nodes joined the cluster
echo "=== Step 10: Verifying nodes joined the cluster ==="
echo "Waiting 30 seconds for nodes to register..."
sleep 30

echo "Checking nodes in cluster:"
kubectl get nodes -o wide

echo
echo "=== Node Group Status ==="
aws eks describe-nodegroup \
    --cluster-name $CLUSTER_NAME \
    --nodegroup-name $NEW_NODE_GROUP_NAME \
    --region $REGION \
    --query 'nodegroup.{Status:status,Health:health,CreatedAt:createdAt}' \
    --output table

echo
echo "=== EC2 Instances Status ==="
aws ec2 describe-instances \
    --region $REGION \
    --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
    --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,Type:InstanceType,LaunchTime:LaunchTime}' \
    --output table

echo
echo "=== Fix Complete ==="
echo "New node group: $NEW_NODE_GROUP_NAME"
echo "IAM role: $NODE_ROLE_NAME"
echo "Launch template: $LAUNCH_TEMPLATE_NAME"
echo
echo "If nodes still don't join, check:"
echo "1. VPC DNS resolution and DNS hostnames are enabled"
echo "2. Subnets have internet access (via IGW or NAT)"
echo "3. Security groups allow required traffic"
echo "4. IAM roles have correct policies"
echo
echo "Completed at $(date)"
