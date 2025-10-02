#!/bin/bash

# Activate the virtual environment
source .venv/bin/activate

# Run the FastAPI server with hot reload
uvicorn main:app --reload
