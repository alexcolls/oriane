#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="extraction-pipeline:dev"
LOG_FILE="test/test_docker.log"
JOB_JSON_FILE="test/job_input.json"
ENV_FILE=".env"

log() { echo -e "$*" | tee -a "$LOG_FILE" ; }

log "\n========== DOCKER TEST RUN: $(date '+%Y-%m-%d %H:%M:%S') ==========\n"

# ---------------------------------------------------------------------
# 1) Build Docker image (always)  – measure time
# ---------------------------------------------------------------------
log "🔨 docker build -t $IMAGE_TAG ."
t0=$(date +%s)
docker build -t "$IMAGE_TAG" . 2>&1 | tee -a "$LOG_FILE"
t1=$(date +%s)
BUILD_SEC=$((t1 - t0))
log "✅ Image built in $BUILD_SEC sec\n"

# ---------------------------------------------------------------------
# 2) Run container with JOB_INPUT + AWS creds – measure time
# ---------------------------------------------------------------------
if [[ ! -f "$JOB_JSON_FILE" ]]; then
  log "❌  $JOB_JSON_FILE not found"; exit 1
fi
JOB_JSON=$(jq -c . "$JOB_JSON_FILE")

log "🚀 docker run $IMAGE_TAG"
t0=$(date +%s)
docker run --rm \
  --env-file "$ENV_FILE" \
  -e "JOB_INPUT=$JOB_JSON" \
  -v "$HOME/.aws:/root/.aws:ro" \
  --gpus all \
  "$IMAGE_TAG" 2>&1 | tee -a "$LOG_FILE"
t1=$(date +%s)
RUN_SEC=$((t1 - t0))

# ---------------------------------------------------------------------
# 3) Summary
# ---------------------------------------------------------------------
log "\n──────── SUMMARY ────────"
printf "BUILD TIME    : %02dm %02ds\n" $((BUILD_SEC/60)) $((BUILD_SEC%60)) | tee -a "$LOG_FILE"
printf "CONTAINER TIME: %02dm %02ds\n" $((RUN_SEC/60))  $((RUN_SEC%60))  | tee -a "$LOG_FILE"
log "Log written to $LOG_FILE\n"
