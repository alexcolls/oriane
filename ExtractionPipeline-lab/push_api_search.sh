#!/bin/bash
# push_image.sh — build & push oriane-search-api-v1 to ECR without sudo
set -e

# ───────────────────────────────────────────────────────────────
# Configuration
# ───────────────────────────────────────────────────────────────
ACCOUNT_ID="509399609859"
AWS_REGION="us-east-1"
IMAGE_NAME="oriane-search-api-v1"
ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}"

# ───────────────────────────────────────────────────────────────
# Colors for output (if TTY)
# ───────────────────────────────────────────────────────────────
if [ -t 1 ]; then
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  NC='\033[0m'
else
  GREEN='' ; YELLOW='' ; NC=''
fi

# ───────────────────────────────────────────────────────────────
# Cleanup function
# ───────────────────────────────────────────────────────────────
cleanup() {
  echo -e "${YELLOW}Cleaning up temporary files...${NC}"
  rm -f "${IMAGE_NAME}.tar"
  echo -e "${GREEN}Cleanup complete${NC}"
}

echo -e "${YELLOW}Starting deployment process...${NC}"

# ───────────────────────────────────────────────────────────────
# Ensure ECR repository exists
# ───────────────────────────────────────────────────────────────
if ! aws ecr describe-repositories \
      --repository-names "${IMAGE_NAME}" \
      --region "${AWS_REGION}" \
      >/dev/null 2>&1; then
  echo -e "${YELLOW}Creating ECR repository...${NC}"
  aws ecr create-repository \
      --repository-name "${IMAGE_NAME}" \
      --region "${AWS_REGION}"
fi

# ───────────────────────────────────────────────────────────────
# Authenticate Docker with ECR
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}Authenticating with ECR...${NC}"
aws ecr get-login-password \
    --region "${AWS_REGION}" \
  | docker login \
      --username AWS \
      --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# ───────────────────────────────────────────────────────────────
# Build Docker image
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}Building Docker image...${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

if ! docker build --platform linux/amd64 \
    --file "${SCRIPT_DIR}/api/search/Dockerfile" \
    --tag "${IMAGE_NAME}:latest" \
    "${SCRIPT_DIR}"; then
  echo "Error: Docker build failed"
  exit 1
fi

# ───────────────────────────────────────────────────────────────
# Save & reload image to ensure clean tags
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}Saving Docker image to tar file...${NC}"
docker save -o "${IMAGE_NAME}.tar" "${IMAGE_NAME}:latest"

echo -e "${YELLOW}Removing local Docker image...${NC}"
docker rmi "${IMAGE_NAME}:latest" || true

echo -e "${YELLOW}Loading Docker image from tar file...${NC}"
docker load -i "${IMAGE_NAME}.tar"

# ───────────────────────────────────────────────────────────────
# Tag & push to ECR
# ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}Tagging image for ECR...${NC}"
docker tag "${IMAGE_NAME}:latest" "${ECR_REPO}:latest"

echo -e "${YELLOW}Pushing image to ECR (may take a while)...${NC}"
if command -v timeout &>/dev/null; then
  timeout 3000 docker push "${ECR_REPO}:latest"
  status=$?
  if [ $status -eq 124 ]; then
    echo "Error: Docker push timed out"
    exit 1
  elif [ $status -ne 0 ]; then
    echo "Error: Docker push failed"
    exit $status
  fi
else
  docker push "${ECR_REPO}:latest"
fi

# ───────────────────────────────────────────────────────────────
# Cleanup & finish
# ───────────────────────────────────────────────────────────────
cleanup
echo -e "${GREEN}Image deployment completed successfully!${NC}"
