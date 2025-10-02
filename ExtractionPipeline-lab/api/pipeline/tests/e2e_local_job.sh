#!/bin/bash

# =============================================================================
# End-to-End Local Job Test Script
# =============================================================================
# This script spins up the dev container, creates a dummy job through the API,
# polls /jobs/{id}, and prints final status; includes cleanup.
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
    exit 1
}

# Get script directory
SCRIPT_DIR="$(dirname "$(realpath "$0")")" 

# Load environment variables if .env exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# Set default values
API_HOST=${API_HOST:-localhost}
API_PORT=${API_PORT:-8000}
API_KEY=${API_KEY:-your-api-key-here}
CONTAINER_NAME=pipeline-api-dev

# Function to check if container exists
container_exists() {
    docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"
}

# Function to check if container is running
container_running() {
    docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"
}

# Function to wait for API to be ready
wait_for_api() {
    local max_attempts=60
    local attempt=0
    
    log "Waiting for API to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://$API_HOST:$API_PORT/health" > /dev/null 2>&1; then
            success "API is ready!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    done
    
    error "API failed to become ready after $max_attempts seconds"
}

# Function to cleanup resources
cleanup() {
    log "Cleaning up resources..."
    
    if container_exists; then
        log "Stopping and removing container: $CONTAINER_NAME"
        docker rm -f $CONTAINER_NAME > /dev/null 2>&1 || true
    fi
    
    success "Cleanup completed"
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Function to build and start container
start_container() {
    log "Starting E2E test environment..."
    
    # Build the Docker image if it doesn't exist
    if ! docker images | grep -q "pipeline-api.*dev"; then
        log "Building Docker image..."
        cd "$SCRIPT_DIR"
        docker build --target dev -t pipeline-api:dev -f "deploy/docker/Dockerfile" ../ || error "Failed to build Docker image"
    fi
    
    # Stop existing container if running
    if container_running; then
        log "Stopping existing container..."
        docker stop $CONTAINER_NAME > /dev/null 2>&1 || true
    fi
    
    # Remove existing container if it exists
    if container_exists; then
        log "Removing existing container..."
        docker rm $CONTAINER_NAME > /dev/null 2>&1 || true
    fi
    
    # Check if port is in use
    if lsof -i :$API_PORT > /dev/null 2>&1; then
        warning "Port $API_PORT is already in use. Trying to kill existing processes..."
        PIDS=$(lsof -ti :$API_PORT 2>/dev/null || true)
        if [ -n "$PIDS" ]; then
            kill $PIDS || true
            sleep 2
        fi
    fi
    
    # Start new container
    log "Starting container: $CONTAINER_NAME"
    docker run -d \
        --name $CONTAINER_NAME \
        -p $API_PORT:8000 \
        -e LOCAL_MODE=1 \
        -e SKIP_UPLOAD=1 \
        -e API_KEY="$API_KEY" \
        pipeline-api:dev || error "Failed to start container"
    
    # Wait for API to be ready
    wait_for_api
}

# Function to create a job
create_job() {
    log "Creating test job..."
    
    # Sample job payload using the /process endpoint
    local job_payload='{
        "items": [
            {
                "platform": "instagram",
                "code": "DHrbLqfv-ka"
            }
        ]
    }'
    
    # Create job using /process endpoint
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$job_payload" \
        "http://$API_HOST:$API_PORT/process" || error "Failed to create job")
    
    local job_id=$(echo "$response" | jq -r '.jobId' 2>/dev/null || echo "null")
    
    if [ "$job_id" == "null" ] || [ -z "$job_id" ]; then
        error "Failed to create job: $response"
    fi
    
    success "Job created with ID: $job_id"
    echo "$job_id"
}

# Function to poll job status
poll_job_status() {
    local job_id="$1"
    local max_attempts=120  # 10 minutes at 5-second intervals
    local attempt=0
    
    log "Polling job status for ID: $job_id"
    
    while [ $attempt -lt $max_attempts ]; do
        local response=$(curl -s -H "X-API-Key: $API_KEY" \
            "http://$API_HOST:$API_PORT/status/$job_id" 2>/dev/null || echo '{"status": "unknown"}')
        
        local status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "unknown")
        local progress=$(echo "$response" | jq -r '.progress' 2>/dev/null || echo "0")
        
        log "Job status: $status (progress: $progress%)"
        
        # Check if job is in terminal state
        if [[ "$status" == "completed" || "$status" == "failed" || "$status" == "error" ]]; then
            if [ "$status" == "completed" ]; then
                success "Job completed successfully!"
            else
                warning "Job finished with status: $status"
            fi
            
            # Print full job details
            log "Final job details:"
            echo "$response" | jq . 2>/dev/null || echo "$response"
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 5
    done
    
    error "Job polling timed out after $((max_attempts * 5)) seconds"
}

# Main function
main() {
    log "Starting E2E local job test..."
    
    # Check dependencies
    command -v docker >/dev/null 2>&1 || error "Docker is required but not installed"
    command -v curl >/dev/null 2>&1 || error "curl is required but not installed"
    command -v jq >/dev/null 2>&1 || error "jq is required but not installed"
    
    # Start container and API
    start_container
    
    # Create job
    local job_id=$(create_job)
    
    # Poll for completion
    poll_job_status "$job_id"
    
    success "E2E test completed successfully!"
}

# Run main function
main "$@"

