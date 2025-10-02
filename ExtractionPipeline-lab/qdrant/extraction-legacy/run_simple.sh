#!/bin/bash

# Simple Instagram Video Processor Runner with Full Logging
# ========================================================
# Loads environment and runs the simplified processor with comprehensive logging

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Setup logging
LOG_FILE="$SCRIPT_DIR/simple_processor.log"
ERROR_LOG="$SCRIPT_DIR/simple_processor_errors.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Enhanced logging functions (similar to test_locally.sh)
log() { echo -e "$*" | tee -a "$LOG_FILE" ; }
step_log() { echo -e "\n🔸 $*" | tee -a "$LOG_FILE" ; }
info_log() { echo -e "   ➜ $*" | tee -a "$LOG_FILE" ; }
success_log() { echo -e "   ✅ $*" | tee -a "$LOG_FILE" ; }
error_log() { echo -e "   ❌ $*" | tee -a "$LOG_FILE" ; }

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE" >&2
}

# Initialize log files
log "\n🚀 ========== SIMPLE INSTAGRAM VIDEO PROCESSOR ========== 🚀"
log "📅 Started at: $(date '+%Y-%m-%d %T')"
log "📁 Working directory: $SCRIPT_DIR"
log "📄 Log file: $LOG_FILE"
log "🔴 Error log: $ERROR_LOG"
log "═══════════════════════════════════════════════════════════\n"

# Load environment files
step_log "1️⃣ ENVIRONMENT CONFIGURATION"

if [[ -f ".env" ]]; then
    info_log "Loading local environment: .env"
    set -a  # Export all variables
    source .env
    set +a  # Stop exporting
else
    error_log "Local .env file not found!"
    exit 1
fi

if [[ -f "../../core/py/pipeline/.env" ]]; then
    info_log "Loading core pipeline environment: ../../core/py/pipeline/.env"
    set -a  # Export all variables
    source ../../core/py/pipeline/.env
    set +a  # Stop exporting
else
    error_log "Core pipeline .env file not found!"
    exit 1
fi

# Check required environment variables
if [[ -z "${ORIANE_ADMIN_DB_URL:-}" ]]; then
    error_log "ORIANE_ADMIN_DB_URL environment variable is required"
    exit 1
fi

success_log "Environment loaded successfully!"

# Default arguments (optimized for GPU memory)
BATCH_SIZE=1000
MAX_WORKERS=4

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --max-workers)
            MAX_WORKERS="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--batch-size N] [--max-workers N]"
            echo "  --batch-size N    Number of videos per batch (default: 1000)"
            echo "  --max-workers N   Number of parallel workers (default: 1)"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Activate virtual environment
step_log "2️⃣ VIRTUAL ENVIRONMENT ACTIVATION"
if [[ -f ".venv/bin/activate" ]]; then
    info_log "Activating virtual environment..."
    source .venv/bin/activate
    info_log "Virtual environment activated: $VIRTUAL_ENV"
    info_log "Python executable: $(which python)"
    info_log "Python version: $(python --version)"
    success_log "Virtual environment ready"
else
    error_log "Virtual environment not found!"
    error_log "Please run setup_env.py first to create the virtual environment:"
    error_log "  python3 setup_env.py"
    exit 1
fi

# Clear GPU memory before starting
step_log "3️⃣ GPU MEMORY CLEANUP"
info_log "Clearing GPU memory and lingering processes..."
python3 clear_gpu_memory.py
success_log "GPU cleanup completed"

# Run the processor
step_log "4️⃣ PROCESSOR EXECUTION"
info_log "Starting Instagram Video Processor..."
info_log "Batch size: $BATCH_SIZE"
info_log "Max workers: $MAX_WORKERS"
info_log "All output will be logged to: $LOG_FILE"
info_log "Full error details will be logged to: $ERROR_LOG"

echo -e "${GREEN}"
echo "🎬 =================================================="
echo "   Simple Instagram Video Processor"
echo "   Batch size: $BATCH_SIZE | Workers: $MAX_WORKERS"
echo "=================================================="
echo -e "${NC}"

# Execute with full logging
PROC_START=$(date +%s)
python3 simple_processor.py --batch-size "$BATCH_SIZE" --max-workers "$MAX_WORKERS" 2>&1
PROC_SEC=$(( $(date +%s) - PROC_START ))

exit_code=$?

if [[ $exit_code -eq 0 ]]; then
    log_success "Processing completed successfully!"
else
    log_error "Processing failed with exit code: $exit_code"
fi

exit $exit_code
