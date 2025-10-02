#!/bin/bash

# Get the script directory and project root
SCRIPT_DIR="$(dirname "$(realpath "$0")")" 
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if we're running in a Docker container
if [ -f /.dockerenv ]; then
    # Running in Docker - just run uvicorn directly
    uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
else
    # Running locally - use virtual environment
    # Change to project root directory
    cd "$PROJECT_ROOT"
    
    # Activate the virtual environment
    source "$PROJECT_ROOT/.venv/bin/activate"
    
    # Run the FastAPI server with hot reload
    uvicorn src.api.app:app --reload
fi
