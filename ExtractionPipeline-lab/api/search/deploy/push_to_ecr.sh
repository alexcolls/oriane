#!/bin/bash

# Deploy Oriane API to Amazon ECR
# This script builds, tags, and pushes the Docker image to ECR.
# It's a lighter and cleaner version of the push_image.sh script. Both works.

set -e

# Configuration - Update these values for your environment
VERSION="1.0.0"
ACCOUNT_ID="509399609859"
AWS_REGION="us-east-1"
IMAGE_NAME="oriane-search-api-v1"
REGISTRY_DOMAIN="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
REPOSITORY_NAME="${REPOSITORY_NAME:-oriane-search-api-v1}"
# Full ECR repository URI (registry domain + repository name)
ECR_REPO="${REGISTRY_DOMAIN}/${REPOSITORY_NAME}"
IMAGE_TAG="${IMAGE_TAG:-1.0.0}"
ROLE="OrianeCollector"

echo "🚀 Building image and pushing to ECR"
echo "==============================="
echo "Registry domain: $REGISTRY_DOMAIN"
echo "Repository URI: $ECR_REPO"
echo "Tag: $IMAGE_TAG"
echo "Region: $AWS_REGION"
echo ""

###############################################
# Step 1: Build the Docker image
#----------------------------------------------
# We need a build context that includes **both**
# the `api/` directory (where the Dockerfile lives)
# and the sibling `core/` directory referenced by
# the COPY commands in the Dockerfile.  Using the
# deploy folder (`api/deploy`) as context hides
# everything outside this directory, which causes
# the "… not found" errors you encountered.
#
# The project root contains both folders, so we
# switch our context there and point Docker to the
# Dockerfile inside `api/search/`.
###############################################

echo "1. Building Docker image (project root context)…"

# Determine project root (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Build from the project root so all referenced paths are available
docker build -t $IMAGE_NAME:$IMAGE_TAG \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VERSION=$IMAGE_TAG \
    --build-arg GIT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "unknown") \
    -f "$PROJECT_ROOT/api/search/Dockerfile" "$PROJECT_ROOT"

echo "✅ Image built successfully"

# Step 2: Authenticate with ECR
echo "2. Authenticating with ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $REGISTRY_DOMAIN

echo "✅ ECR authentication successful"

# Step 3: Create repository if it doesn't exist
echo "3. Ensuring ECR repository exists..."
if ! aws ecr describe-repositories --repository-names $REPOSITORY_NAME --region $AWS_REGION >/dev/null 2>&1; then
    echo "Creating ECR repository: $REPOSITORY_NAME"
    aws ecr create-repository \
        --repository-name $REPOSITORY_NAME \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true
    echo "✅ Repository created"
else
    echo "✅ Repository already exists"
fi

# Step 4: Tag the image for ECR
echo "4. Tagging image for ECR..."
docker tag $IMAGE_NAME:$IMAGE_TAG $ECR_REPO:$IMAGE_TAG
docker tag $IMAGE_NAME:$IMAGE_TAG $ECR_REPO:latest

echo "✅ Image tagged for ECR"

# Step 5: Push to ECR
echo "5. Pushing to ECR..."
docker push $ECR_REPO:$IMAGE_TAG
docker push $ECR_REPO:latest

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo "✅ Image pushed to: $ECR_REPO:$IMAGE_TAG"
echo "✅ Latest tag: $ECR_REPO:latest"
echo ""
echo "Next steps:"
echo "- Deploy to ECS/EKS using the image URI above"
echo "- Ensure your deployment environment has:"
echo "  * GPU-enabled instances (for CUDA acceleration)"
echo "  * Proper IAM roles for ECR access"
echo "  * Environment variables from .env file"
echo "  * Access to Qdrant vector database"
echo "  * Access to S3 buckets (if using S3 features)"
