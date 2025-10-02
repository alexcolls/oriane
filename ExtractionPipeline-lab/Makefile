# Oriane Extraction Pipeline Makefile
# ====================================

.PHONY: help install extract resume clean test

# Default target
help:
	@echo "🎬 Oriane Extraction Pipeline - Make Commands"
	@echo "============================================="
	@echo ""
	@echo "Available targets:"
	@echo "  extract    - Activate virtual environment and run main.py"
	@echo "  resume     - Re-run extraction after crash (same as extract)"
	@echo "  install    - Install Python dependencies in virtual environment"
	@echo "  test       - Run test suite"
	@echo "  clean      - Clean up temporary files and cache"
	@echo ""
	@echo "Environment variables required:"
	@echo "  ORIANE_ADMIN_DB_URL - PostgreSQL database connection URL"
	@echo "  QDRANT_URL          - Qdrant vector database URL"
	@echo "  QDRANT_KEY          - Qdrant API key"
	@echo "  AWS_REGION          - AWS region for S3 storage"
	@echo "  AWS_ACCESS_KEY_ID   - AWS access key"
	@echo "  AWS_SECRET_ACCESS_KEY - AWS secret key"
	@echo ""

# Python virtual environment setup
VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

# Create virtual environment if it doesn't exist
$(VENV_DIR):
	@echo "📦 Creating Python virtual environment..."
	python3 -m venv $(VENV_DIR)
	@echo "✅ Virtual environment created at $(VENV_DIR)"

# Install dependencies
install: $(VENV_DIR)
	@echo "🔧 Installing Python dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Dependencies installed"

# Main extraction target
extract: $(VENV_DIR) install
	@echo "🚀 Starting extraction pipeline..."
	@echo "📊 Checking environment variables..."
	@if [ -z "$$ORIANE_ADMIN_DB_URL" ]; then \
		echo "❌ Error: ORIANE_ADMIN_DB_URL environment variable is required"; \
		exit 1; \
	fi
	@if [ -z "$$QDRANT_URL" ]; then \
		echo "❌ Error: QDRANT_URL environment variable is required"; \
		exit 1; \
	fi
	@if [ -z "$$QDRANT_KEY" ]; then \
		echo "❌ Error: QDRANT_KEY environment variable is required"; \
		exit 1; \
	fi
	@if [ -z "$$AWS_REGION" ]; then \
		echo "❌ Error: AWS_REGION environment variable is required"; \
		exit 1; \
	fi
	@echo "✅ Environment variables validated"
	@echo "🎬 Activating virtual environment and running main.py..."
	$(PYTHON) main.py

# Resume after crash (same as extract)
resume: extract

# Run test suite
test: $(VENV_DIR) install
	@echo "🧪 Running test suite..."
	$(PYTHON) -m pytest tests/ -v
	@echo "✅ Tests completed"

# Clean up
clean:
	@echo "🧹 Cleaning up temporary files..."
	rm -rf __pycache__/
	rm -rf **/__pycache__/
	rm -rf .pytest_cache/
	rm -rf *.log
	rm -rf checkpoint.txt
	@echo "✅ Cleanup completed"

# Help target (default)
.DEFAULT_GOAL := help
