# =============================================================================
# Multi-stage Dockerfile for FastAPI Search Service with GPU Support
# =============================================================================
# This Dockerfile creates a production-ready container for the FastAPI search
# service with CUDA support for GPU acceleration.
#
# Build stages:
#   1. base: Common dependencies and Python setup
#   2. dev: Development dependencies and tools
#   3. prod: Production image with minimal dependencies
#
# Usage:
#   docker build -t search-api:latest .
#   docker build --target dev -t search-api:dev .
#
# =============================================================================

# Stage 1: Base image with CUDA support
FROM ubuntu:22.04 as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    pkg-config \
    libhdf5-dev \
    libopencv-dev \
    ffmpeg \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app/search

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set up Python environment
ENV PATH="/home/appuser/.local/bin:$PATH"
RUN python3 -m pip install --user --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN python3 -m pip install --user -r requirements.txt

# Stage 2: Development image
FROM base as dev

# Install development dependencies
RUN python3 -m pip install --user \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    flake8 \
    mypy \
    isort

# Copy development scripts
COPY --chown=appuser:appuser scripts/run-dev.sh scripts/run-tests.sh ./
RUN chmod +x run-dev.sh run-tests.sh

# Development command
CMD ["./run-dev.sh"]

# Stage 3: Production image
FROM base as prod

# Copy application code (search source tree)
COPY --chown=appuser:appuser . .

# Create symbolic links for shared modules
RUN ln -sf /app/shared/auth /app/search/auth && \
    ln -sf /app/shared/config /app/search/config

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${API_PORT:-8000}/health || exit 1

# Expose port
EXPOSE ${API_PORT:-8000}

# Production command
CMD ["python3", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "${API_PORT:-8000}"]

# =============================================================================
# Build Instructions:
# 
# Development build:
#   docker build --target dev -t search-api:dev .
#
# Production build:
#   docker build --target prod -t search-api:prod .
#
# Run development container:
#   docker run -p 8000:8000 -v $(pwd):/app/search search-api:dev
#
# Run production container:
#   docker run -p 8000:8000 search-api:prod
#
# Run with GPU support:
#   docker run --gpus all -p 8000:8000 search-api:prod
# =============================================================================
