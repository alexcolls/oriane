#!/usr/bin/env bash
set -euo pipefail

JOB_INPUT=$(jq -c . < job_input.json)

docker run --rm --gpus all \
  --env-file "$(realpath ../../.env)" \
  --env "JOB_INPUT=$JOB_INPUT"  \
  extraction-pipeline
