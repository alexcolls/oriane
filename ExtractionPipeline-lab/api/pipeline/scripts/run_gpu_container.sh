#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
    echo "Environment variables loaded from .env"
else
    echo "Warning: .env file not found"
    exit 1
fi

# Set default values if not defined in .env
if [ -z "$API_PORT" ]; then
    echo "API_PORT not defined in .env, using default 8000"
    export API_PORT=8000
fi

if [ -z "$DOCKER_IMAGE_NAME" ]; then
    export DOCKER_IMAGE_NAME="extraction-pipeline"
    echo "Using default Docker image name: $DOCKER_IMAGE_NAME"
fi

if [ -z "$DOCKER_TAG" ]; then
    export DOCKER_TAG="latest"
    echo "Using default Docker tag: $DOCKER_TAG"
fi

# Check if Docker image exists
if ! docker images | grep -q "$DOCKER_IMAGE_NAME"; then
    echo "Docker image $DOCKER_IMAGE_NAME:$DOCKER_TAG not found. Please build it first using scripts/docker_build.sh"
    exit 1
fi

# Check if nvidia-docker is available
if ! command -v nvidia-docker &> /dev/null && ! docker info 2>/dev/null | grep -q "nvidia"; then
    echo "Warning: NVIDIA Docker runtime not detected. GPU support may not be available."
fi

# Run Docker container with GPU support
echo "Running Docker container with GPU support..."
echo "Image: $DOCKER_IMAGE_NAME:$DOCKER_TAG"
echo "Port mapping: $API_PORT:$API_PORT"

docker run --gpus all \
    -p $API_PORT:$API_PORT \
    --env-file .env \
    --name extraction-pipeline-container \
    --rm \
    $DOCKER_IMAGE_NAME:$DOCKER_TAG
