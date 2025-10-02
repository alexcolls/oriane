#!/usr/bin/env bash
set -euo pipefail
echo "→ GPU accelerator check"

# detect torch minor (e.g. '2.3')
TORCH_MINOR=$(python - <<'PY'
import importlib.metadata as im, re
print(re.match(r'^(\d+\.\d+)', im.version('torch')).group(1))
PY
)

# map torch → accelerator versions
case "$TORCH_MINOR" in
  2.3) FA="2.3.0.post1"; XF="0.0.27" ;;
  2.4) FA="2.4.2.post1"; XF="0.0.28" ;;
  2.5) FA="2.5.5.post1"; XF="0.0.29" ;;
  *)   echo "ℹ️  No flash-attn / xformers wheels for torch $TORCH_MINOR"; exit 0 ;;
esac

py_has() { python - "$@" <<'PY'
import importlib.metadata as im, sys
pkg, want = sys.argv[1], sys.argv[2]
try:
    sys.exit(0 if im.version(pkg).startswith(want) else 1)
except im.PackageNotFoundError:
    sys.exit(1)
PY
}

NEED=()
py_has flash_attn "$FA" || NEED+=("flash-attn==$FA")
py_has xformers   "$XF" || NEED+=("xformers==$XF")

if [[ ${#NEED[@]} -eq 0 ]]; then
  echo "✓ Correct flash-attn / xformers already installed"
  exit 0
fi

echo "→ Installing: ${NEED[*]}"
pip install --no-deps --force-reinstall \
  --extra-index-url https://download.pytorch.org/whl/cu121 \
  "${NEED[@]}" || echo "ℹ️  Wheels not found – skipped"
echo "✓ Accelerator step finished"
