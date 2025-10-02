#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
    echo "Environment variables loaded from .env"
else
    echo "Warning: .env file not found"
    exit 1
fi

# Set default API_PORT if not defined
if [ -z "$API_PORT" ]; then
    echo "API_PORT not defined in .env, using default 8000"
    export API_PORT=8000
fi

echo "Starting development server on port $API_PORT..."
uvicorn api.app:app --reload --port $API_PORT
