#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path; import os, importlib
tasks = importlib.import_module("src.core.background.tasks")
print("ENTRYPOINT_PATH:", tasks.ENTRYPOINT_PATH)
assert Path(tasks.ENTRYPOINT_PATH).exists()
PY
