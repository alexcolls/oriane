#!/bin/bash


# =============================================================================
# Comprehensive Deployment Script for Oriane Pipeline API to AWS EKS
# =============================================================================
# This script sets up an EKS cluster, configures node groups, and deploys 
# the Oriane Pipeline API with scalable CPU and GPU support for video processing.
# Optimized for EKS 1.33 with appropriate GPU instances for video workloads.
# 
# Key Features:
# - Uses EKS 1.33 with Amazon Linux 2023 AMI for better GPU support
# - Configurable GPU instance types (g5.xlarge, g5.2xlarge, g4dn.xlarge, g4dn.2xlarge)
# - Larger disk sizes (200GB GPU, 80GB CPU) for video processing storage
# - Proper node selectors and taints to separate CPU and GPU workloads
# - GPU resource requests and limits for video processing
# - All configuration managed via .env file
# - Removes AL2 downgrade logic - requires AL2023 for EKS 1.33
#
# Run examples:
# bash deploy_to_eks.sh
# bash deploy_to_eks.sh --help
# bash deploy_to_eks.sh --dry-run
# bash deploy_to_eks.sh --no-rebuild
# bash deploy_to_eks.sh --dry-run --no-rebuild
# =============================================================================

set -euo pipefail

# Help function
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy the Oriane Pipeline API to AWS EKS.

Options:
    --dry-run         Show what would be done without executing
    --no-rebuild      Skip Docker image rebuild and use the latest existing image from ECR
    -h, --help        Show this help message

Examples:
    $0                    # Normal deployment with new image build
    $0 --dry-run          # Show what would be done without executing
    $0 --no-rebuild       # Deploy using the latest existing image from ECR
    $0 --dry-run --no-rebuild  # Show what would be done using existing image

Environment:
    Configuration is loaded from .env file in the current directory only.
    Required variables: CLUSTER_NAME, EKS_VERSION, AWS_REGION

EOF
}

# Parse command line arguments
DRY_RUN=false
NO_REBUILD=false
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-rebuild)
            NO_REBUILD=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            ;;
    esac
done

# Get the script directory and project root
SCRIPT_DIR="$(dirname "$(realpath "$0")")" 
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to execute or print commands based on dry-run mode
execute_or_print() {
    local cmd="$1"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "[DRY-RUN] Would execute: $cmd"
    else
        eval "$cmd"
    fi
}

# Load environment variables from .env (only from current directory)
ENV_FILE="$(pwd)/.env"
if [[ "$DRY_RUN" == "true" ]]; then
    if [[ ! -f "$ENV_FILE" ]]; then
        echo "[DRY-RUN] .env file not found in current directory. Using sample values for dry run."
        # Use sample values for dry run
        CLUSTER_NAME="oriane-pipeline-api-cluster"
        EKS_VERSION="1.33"
        AWS_REGION="us-east-1"
        API_VERSION="0.9.0"
        CPU_NODE_GROUP_NAME="oriane-pipeline-api-cpu-node"
        GPU_NODE_GROUP_NAME="oriane-pipeline-worker-gpu-node"
        DB_PASSWORD="dummy-password"
        API_KEY="dummy-api-key"
        QDRANT_KEY="dummy-qdrant-key"
    else
        source "$ENV_FILE"
    fi
else
    [[ -f "$ENV_FILE" ]] || { echo "[ERROR] .env not found in current directory"; exit 1; }
    source "$ENV_FILE"
fi

