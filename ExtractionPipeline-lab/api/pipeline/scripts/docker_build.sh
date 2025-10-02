#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
    echo "Environment variables loaded from .env"
else
    echo "Warning: .env file not found, proceeding without environment variables"
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

# Build Docker image with CUDA support
echo "Building Docker image: $DOCKER_IMAGE_NAME:$DOCKER_TAG"
echo "Building with python3 binary and CUDA libraries..."

# Create Dockerfile if it doesn't exist
if [ ! -f Dockerfile ]; then
    echo "Creating Dockerfile with CUDA support..."
    cat > Dockerfile << 'EOF'
# Use Python 3.11 slim base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python3", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
fi

# Build the Docker image
docker build -t $DOCKER_IMAGE_NAME:$DOCKER_TAG .

echo "Docker image built successfully: $DOCKER_IMAGE_NAME:$DOCKER_TAG"
