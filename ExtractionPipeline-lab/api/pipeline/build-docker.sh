#!/bin/bash

# Exit script on error
set -euo pipefail

# Get the script directory and project root
SCRIPT_DIR="$(dirname "$(realpath "$0")")" 
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Variables
IMAGE_NAME="pipeline-api"
DEV_CONTAINER_NAME="pipeline-api-dev"
PORT=8000

# Build the development Docker image
log() {
    echo -e "[INFO] $1"
}

log "Building Docker image..."
docker build --target dev -t $IMAGE_NAME:dev -f "$SCRIPT_DIR/deploy/docker/Dockerfile" "$PROJECT_ROOT"

# Run the Docker container
docker run -d --rm --name $DEV_CONTAINER_NAME -p $PORT:8000 $IMAGE_NAME:dev

# Basic test to verify the API is running on localhost
log "Testing the API..."

# Wait for the model to load (Jina model takes 2-3 minutes to download and load)
log "Waiting for model to load (this may take 2-3 minutes)..."

# Wait up to 5 minutes for the API to be ready
WAIT_TIME=300  # 5 minutes in seconds
COUNTER=0
INTERVAL=10

while [ $COUNTER -lt $WAIT_TIME ]; do
    if curl -sS http://localhost:$PORT/health > /dev/null 2>&1; then
        log "API is ready! Testing /docs endpoint..."
        break
    fi
    log "Waiting for API to be ready... ($COUNTER/$WAIT_TIME seconds)"
    sleep $INTERVAL
    COUNTER=$((COUNTER + INTERVAL))
done

if [ $COUNTER -ge $WAIT_TIME ]; then
    echo "[ERROR] API did not become ready within $WAIT_TIME seconds"
    docker stop $DEV_CONTAINER_NAME
    exit 1
fi

if curl -sS http://localhost:$PORT/docs > /dev/null; then
    log "API is running successfully on http://localhost:$PORT"
    # Optionally, more tests can be added here
else
    echo "[ERROR] API test failed."
    # Stop the container in case of failure
    docker stop $DEV_CONTAINER_NAME
    exit 1
fi

# Run ENTRYPOINT path regression test
log "Running ENTRYPOINT path regression test..."
if docker exec $DEV_CONTAINER_NAME /app/pipeline/tests/test_entrypoint_path.sh; then
    log "ENTRYPOINT path test passed"
else
    echo "[ERROR] ENTRYPOINT path test failed."
    docker stop $DEV_CONTAINER_NAME
    exit 1
fi

# Stop the container after test
docker stop $DEV_CONTAINER_NAME
log "Build and test completed successfully."