# Set default values if not provided in .env
IMAGE_NAME="oriane-pipeline-api"
K8S_NAMESPACE="oriane-pipeline-api"
AMI_FAMILY="${AMI_FAMILY:-AmazonLinux2023}"
GPU_INSTANCE_TYPES="${GPU_INSTANCE_TYPES:-g5.xlarge,g5.2xlarge,g4dn.xlarge,g4dn.2xlarge}"
CPU_INSTANCE_TYPES="${CPU_INSTANCE_TYPES:-c6g.large,c6g.xlarge,c6g.2xlarge}"
GPU_MIN_NODES="${GPU_MIN_NODES:-0}"
GPU_MAX_NODES="${GPU_MAX_NODES:-5}"
GPU_DESIRED_NODES="${GPU_DESIRED_NODES:-1}"
CPU_MIN_NODES="${CPU_MIN_NODES:-2}"
CPU_MAX_NODES="${CPU_MAX_NODES:-10}"
CPU_DESIRED_NODES="${CPU_DESIRED_NODES:-3}"
GPU_DISK_SIZE="${GPU_DISK_SIZE:-200}"
CPU_DISK_SIZE="${CPU_DISK_SIZE:-80}"
# ALB Controller settings
AWS_PROFILE="${AWS_PROFILE:-default}"
ALB_DOMAIN="${ALB_DOMAIN:-pipeline.api.qdrant.admin.oriane.xyz}"
ALB_CERTIFICATE_ARN="${ALB_CERTIFICATE_ARN:-}"
ALB_POLICY_ARN_FILE="$SCRIPT_DIR/deploy/alb-policy-arn.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
# YELLOW='\033[1;33m'  # Unused but kept for future use
NC='\033[0m' # No Color

# Validate EKS version and AMI family compatibility
# For EKS 1.33+, we use AL2023 GPU AMIs which are available

# Validate required environment variables
if [[ -z "${CLUSTER_NAME:-}" || -z "${EKS_VERSION:-}" || -z "${AWS_REGION:-}" ]]; then
    echo -e "${RED}[ERROR] Required environment variables missing. Please check your .env file.${NC}"
    echo -e "${RED}Required: CLUSTER_NAME, EKS_VERSION, AWS_REGION${NC}"
    exit 1
fi

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

