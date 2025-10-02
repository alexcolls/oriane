from __future__ import annotations

"""Embeddings service

Provides thin convenience wrappers around the central CLIP embedding
utilities that live under `core/py/pipeline/src` so that the API layer
can stay agnostic of the underlying module layout.
"""

import sys
from functools import lru_cache
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _ensure_pipeline_on_path() -> None:
    """Add the pipeline root to *sys.path* once.

    The core embedding logic resides under
    `core/py/pipeline/src/infer_embeds.py`.  Because this folder isn't
    installed as a Python package, we extend *sys.path* at runtime so that
    `import src.infer_embeds` succeeds from anywhere in the repo.
    """
    current_file = Path(__file__).resolve()
    # We expect the repo layout: <repo_root>/core/py/pipeline/src
    # current_file = <repo_root>/api/services/embeddings_service.py
    repo_root = current_file.parents[2]  # ascend from 'services' -> 'api' -> repo
    pipeline_root = repo_root / "core" / "py" / "pipeline"
    if pipeline_root.exists():
        sys.path.insert(0, str(pipeline_root))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_text_embedding(prompt: str) -> List[float]:
    """Return a single CLIP embedding for *prompt* (L2-normalised)."""
    _ensure_pipeline_on_path()

    # Import lazily so that heavy model initialisation only happens when
    # embeddings are actually requested.
    from src.infer_embeds import encode_text_batch  # pylint: disable=import-error

    return encode_text_batch([prompt])[0]


def get_image_embedding(image) -> List[float]:
    """Return a single CLIP embedding for an image (L2-normalised).

    Args:
        image: PIL Image object or image data that can be processed by the CLIP model

    Returns:
        List[float]: The embedding vector for the image
    """
    _ensure_pipeline_on_path()

    # Import lazily so that heavy model initialisation only happens when
    # embeddings are actually requested.
    from src.infer_embeds import encode_image_batch  # pylint: disable=import-error

    return encode_image_batch([image])[0]
