#!/usr/bin/env bash
set -euo pipefail

IMAGE="extraction-pipeline"

docker build --no-cache -t $IMAGE .
