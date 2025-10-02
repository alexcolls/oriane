#!/usr/bin/env bash
set -euo pipefail

# Ensure jq is available
command -v jq >/dev/null || { echo "ERROR: jq is required but not installed" >&2; exit 1; }

PAYLOAD_FILE="sample.json"
[[ -f "$PAYLOAD_FILE" ]] || { echo "ERROR: Payload file '$PAYLOAD_FILE' not found" >&2; exit 1; }

# Read and JSON-encode the entire file (escaping quotes and newlines)
ENCODED_PAYLOAD=$(jq -Rs . "$PAYLOAD_FILE")

echo ">>> Encoded JOB_INPUT payload:"
echo "$ENCODED_PAYLOAD"

# Build the overrides JSON with a simple cat-heredoc
OVERRIDES=$(cat <<EOF
{"environment":[{"name":"JOB_INPUT","value":$ENCODED_PAYLOAD}]}
EOF
)

echo ">>> Container overrides:"
echo "$OVERRIDES"

echo "Submitting Batch job..."
aws batch submit-job \
  --job-name test-job-extraction \
  --job-queue ExtractionGPU_Queue \
  --job-definition ExtractionGPU_JobDef \
  --container-overrides "$OVERRIDES" \
  --region us-east-1

echo "✅ Submitted successfully"
