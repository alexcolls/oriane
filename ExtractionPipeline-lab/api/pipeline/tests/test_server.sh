#!/bin/bash

# test_server.sh - Smoke test for the server
# This script:
# 1. Starts the server in the background on a random free port
# 2. Waits for /health to return 200
# 3. Kills the server
# Returns non-zero on failure for CI

set -e  # Exit on any error

# Get the script directory and project root
SCRIPT_DIR="$(dirname "$(realpath "$0")")" 
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")" 

# Change to project root directory
cd "$PROJECT_ROOT"

# Function to find a free port
find_free_port() {
    python3 -c "import socket; s = socket.socket(); s.bind(('', 0)); print(s.getsockname()[1]); s.close()"
}

# Function to cleanup on exit
cleanup() {
    if [ ! -z "$SERVER_PID" ]; then
        echo "Killing server process $SERVER_PID"
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
}

# Set up trap to cleanup on exit
trap cleanup EXIT

# Find a free port
PORT=$(find_free_port)
echo "Using port $PORT for testing"

# Start the server in the background
echo "Starting server on port $PORT..."
python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port $PORT &
SERVER_PID=$!

echo "Server started with PID $SERVER_PID"

# Wait for server to be ready
echo "Waiting for server to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -f "http://localhost:$PORT/health" > /dev/null 2>&1; then
        echo "Server is ready!"
        break
    fi
    
    # Check if server process is still running
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo "ERROR: Server process died unexpectedly"
        exit 1
    fi
    
    ATTEMPT=$((ATTEMPT + 1))
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS - waiting for server..."
    sleep 1
done

# Check if we timed out
if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "ERROR: Server did not become ready within $MAX_ATTEMPTS seconds"
    exit 1
fi

# Test the health endpoint
echo "Testing health endpoint..."
RESPONSE=$(curl -s -w "%{http_code}" "http://localhost:$PORT/health")
HTTP_CODE=${RESPONSE: -3}
BODY=${RESPONSE%???}

if [ "$HTTP_CODE" != "200" ]; then
    echo "ERROR: Health check failed with HTTP code $HTTP_CODE"
    echo "Response body: $BODY"
    exit 1
fi

echo "SUCCESS: Health check passed with HTTP 200"
echo "Response: $BODY"

# Cleanup will be handled by the trap
echo "Smoke test completed successfully!"
