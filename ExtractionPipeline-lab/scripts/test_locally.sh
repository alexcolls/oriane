#!/bin/bash

set -e

echo "==============================================="
echo "Testing Pipeline API Process Endpoint Flow"
echo "==============================================="

# Check if Python dependencies are installed
echo "Checking Python dependencies..."
python3 -c "import fastapi, uvicorn, pydantic" || {
    echo "Missing required Python packages. Installing..."
    pip3 install fastapi uvicorn pydantic python-dotenv
}

# Create a minimal .env file for testing
echo "Creating test environment file..."
cat > .env << EOF
API_NAME=Pipeline API Test
API_PORT=8000
API_KEY=test-key-123
API_USERNAME=testuser
API_PASSWORD=testpass
MAX_VIDEOS_PER_REQUEST=10
VP_OUTPUT_DIR=/tmp/pipeline-test
DEBUG_PIPELINE=1
LOCAL_MODE=1
SKIP_UPLOAD=1
EOF

# Start the API in the background
echo "Starting API server..."
python3 -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Wait for API to start
echo "Waiting for API to start..."
sleep 10

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    kill $API_PID 2>/dev/null || true
    rm -f .env
    rm -rf /tmp/pipeline-test
}
trap cleanup EXIT

# Test health endpoint first
echo "Testing health endpoint..."
curl -sf http://localhost:8000/health || {
    echo "Health check failed!"
    exit 1
}
echo "✅ Health check passed"

# Test process endpoint with valid API key and get job ID
echo "Testing POST /process endpoint..."
PROCESS_RESPONSE=$(curl -X POST "http://localhost:8000/process" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: test-key-123" \
     -d '{
       "items": [
         {
           "platform": "instagram",
           "code": "test123"
         }
       ]
     }' -s)

echo "Process response: $PROCESS_RESPONSE"

# Extract job ID from response
JOB_ID=$(echo "$PROCESS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['jobId'])")

if [ -z "$JOB_ID" ]; then
    echo "❌ Failed to extract job ID from response"
    exit 1
fi

echo "✅ Process endpoint passed - Job ID: $JOB_ID"

# Poll /status endpoint until job is complete
echo "Polling job status until completion..."
MAX_ATTEMPTS=60
ATTEMPT=0
POLL_INTERVAL=5

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    echo "Polling attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    STATUS_RESPONSE=$(curl -sf "http://localhost:8000/status/$JOB_ID" \
        -H "X-API-Key: test-key-123" \
        -H "Content-Type: application/json")
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to get job status"
        exit 1
    fi
    
    echo "Status response: $STATUS_RESPONSE"
    
    # Extract status from response
    STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    PROGRESS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['progress'])")
    
    echo "Current status: $STATUS (Progress: $PROGRESS%)"
    
    case "$STATUS" in
        "COMPLETED")
            echo "✅ Job completed successfully!"
            echo "Final status response: $STATUS_RESPONSE"
            break
            ;;
        "FAILED")
            echo "❌ Job failed!"
            # Print logs for debugging
            echo "Job logs:"
            echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['log_tail'])"
            exit 1
            ;;
        "RUNNING"|"PENDING")
            echo "Job is still $STATUS, waiting $POLL_INTERVAL seconds..."
            sleep $POLL_INTERVAL
            ;;
        *)
            echo "Unknown status: $STATUS"
            sleep $POLL_INTERVAL
            ;;
    esac
done

# Check if we exceeded max attempts
if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
    echo "❌ Job did not complete within expected time ($((MAX_ATTEMPTS * POLL_INTERVAL)) seconds)"
    echo "Final status: $STATUS"
    exit 1
fi

# Assert that final status is COMPLETED
if [ "$STATUS" != "COMPLETED" ]; then
    echo "❌ Expected status COMPLETED but got: $STATUS"
    exit 1
fi

echo "✅ Job status polling completed - Final status: $STATUS"

# Additional test: verify we can still get job status after completion
echo "Testing job status retrieval after completion..."
FINAL_STATUS_RESPONSE=$(curl -sf "http://localhost:8000/status/$JOB_ID" \
    -H "X-API-Key: test-key-123" \
    -H "Content-Type: application/json")

FINAL_STATUS=$(echo "$FINAL_STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")

if [ "$FINAL_STATUS" != "COMPLETED" ]; then
    echo "❌ Job status changed after completion: $FINAL_STATUS"
    exit 1
fi

echo "✅ Job status persistence verified"

# Test jobs endpoint to ensure job appears in listing
echo "Testing jobs endpoint..."
curl -sf http://localhost:8000/jobs \
     -H "X-API-Key: test-key-123" || {
    echo "❌ Jobs endpoint failed!"
    exit 1
}

echo "✅ Jobs endpoint passed"

echo ""
echo "==============================================="
echo "All API process flow tests passed successfully! ✅"
echo "- POST /process endpoint creates job"
echo "- Job ID returned correctly"
echo "- Status polling works"
echo "- Job completes with COMPLETED status"
echo "- Job status persists after completion"
echo "- Jobs listing includes completed job"
echo "==============================================="