setup_alb_controller() {
    log "Setting up ALB Controller IAM Policy..."
    execute_or_print "bash ${SCRIPT_DIR}/deploy/01-create-iam-policy.sh"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        POLICY_ARN="arn:aws:iam::123456789012:policy/AWSLoadBalancerControllerIAMPolicy"
        log "[DRY-RUN] Would use ALB Policy ARN: ${POLICY_ARN}"
    else
        if [[ -f ${ALB_POLICY_ARN_FILE} ]]; then
            POLICY_ARN=$(cat ${ALB_POLICY_ARN_FILE})
            log "ALB Policy ARN: ${POLICY_ARN}"
        else
            error "ALB IAM Policy ARN file not found."
        fi
    fi
    success "ALB Controller setup completed!"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

# Obtain the latest EKS Optimized GPU AMI based on AMI_FAMILY
if [[ "$DRY_RUN" == "true" ]]; then
    GPU_AMI_ID="ami-0123456789abcdef0"
    echo "[DRY-RUN] Would query AWS SSM for GPU AMI ID. Using dummy value: $GPU_AMI_ID"
else
    # Build the correct SSM parameter path based on AMI_FAMILY
    if [[ "$AMI_FAMILY" == "AmazonLinux2023" ]]; then
        SSM_PATH="/aws/service/eks/optimized-ami/1.33/amazon-linux-2023-gpu/recommended/image_id"
    elif [[ "$EKS_VERSION" == "1.32" ]]; then
        SSM_PATH="/aws/service/eks/optimized-ami/1.32/amazon-linux-2-gpu/recommended/image_id"
    else
        SSM_PATH="/aws/service/eks/optimized-ami/${EKS_VERSION}/amazon-linux-2-gpu/recommended/image_id"
    fi
    
    echo "[INFO] Querying SSM parameter: $SSM_PATH"
    GPU_AMI_ID=$(aws ssm get-parameters \
      --names "$SSM_PATH" \
      --query 'Parameters[0].Value' --output text 2>/dev/null || echo "None")
    
    echo "[INFO] Retrieved GPU AMI ID: $GPU_AMI_ID"
fi

# Sanity check - ensure GPU_AMI_ID is not empty and valid
# If AL2023 GPU AMI is not available, fall back to AL2 GPU AMI
if [[ -z "$GPU_AMI_ID" || "$GPU_AMI_ID" == "None" ]]; then
    if [[ "$AMI_FAMILY" == "AmazonLinux2023" ]]; then
        log "AL2023 GPU AMI not available for EKS ${EKS_VERSION}, falling back to AL2 GPU AMI"
        AMI_FAMILY="AmazonLinux2"
        SSM_PATH="/aws/service/eks/optimized-ami/1.32/amazon-linux-2-gpu/recommended/image_id"
        echo "[INFO] Querying fallback SSM parameter: $SSM_PATH"
        GPU_AMI_ID=$(aws ssm get-parameters \
          --names "$SSM_PATH" \
          --query 'Parameters[0].Value' --output text 2>/dev/null || echo "None")
        echo "[INFO] Retrieved fallback GPU AMI ID: $GPU_AMI_ID"
        
        if [[ -z "$GPU_AMI_ID" || "$GPU_AMI_ID" == "None" ]]; then
            error "No GPU AMI ID found for fallback AL2 either. Please check your AWS configuration."
        fi
    elif [[ "$GPU_AMI_ID" == "None" ]]; then
        error "No GPU AMI ID found for EKS version ${EKS_VERSION} with AMI family ${AMI_FAMILY}. This combination may not be supported yet."
    else
        error "Failed to retrieve GPU AMI ID. Please verify your AWS credentials and permissions."
    fi
fi

log "Using GPU AMI ID: $GPU_AMI_ID for EKS version ${EKS_VERSION}"

# --- Functions ---

create_eks_cluster() {
    log "Creating EKS Cluster if not exists..."
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "[DRY-RUN] Would check if cluster exists: eksctl get cluster --name '$CLUSTER_NAME' --region '$AWS_REGION'"
        echo "[DRY-RUN] Would use existing VPC: vpc-0c3ab41805ec7bf44"
        echo "[DRY-RUN] Would query subnets: aws ec2 describe-subnets --filters 'Name=vpc-id,Values=vpc-0c3ab41805ec7bf44' --query 'Subnets[?AvailabilityZone!=\`us-east-1e\`].SubnetId' --output text | tr '\t' ','"
        echo "[DRY-RUN] Would create cluster: eksctl create cluster --name '$CLUSTER_NAME' --region '$AWS_REGION' --vpc-public-subnets 'subnet-123,subnet-456' --nodes 1 --managed --version '$EKS_VERSION'"
        success "EKS Cluster '$CLUSTER_NAME' would be created"
    else
        if ! eksctl get cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" 2>/dev/null; then
            # Use existing VPC to avoid hitting VPC limits
            EXISTING_VPC="vpc-0c3ab41805ec7bf44"
            
            # Get subnets for the existing VPC (excluding us-east-1e)
            SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$EXISTING_VPC" --query "Subnets[?AvailabilityZone!=\`us-east-1e\`].SubnetId" --output text | tr '\t' ',')
            
            log "Using existing VPC: $EXISTING_VPC"
            log "Using subnets: $SUBNETS"
            
            eksctl create cluster \
                --name "$CLUSTER_NAME" \
                --region "$AWS_REGION" \
                --vpc-public-subnets "$SUBNETS" \
                --nodes 1 \
                --managed \
                --version "$EKS_VERSION"
            success "EKS Cluster '$CLUSTER_NAME' created"
        else
            success "EKS Cluster '$CLUSTER_NAME' already exists"
        fi
    fi
}

create_node_groups() {
    # Convert comma-separated instance types to array
    IFS=',' read -ra CPU_TYPES <<< "$CPU_INSTANCE_TYPES"
    IFS=',' read -ra GPU_TYPES <<< "$GPU_INSTANCE_TYPES"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "[DRY-RUN] Would check if CPU node group exists: eksctl get nodegroup --cluster '$CLUSTER_NAME' --name '$CPU_NODE_GROUP_NAME' --region '$AWS_REGION'"
        echo "[DRY-RUN] Would create CPU node group: eksctl create nodegroup --cluster '$CLUSTER_NAME' --name '$CPU_NODE_GROUP_NAME' --region '$AWS_REGION' --node-type '${CPU_TYPES[0]}' --nodes $CPU_DESIRED_NODES --nodes-min $CPU_MIN_NODES --nodes-max $CPU_MAX_NODES --node-volume-size $CPU_DISK_SIZE --node-ami-family '$AMI_FAMILY' --managed"
        echo "[DRY-RUN] Would check if GPU node group exists: eksctl get nodegroup --cluster '$CLUSTER_NAME' --name '$GPU_NODE_GROUP_NAME' --region '$AWS_REGION'"
        echo "[DRY-RUN] Would create GPU node group: eksctl create nodegroup --cluster '$CLUSTER_NAME' --name '$GPU_NODE_GROUP_NAME' --region '$AWS_REGION' --node-type '${GPU_TYPES[0]}' --nodes $GPU_DESIRED_NODES --nodes-min $GPU_MIN_NODES --nodes-max $GPU_MAX_NODES --node-volume-size $GPU_DISK_SIZE --node-ami-family '$AMI_FAMILY' --node-ami '$GPU_AMI_ID' --managed --node-labels 'nodeType=gpu,workload=video-processing'"
        echo "[DRY-RUN] Would check for NVIDIA device plugin: kubectl get daemonset -n kube-system nvidia-device-plugin-daemonset"
        echo "[DRY-RUN] Would apply NVIDIA device plugin: kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.5/nvidia-device-plugin.yml"
        success "Node groups would be created"
    else
        # Check if CPU node group exists
        if ! eksctl get nodegroup --cluster "$CLUSTER_NAME" --name "$CPU_NODE_GROUP_NAME" --region "$AWS_REGION" 2>/dev/null; then
            log "Creating CPU node group with instance types: ${CPU_INSTANCE_TYPES}"
            log "CPU scaling: min=${CPU_MIN_NODES}, max=${CPU_MAX_NODES}, desired=${CPU_DESIRED_NODES}"
            
            # Build CPU node group command
            CPU_NODEGROUP_CMD="eksctl create nodegroup \\
                --cluster '$CLUSTER_NAME' \\
                --name '$CPU_NODE_GROUP_NAME' \\
                --region '$AWS_REGION' \\
                --node-type '${CPU_TYPES[0]}' \\
                --nodes $CPU_DESIRED_NODES \\
                --nodes-min $CPU_MIN_NODES \\
                --nodes-max $CPU_MAX_NODES \\
                --node-volume-size $CPU_DISK_SIZE \\
                --node-ami-family '$AMI_FAMILY' \\
                --managed"
            
            # Add multiple instance types if more than one specified
            if [[ ${#CPU_TYPES[@]} -gt 1 ]]; then
                CPU_NODEGROUP_CMD+=" --instance-types ${CPU_INSTANCE_TYPES}"
            fi
            
            eval "$CPU_NODEGROUP_CMD"
            success "CPU node group '$CPU_NODE_GROUP_NAME' created"
        else
            success "CPU node group '$CPU_NODE_GROUP_NAME' already exists"
        fi

        # Check if GPU node group exists
        if ! eksctl get nodegroup --cluster "$CLUSTER_NAME" --name "$GPU_NODE_GROUP_NAME" --region "$AWS_REGION" 2>/dev/null; then
            log "Creating GPU node group with instance types: ${GPU_INSTANCE_TYPES}"
            log "GPU scaling: min=${GPU_MIN_NODES}, max=${GPU_MAX_NODES}, desired=${GPU_DESIRED_NODES}"
            log "Using AMI: $GPU_AMI_ID"
            
            # Build GPU node group command
            # Use instance-types if multiple types specified, otherwise use node-type
            if [[ ${#GPU_TYPES[@]} -gt 1 ]]; then
                GPU_NODEGROUP_CMD="eksctl create nodegroup \\
                    --cluster '$CLUSTER_NAME' \\
                    --name '$GPU_NODE_GROUP_NAME' \\
                    --region '$AWS_REGION' \\
                    --instance-types ${GPU_INSTANCE_TYPES} \\
                    --nodes $GPU_DESIRED_NODES \\
                    --nodes-min $GPU_MIN_NODES \\
                    --nodes-max $GPU_MAX_NODES \\
                    --node-volume-size $GPU_DISK_SIZE \\
                    --node-ami-family '$AMI_FAMILY' \\
                    --node-ami '$GPU_AMI_ID' \\
                    --managed"
            else
                GPU_NODEGROUP_CMD="eksctl create nodegroup \\
                    --cluster '$CLUSTER_NAME' \\
                    --name '$GPU_NODE_GROUP_NAME' \\
                    --region '$AWS_REGION' \\
                    --node-type '${GPU_TYPES[0]}' \\
                    --nodes $GPU_DESIRED_NODES \\
                    --nodes-min $GPU_MIN_NODES \\
                    --nodes-max $GPU_MAX_NODES \\
                    --node-volume-size $GPU_DISK_SIZE \\
                    --node-ami-family '$AMI_FAMILY' \\
                    --node-ami '$GPU_AMI_ID' \\
                    --managed"
            fi
            
            # Add GPU-specific labels
            GPU_NODEGROUP_CMD+=" --node-labels 'nodeType=gpu,workload=video-processing'"
            
            # For AL2 AMI with EKS 1.33, we need to use a config file approach
            if [[ "$AMI_FAMILY" == "AmazonLinux2" && "$EKS_VERSION" == "1.33" ]]; then
                log "Using AL2 AMI with EKS 1.33 requires config file approach"
                # Create a temporary config file for the nodegroup
                cat > /tmp/gpu-nodegroup.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: $CLUSTER_NAME
  region: $AWS_REGION
  version: "$EKS_VERSION"
managedNodeGroups:
  - name: $GPU_NODE_GROUP_NAME
    instanceTypes: [$(echo $GPU_INSTANCE_TYPES | sed 's/,/", "/g' | sed 's/^/"/' | sed 's/$/"/')]
    minSize: $GPU_MIN_NODES
    maxSize: $GPU_MAX_NODES
    desiredCapacity: $GPU_DESIRED_NODES
    volumeSize: $GPU_DISK_SIZE
    ami: $GPU_AMI_ID
    amiFamily: $AMI_FAMILY
    labels:
      nodeType: gpu
      workload: video-processing
    overrideBootstrapCommand: |
      #!/bin/bash
      /etc/eks/bootstrap.sh $CLUSTER_NAME
EOF
                eksctl create nodegroup -f /tmp/gpu-nodegroup.yaml
                rm -f /tmp/gpu-nodegroup.yaml
            else
                eval "$GPU_NODEGROUP_CMD"
            fi
            success "GPU node group '$GPU_NODE_GROUP_NAME' created"
        else
            success "GPU node group '$GPU_NODE_GROUP_NAME' already exists"
        fi
        
        # Apply Nvidia device plugin if not already present
        if ! kubectl get daemonset -n kube-system nvidia-device-plugin-daemonset 2>/dev/null; then
            log "Applying NVIDIA device plugin DaemonSet..."
            kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.5/nvidia-device-plugin.yml
            success "NVIDIA device plugin applied"
        else
            success "NVIDIA device plugin already exists"
        fi
    fi
}

build_and_push_image() {
    if [[ "$DRY_RUN" == "true" ]]; then
        if [[ "$NO_REBUILD" == "true" ]]; then
            echo "[DRY-RUN] Would get AWS account ID: aws sts get-caller-identity --query Account --output text"
            echo "[DRY-RUN] Would get most recent image: aws ecr describe-images --repository-name $IMAGE_NAME --region '$AWS_REGION' --query 'sort_by(imageDetails,&imagePushedAt)[-1].imageTags[0]' --output text"
            ECR_IMAGE_URI="123456789012.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:latest-tag"
            success "Would use existing image from ECR"
        else
            echo "[DRY-RUN] Would get AWS account ID: aws sts get-caller-identity --query Account --output text"
            echo "[DRY-RUN] Would build Docker image: docker build -t '$IMAGE_NAME:$API_VERSION-timestamp' -f '$PROJECT_ROOT/deploy/docker/Dockerfile' '$PROJECT_ROOT' --target prod"
            echo "[DRY-RUN] Would create ECR repository: aws ecr create-repository --repository-name $IMAGE_NAME --region '$AWS_REGION'"
            echo "[DRY-RUN] Would tag image: docker tag '$IMAGE_NAME:$API_VERSION-timestamp' '123456789012.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$API_VERSION-timestamp'"
            echo "[DRY-RUN] Would login to ECR: aws ecr get-login-password --region '$AWS_REGION' | docker login --username AWS --password-stdin"
            echo "[DRY-RUN] Would push image: docker push '123456789012.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$API_VERSION-timestamp'"
            ECR_IMAGE_URI="123456789012.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}:${API_VERSION}-timestamp"
            success "Image would be pushed to ECR"
        fi
    else
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        
        if [[ "$NO_REBUILD" == "true" ]]; then
            # Use the most recent image from ECR
            log "Using existing image from ECR (--no-rebuild flag set)"
            
            # Get the most recent image tag from ECR
            LATEST_TAG=$(aws ecr describe-images --repository-name $IMAGE_NAME --region "$AWS_REGION" --query 'sort_by(imageDetails,&imagePushedAt)[-1].imageTags[0]' --output text 2>/dev/null || echo "")
            
            if [[ -z "$LATEST_TAG" || "$LATEST_TAG" == "null" ]]; then
                error "No existing images found in ECR repository. Please run without --no-rebuild flag to build a new image."
            fi
            
            ECR_IMAGE_URI="${ECR_REGISTRY}/${IMAGE_NAME}:${LATEST_TAG}"
            log "Using existing image: $ECR_IMAGE_URI"
            success "Using existing image from ECR"
        else
            # Build and push new image
            # Create image tag with version and timestamp
            TIMESTAMP=$(date +%Y%m%d-%H%M%S)
            IMAGE_TAG="${API_VERSION}-${TIMESTAMP}"
            ECR_IMAGE_URI="${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
            
            log "Building and pushing Docker image with tag: $IMAGE_TAG"
            docker build -t "$IMAGE_NAME:$IMAGE_TAG" -f "$SCRIPT_DIR/deploy/docker/Dockerfile" "$PROJECT_ROOT" --target prod
            aws ecr create-repository --repository-name $IMAGE_NAME --region "$AWS_REGION" || true
            docker tag "$IMAGE_NAME:$IMAGE_TAG" "$ECR_IMAGE_URI"
            aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
            docker push "$ECR_IMAGE_URI"
            success "Image pushed to ECR: $ECR_IMAGE_URI"
        fi
    fi
}

update_and_apply_manifests() {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "[DRY-RUN] Would create namespace: kubectl create namespace '$K8S_NAMESPACE'"
        echo "[DRY-RUN] Would create ConfigMap: kubectl create configmap '${IMAGE_NAME}-config' --from-env-file='$PROJECT_ROOT/.env' -n '$K8S_NAMESPACE' --dry-run=client -o yaml | kubectl apply -f -"
        echo "[DRY-RUN] Would create Secret: kubectl create secret generic '${IMAGE_NAME}-secrets' --from-literal=DB_PASSWORD='***' --from-literal=API_KEY='***' --from-literal=QDRANT_KEY='***' -n '$K8S_NAMESPACE' --dry-run=client -o yaml | kubectl apply -f -"
        echo "[DRY-RUN] Would update image in deployment files: sed -i 's|image:.*|image: $ECR_IMAGE_URI|g' '$PROJECT_ROOT/deploy/kubernetes/deployment-cpu.yaml'"
        echo "[DRY-RUN] Would update image in deployment files: sed -i 's|image:.*|image: $ECR_IMAGE_URI|g' '$PROJECT_ROOT/deploy/kubernetes/deployment-gpu.yaml'"
        echo "[DRY-RUN] Would apply Kubernetes manifests:"
        echo "[DRY-RUN]   kubectl apply -f '$PROJECT_ROOT/deploy/kubernetes/deployment-cpu.yaml'"
        echo "[DRY-RUN]   kubectl apply -f '$PROJECT_ROOT/deploy/kubernetes/deployment-gpu.yaml'"
        echo "[DRY-RUN]   kubectl apply -f '$PROJECT_ROOT/deploy/kubernetes/service.yaml'"
        echo "[DRY-RUN]   kubectl apply -f '$PROJECT_ROOT/deploy/kubernetes/hpa.yaml'"
        echo "[DRY-RUN] Would substitute environment variables in ingress: envsubst < '$PROJECT_ROOT/deploy/kubernetes/ingress.yaml' | kubectl apply -f -"
        success "Kubernetes deployments would be applied"
    else
        # Create namespace if it doesn't exist
        kubectl create namespace "$K8S_NAMESPACE" || true
        
        # Create ConfigMap and Secrets
        log "Creating ConfigMap and Secrets..."
        kubectl create configmap "${IMAGE_NAME}-config" --from-env-file="$ENV_FILE" -n "$K8S_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
        kubectl create secret generic "${IMAGE_NAME}-secrets" \
            --from-literal=DB_PASSWORD="${DB_PASSWORD}" \
            --from-literal=API_KEY="${API_KEY}" \
            --from-literal=QDRANT_KEY="${QDRANT_KEY}" \
            -n "$K8S_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
        
        # Update image in deployment files
        sed -i "s|image:.*|image: $ECR_IMAGE_URI|g" "$SCRIPT_DIR/deploy/kubernetes/deployment-cpu.yaml"
        sed -i "s|image:.*|image: $ECR_IMAGE_URI|g" "$SCRIPT_DIR/deploy/kubernetes/deployment-gpu.yaml"

        log "Applying Kubernetes manifests..."
        kubectl apply -f "$SCRIPT_DIR/deploy/kubernetes/deployment-cpu.yaml"
        kubectl apply -f "$SCRIPT_DIR/deploy/kubernetes/deployment-gpu.yaml"
        kubectl apply -f "$SCRIPT_DIR/deploy/kubernetes/service.yaml" || true
        kubectl apply -f "$SCRIPT_DIR/deploy/kubernetes/hpa.yaml" || true
        
        # Apply ingress with environment variable substitution
        log "Applying ingress with domain: $ALB_DOMAIN"
        envsubst < "${PROJECT_ROOT}/deploy/kubernetes/ingress.yaml" | kubectl apply -f -
        success "Kubernetes deployments applied"
    fi
}

deploy_status() {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "[DRY-RUN] Would check deployment status: kubectl get deployments -n '$K8S_NAMESPACE'"
        echo "[DRY-RUN] Would check rollout status: kubectl rollout status deployment/oriane-pipeline-api -n '$K8S_NAMESPACE'"
        echo "[DRY-RUN] Would check rollout status: kubectl rollout status deployment/oriane-pipeline-worker -n '$K8S_NAMESPACE'"
        success "Deployments would be ready and running"
    else
        log "Checking deployment status..."
        kubectl get deployments -n "$K8S_NAMESPACE"
        kubectl rollout status deployment/oriane-pipeline-api -n "$K8S_NAMESPACE"
        kubectl rollout status deployment/oriane-pipeline-worker -n "$K8S_NAMESPACE"
        success "Deployments are ready and running"
    fi
}

verify_external_access() {
    log "Verifying external access to API..."
    execute_or_print "bash ${SCRIPT_DIR}/deploy/07-verify-api.sh"
    success "External access verification completed!"
}

# --- Main Execution ---

main() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log "Running in DRY-RUN mode - no actual AWS calls will be made"
    fi
    
    create_eks_cluster
    create_node_groups
    setup_alb_controller
    build_and_push_image
    update_and_apply_manifests
    deploy_status
    verify_external_access
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "Dry-run of deployment to EKS cluster '$CLUSTER_NAME' is complete!"
    else
        log "Deployment to EKS cluster '$CLUSTER_NAME' is complete!"
    fi
}

main "$@"

