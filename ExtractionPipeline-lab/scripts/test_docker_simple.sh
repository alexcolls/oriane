#!/bin/bash

set -e

echo "==============================================="
echo "Testing Pipeline API with Docker (Simple)"
echo "==============================================="

# Variables
DOCKER_IMAGE="pipeline-api-simple:latest"
CONTAINER_NAME="pipeline-api-test"
API_PORT=8001

# Create a simplified Dockerfile for testing
echo "Creating simplified Dockerfile for testing..."
cat > Dockerfile.simple << 'EOF'
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser && \
    chown -R appuser:appuser /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Switch to non-root user
USER appuser

# Create directories
RUN mkdir -p /app/.output/tmp/videos /app/.output/tmp/frames /app/.output/logs /app/.output/reports

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create a test requirements.txt with minimal dependencies
echo "Creating test requirements file..."
cat > requirements.test.txt << 'EOF'
fastapi>=0.104.0,<1.0.0
uvicorn[standard]>=0.24.0,<1.0.0
python-dotenv>=1.0,<2.0
python-multipart>=0.0.6,<1.0.0
pydantic>=2.4.0,<3.0.0
httpx>=0.25.0,<1.0.0
python-jose[cryptography]>=3.3.0,<4.0.0
passlib[bcrypt]>=1.7.4,<2.0.0
requests>=2.31.0,<3.0.0
EOF

# Create test environment file
echo "Creating test environment file..."
cat > .env.test << 'EOF'
API_NAME=Pipeline API Docker Test
API_PORT=8000
API_KEY=docker-test-key-123
API_USERNAME=testuser
API_PASSWORD=testpass
MAX_VIDEOS_PER_REQUEST=10
VP_OUTPUT_DIR=/app/.output
DEBUG_PIPELINE=1
LOCAL_MODE=1
SKIP_UPLOAD=1
EOF

# Build Docker image
echo "Building Docker image..."
docker build -f Dockerfile.simple -t $DOCKER_IMAGE .

# Run Docker container
echo "Running Docker container..."
docker run -d \
    --name $CONTAINER_NAME \
    -p $API_PORT:8000 \
    -e API_KEY=docker-test-key-123 \
    -e API_NAME="Pipeline API Docker Test" \
    -e LOCAL_MODE=1 \
    -e SKIP_UPLOAD=1 \
    $DOCKER_IMAGE

# Wait for container to start
echo "Waiting for container to start..."
sleep 10

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    rm -f Dockerfile.simple requirements.test.txt .env.test
}
trap cleanup EXIT

# Test Docker container health
echo "Testing Docker container health..."
for i in {1..30}; do
    if curl -sf http://localhost:$API_PORT/health; then
        echo -e "\n✅ Docker health check passed"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Docker health check failed after 30 attempts"
        docker logs $CONTAINER_NAME
        exit 1
    fi
    sleep 1
done

# Test root endpoint
echo "Testing root endpoint..."
curl -sf http://localhost:$API_PORT/ | python3 -m json.tool

# Test configuration endpoint
echo "Testing configuration endpoint..."
curl -sf http://localhost:$API_PORT/config | python3 -m json.tool

# Test process endpoint with API key
echo "Testing process endpoint..."
RESPONSE=$(curl -X POST "http://localhost:$API_PORT/process" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: docker-test-key-123" \
    -d '{
        "items": [
            {
                "platform": "instagram",
                "code": "test123"
            }
        ]
    }')

echo "Process endpoint response: $RESPONSE"

# Test jobs endpoint
echo "Testing jobs endpoint..."
curl -sf http://localhost:$API_PORT/jobs \
    -H "X-API-Key: docker-test-key-123" | python3 -m json.tool

echo -e "\n==============================================="
echo "Docker tests completed successfully! ✅"
echo "Container logs:"
docker logs $CONTAINER_NAME --tail 20
echo "==============================================="
