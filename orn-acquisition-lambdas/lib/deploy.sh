#!/bin/bash

# Source utils
LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$LIB_DIR/utils.sh"

# Function to create ECR repository if it doesn't exist
create_ecr_repo() {
    local image_name="$1"
    
    info_message "Checking ECR repository..."
    if ! aws ecr describe-repositories --repository-names "$image_name" 2>/dev/null; then
        info_message "Creating ECR repository: $image_name"
        if ! aws ecr create-repository --repository-name "$image_name"; then
            handle_error "Failed to create ECR repository: $image_name"
        fi
        success_message "ECR repository created successfully"
    else
        success_message "ECR repository already exists"
    fi
}

# Function to authenticate Docker to ECR
authenticate_ecr() {
    info_message "Authenticating with ECR..."
    if ! aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"; then
        handle_error "Failed to authenticate with ECR"
    fi
    success_message "ECR authentication successful"
}

# Function to build Docker image
build_docker_image() {
    local lambda_path="$1"
    local image_name="$2"
    
    info_message "Building Docker image: $image_name"
    info_message "Lambda path: $lambda_path"
    
    # Change to lambda directory
    cd "$lambda_path" || handle_error "Failed to change to lambda directory: $lambda_path"
    
    # Force Docker to build in the right AWS ECR format
    export DOCKER_BUILDKIT=0
    export DOCKER_CLI_EXPERIMENTAL=enabled
    
    # Build Docker image with the specified platform
    if ! docker build --platform linux/amd64 --tag "$image_name" .; then
        handle_error "Docker build failed"
    fi
    
    success_message "Docker image built successfully"
}

# Function to save and reload Docker image (for consistency)
process_docker_image() {
    local image_name="$1"
    local tar_file="${image_name}.tar"
    
    # Save Docker image to tar file
    info_message "Saving Docker image to tar file..."
    if ! docker save -o "$tar_file" "${image_name}:latest"; then
        handle_error "Failed to save Docker image"
    fi
    
    # Remove local Docker image to ensure a clean load
    info_message "Removing local Docker image..."
    docker rmi "${image_name}:latest" || true
    
    # Load Docker image from tar file
    info_message "Loading Docker image from tar file..."
    if ! docker load -i "$tar_file"; then
        handle_error "Failed to load Docker image"
    fi
    
    # Clean up tar file immediately after loading
    info_message "Cleaning up temporary tar file..."
    if ! rm -f "$tar_file"; then
        info_message "Warning: Failed to remove tar file: $tar_file"
    else
        success_message "Temporary tar file removed"
    fi
    
    success_message "Docker image processed successfully"
}

# Function to tag and push image to ECR
push_to_ecr() {
    local image_name="$1"
    local ecr_repo="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${image_name}"
    
    info_message "Tagging and pushing image to ECR..."
    info_message "Source image: ${image_name}:latest"
    info_message "Target image: ${ecr_repo}:latest"
    
    # Ensure the source image exists
    if ! docker image inspect "${image_name}:latest" >/dev/null 2>&1; then
        handle_error "Source image ${image_name}:latest does not exist"
    fi
    
    # Remove any existing tags for the target image
    docker rmi "${ecr_repo}:latest" 2>/dev/null || true
    
    # Tag the image with proper validation
    if ! docker tag "${image_name}:latest" "${ecr_repo}:latest"; then
        handle_error "Failed to tag image"
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p /tmp/lambda-deploy-logs
    
    # Push with timeout and plain progress output
    info_message "Pushing image to ECR (this may take a few minutes)..."
    if ! timeout 3000 docker push "${ecr_repo}:latest" 2>&1 | tee "/tmp/lambda-deploy-logs/docker_push_${image_name}.log"; then
        if [ $? -eq 124 ]; then
            handle_error "Docker push timed out after 50 minutes"
        else
            echo "Error: Failed to push image to ECR"
            echo "Last 10 lines of push log:"
            tail -n 10 "/tmp/lambda-deploy-logs/docker_push_${image_name}.log"
            # Try one more time
            docker push "${ecr_repo}:latest"
            if [ $? -ne 0 ]; then
                handle_error "Failed to push image to ECR on retry"
            fi
        fi
    fi
    
    success_message "Image pushed to ECR successfully!"
    info_message "Image: ${ecr_repo}:latest"
    info_message "Digest: $(docker inspect --format='{{index .RepoDigests 0}}' "${ecr_repo}:latest" 2>/dev/null | cut -d'@' -f2 || echo 'N/A')"
}

# Main deployment function
deploy_lambda() {
    local lambda_path="$1"
    local image_name="$2"
    
    info_message "Starting deployment process..."
    
    # Pre-deployment checks
    check_docker
    check_aws
    validate_lambda_structure "$lambda_path"
    
    # Create ECR repository
    create_ecr_repo "$image_name"
    
    # Authenticate with ECR
    authenticate_ecr
    
    # Build Docker image
    build_docker_image "$lambda_path" "$image_name"
    
    # Process image (save/load cycle for consistency)
    process_docker_image "$image_name"
    
    # Push to ECR
    push_to_ecr "$image_name"
    
    # Clean up
    cleanup
}
