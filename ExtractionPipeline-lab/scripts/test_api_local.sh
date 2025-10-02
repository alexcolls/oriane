#!/bin/bash

set -e

echo "==============================================="
echo "Testing Pipeline API Locally"
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
EOF

# Start the API in the background
echo "Starting API server..."
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Wait for API to start
echo "Waiting for API to start..."
sleep 5

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    kill $API_PID 2>/dev/null || true
    rm -f .env
    rm -rf /tmp/pipeline-test
}
trap cleanup EXIT

# Test health endpoint
echo "Testing health endpoint..."
curl -sf http://localhost:8000/health || {
    echo "Health check failed!"
    exit 1
}

echo -e "\n✅ Health check passed"

# Test root endpoint
echo "Testing root endpoint..."
curl -sf http://localhost:8000/ || {
    echo "Root endpoint failed!"
    exit 1
}

echo -e "\n✅ Root endpoint passed"

# Test configuration endpoint
echo "Testing configuration endpoint..."
curl -sf http://localhost:8000/config || {
    echo "Config endpoint failed!"
    exit 1
}

echo -e "\n✅ Configuration endpoint passed"

# Test process endpoint with valid API key
echo "Testing process endpoint..."
curl -X POST "http://localhost:8000/process" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: test-key-123" \
     -d '{
       "items": [
         {
           "platform": "instagram",
           "code": "test123"
         }
       ]
     }' || {
    echo "Process endpoint failed!"
    exit 1
}

echo -e "\n✅ Process endpoint passed"

# Test job listing endpoint
echo "Testing jobs endpoint..."
curl -sf http://localhost:8000/jobs \
     -H "X-API-Key: test-key-123" || {
    echo "Jobs endpoint failed!"
    exit 1
}

echo -e "\n✅ Jobs endpoint passed"

echo -e "\n==============================================="
echo "All API tests passed successfully! ✅"
echo "==============================================="
