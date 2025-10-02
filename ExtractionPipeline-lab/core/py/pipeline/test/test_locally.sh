#!/usr/bin/env bash
set -euo pipefail

# ───────────── config ─────────────
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
LOG_FILE="$REPO_ROOT/test/test_locally.log"
JOB_INPUT_FILE="$REPO_ROOT/test/job_input.json"
EXTRAS_SCRIPT="$REPO_ROOT/lib/extras_gpu.sh"
REQ_HASH_FILE=".venv/.req_hash"
# ──────────────────────────────────

# ───────────── flags ──────────────
FORCE_REINSTALL=false
FORCE_EXTRAS=false
for arg in "$@"; do
  case "$arg" in
    --reinstall) FORCE_REINSTALL=true ;;
    --extras)    FORCE_EXTRAS=true    ;;
    *) echo "Unknown flag $arg" ; exit 1 ;;
  esac
done
# ──────────────────────────────────

log(){ echo -e "$*" | tee -a "$LOG_FILE" ; }
step_log(){ echo -e "\n🔸 $*" | tee -a "$LOG_FILE" ; }
info_log(){ echo -e "   ➜ $*" | tee -a "$LOG_FILE" ; }
success_log(){ echo -e "   ✅ $*" | tee -a "$LOG_FILE" ; }
error_log(){ echo -e "   ❌ $*" | tee -a "$LOG_FILE" ; }

log "\n🚀 ========== LOCAL PIPELINE TEST RUN ========== 🚀"
log "📅 Started at: $(date '+%Y-%m-%d %T')"
log "📁 Working directory: $REPO_ROOT"
log "📄 Log file: $LOG_FILE"
log "═══════════════════════════════════════════════════\n"

# ───── 1️⃣ ensure venv exists ─────
step_log "1️⃣ VIRTUAL ENVIRONMENT SETUP"
if [[ -d .venv ]]; then
    info_log "Virtual environment already exists at .venv"
else
    info_log "Creating new virtual environment at .venv"
    python3 -m venv .venv
    success_log "Virtual environment created successfully"
fi
info_log "Activating virtual environment"
source .venv/bin/activate
success_log "Virtual environment activated: $(which python)"

# ───── 2️⃣ install / update deps ──
step_log "2️⃣ DEPENDENCY MANAGEMENT"
if $FORCE_REINSTALL; then
    info_log "Force reinstall flag detected - reinstalling all dependencies"
    SETUP_START=$(date +%s)
    info_log "Upgrading pip to latest version"
    pip install --upgrade pip
    info_log "Force reinstalling all requirements from requirements.txt"
    pip install --force-reinstall --no-deps -r requirements.txt
    echo "forced" > "$REQ_HASH_FILE"
    SETUP_SEC=$(( $(date +%s) - SETUP_START ))
    success_log "Dependencies force-reinstalled successfully in ${SETUP_SEC}s"
else
    CUR_HASH=$(sha1sum requirements.txt)
    if [[ -f "$REQ_HASH_FILE" && "$(cat "$REQ_HASH_FILE")" == "$CUR_HASH" ]]; then
        info_log "Requirements hash unchanged - dependencies are up to date"
        success_log "Skipping dependency installation"
        SETUP_SEC=0
    else
        info_log "Requirements changed - updating dependencies"
        SETUP_START=$(date +%s)
        info_log "Upgrading pip to latest version"
        pip install --upgrade pip
        info_log "Installing/updating requirements from requirements.txt"
        pip install -r requirements.txt
        echo "$CUR_HASH" > "$REQ_HASH_FILE"
        SETUP_SEC=$(( $(date +%s) - SETUP_START ))
        success_log "Dependencies updated successfully in ${SETUP_SEC}s"
    fi
fi

# ───────────── 3️⃣ optional GPU extras ────────────
step_log "3️⃣ GPU ACCELERATION SETUP"
EXTRAS_SEC=0
if [[ -f "$EXTRAS_SCRIPT" ]]; then
  info_log "Found GPU extras script at: $EXTRAS_SCRIPT"
  chmod +x "$EXTRAS_SCRIPT"
  info_log "Checking GPU accelerators and ML frameworks"
  EXTRAS_START=$(date +%s)
  if $FORCE_EXTRAS; then
      info_log "Force extras flag detected - reinstalling all GPU packages"
      bash "$EXTRAS_SCRIPT" --force | tee -a "$LOG_FILE"
  else
      info_log "Running incremental GPU setup check"
      bash "$EXTRAS_SCRIPT"          | tee -a "$LOG_FILE"
  fi
  EXTRAS_SEC=$(( $(date +%s) - EXTRAS_START ))
  success_log "GPU acceleration setup completed in ${EXTRAS_SEC}s"
else
  info_log "GPU extras script not found at: $EXTRAS_SCRIPT"
  info_log "Skipping GPU acceleration setup"
fi

# ───── 4️⃣ JOB_INPUT env var ───────
step_log "4️⃣ JOB INPUT CONFIGURATION"
if [[ -f "$JOB_INPUT_FILE" ]]; then
    info_log "Found job input file at: $JOB_INPUT_FILE"
    info_log "Validating JSON format"
    if jq -e . "$JOB_INPUT_FILE" >/dev/null 2>&1; then
        export JOB_INPUT="$(jq -c '.' "$JOB_INPUT_FILE")"
        info_log "Job input parsed and exported to JOB_INPUT environment variable"
        info_log "Job contains $(echo "$JOB_INPUT" | jq '.items | length') items to process"
        success_log "Job configuration loaded successfully"
    else
        error_log "Invalid JSON format in job input file"
        exit 1
    fi
else
    error_log "Job input file not found at: $JOB_INPUT_FILE"
    exit 1
fi

# ───── 5️⃣ run pipeline ────────────
step_log "5️⃣ PIPELINE EXECUTION"
info_log "Starting video extraction pipeline with retry queue"
info_log "Command: python main.py"
info_log "All output will be logged to: $LOG_FILE"
PIPE_START=$(date +%s)
python main.py 2>&1 | tee -a "$LOG_FILE"
PIPE_SEC=$(( $(date +%s) - PIPE_START ))
success_log "Pipeline execution completed in $(printf "%02dm %02ds" $((PIPE_SEC/60)) $((PIPE_SEC%60)))"

# ───── 6️⃣ summary ─────────────────
step_log "6️⃣ EXECUTION SUMMARY"
log "\n📊 ═══════════ TIMING BREAKDOWN ═══════════"
printf "⏱️  SETUP TIME     : %02dm %02ds\n" $((SETUP_SEC/60)) $((SETUP_SEC%60)) | tee -a "$LOG_FILE"
printf "🎮 EXTRAS TIME    : %02dm %02ds\n" $((EXTRAS_SEC/60)) $((EXTRAS_SEC%60)) | tee -a "$LOG_FILE"
printf "🔄 PIPELINE TIME  : %02dm %02ds\n" $((PIPE_SEC/60))  $((PIPE_SEC%60))  | tee -a "$LOG_FILE"
TOTAL_SEC=$((SETUP_SEC + EXTRAS_SEC + PIPE_SEC))
printf "🏁 TOTAL TIME     : %02dm %02ds\n" $((TOTAL_SEC/60)) $((TOTAL_SEC%60)) | tee -a "$LOG_FILE"
log "\n📋 Full execution log saved to: $LOG_FILE"
log "🎉 Test execution completed successfully! 🎉\n"
