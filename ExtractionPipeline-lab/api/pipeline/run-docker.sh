#!/usr/bin/env bash
set -euo pipefail

# Script to run the Docker development container


echo "Starting Docker development container..."

# Check if port 8000 is in use
if lsof -i :8000 >/dev/null 2>&1; then
    echo "Port 8000 is already in use. Finding and stopping processes..."
    PIDS=$(lsof -ti :8000 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo "Stopping processes: $PIDS"
        kill $PIDS
        sleep 2
    fi
fi

# Remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^pipeline-api-dev$"; then
    echo "Removing existing pipeline-api-dev container..."
    docker rm -f pipeline-api-dev
fi

# Get the script directory and project root
SCRIPT_DIR="$(dirname "$(realpath "$0")")" 
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Variables
IMAGE_NAME="pipeline-api"
DEV_CONTAINER_NAME="pipeline-api-dev"
PORT=8000

# Run the container with volume mount for development
echo "Starting pipeline-api-dev container..."

# Check if model cache exists
if [ -d "$SCRIPT_DIR/.model-cache" ]; then
    echo "📁 Using pre-downloaded model cache..."
    MODEL_CACHE_MOUNT="-v $SCRIPT_DIR/.model-cache:/home/appuser/.cache/huggingface"
else
    echo "⚠️  No model cache found. Model will be downloaded on first run."
    MODEL_CACHE_MOUNT=""
fi

if docker run -d \
    -p 8000:8000 \
    --name pipeline-api-dev \
    -v "$SCRIPT_DIR:/app/pipeline" \
    $MODEL_CACHE_MOUNT \
    pipeline-api:dev \
    ./run-dev.sh; then
    
    # Wait for the API to be ready (model loading takes 2-3 minutes)
    echo "⏳ Waiting for API to be ready (this may take 2-3 minutes for model loading)..."
    
    # Wait up to 5 minutes for the API to be ready
    WAIT_TIME=300  # 5 minutes in seconds
    COUNTER=0
    INTERVAL=10
    
    while [ $COUNTER -lt $WAIT_TIME ]; do
        if curl -sS http://localhost:$PORT/health > /dev/null 2>&1; then
            echo "✅ API is ready!"
            break
        fi
        
        # Check if container is still running
        if ! docker ps --format '{{.Names}}' | grep -q "^$DEV_CONTAINER_NAME$"; then
            echo "❌ Container stopped unexpectedly. Check logs with: docker logs $DEV_CONTAINER_NAME"
            exit 1
        fi
        
        echo "⏳ Waiting for API to be ready... ($COUNTER/$WAIT_TIME seconds)"
        sleep $INTERVAL
        COUNTER=$((COUNTER + INTERVAL))
    done
    
    if [ $COUNTER -ge $WAIT_TIME ]; then
        echo "❌ API did not become ready within $WAIT_TIME seconds"
        echo "Check logs with: docker logs $DEV_CONTAINER_NAME"
        exit 1
    fi
    
    echo "✅ Container started successfully!"
    echo "📡 API is available at: http://localhost:$PORT"
    echo "📖 API docs: http://localhost:$PORT/docs"
    echo "📋 To view logs: docker logs -f $DEV_CONTAINER_NAME"
    echo "🛑 To stop: docker stop $DEV_CONTAINER_NAME"
else
    echo "❌ Failed to start Docker container"
    exit 1
fi
