#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
    echo "Environment variables loaded from .env"
else
    echo "Warning: .env file not found"
    exit 1
fi

# Set default image name if not defined
if [ -z "$DOCKER_IMAGE_NAME" ]; then
    export DOCKER_IMAGE_NAME="extraction-pipeline"
    echo "Using default Docker image name: $DOCKER_IMAGE_NAME"
fi

# Set default tag if not defined
if [ -z "$DOCKER_TAG" ]; then
    export DOCKER_TAG="latest"
    echo "Using default Docker tag: $DOCKER_TAG"
fi

# Build the Docker image from the project root
echo "Building Docker image: $DOCKER_IMAGE_NAME:$DOCKER_TAG"
cd ../..
docker build -f api/pipeline/deploy/docker/Dockerfile -t $DOCKER_IMAGE_NAME:$DOCKER_TAG .
cd api/pipeline

# Check if image was built successfully
if [ $? -ne 0 ]; then
    echo "Error building Docker image"
    exit 1
fi

echo "Docker image built successfully: $DOCKER_IMAGE_NAME:$DOCKER_TAG"

# Check if nvidia-docker is available for GPU support
GPU_FLAG=""
if command -v nvidia-docker &> /dev/null || docker info 2>/dev/null | grep -q "nvidia"; then
    GPU_FLAG="--gpus all"
    echo "GPU support detected, running with GPU acceleration"
else
    echo "Running without GPU support"
fi

# Run Docker container
echo "Running Docker container..."
docker run $GPU_FLAG -p ${API_PORT:-8000}:${API_PORT:-8000} --env-file .env --name extraction-pipeline-container --rm $DOCKER_IMAGE_NAME:$DOCKER_TAG

