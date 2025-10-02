#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
    echo "Environment variables loaded from .env"
else
    echo "Warning: .env file not found, proceeding without environment variables"
fi

# Set up virtual environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install development dependencies
echo "Installing development dependencies..."
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

# Install additional test dependencies if they exist
if [ -f requirements-dev.txt ]; then
    pip install -r requirements-dev.txt
fi

# Install common test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run tests
echo "Running tests..."
pytest tests/
