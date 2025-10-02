"""
Phase 4 – Frame-level CLIP embeddings
────────────────────────────────────
* Lazy-loads **jina-clip-v2** once per process (CUDA if available, else CPU).
* Exposes two public helpers:
    • `encode_batch(images)`  – encode a list of Paths / PIL.Image objects
    • `encode_directory(path)` – convenience wrapper for a folder of *n_*.png*
* Every public helper is decorated with `@profile`, so wall-time / CPU / RAM /
  GPU usage lands in the global performance report.

This replaces the stand-alone *frames_embeddings.py* while keeping the identical
algorithmic behaviour (same model, same 512-D cosine-normalised vectors). :contentReference[oaicite:0]{index=0}
"""

from __future__ import annotations

import contextlib
import re
import time
from pathlib import Path
from typing import Iterable, List, Sequence, Union

import torch

if not hasattr(torch.backends.cuda, "is_flash_attention_available"):
    torch.backends.cuda.is_flash_attention_available = lambda: False

from config.env_config import settings
from config.logging_config import configure_logging
from config.profiler import profile
from PIL import Image
from sentence_transformers import SentenceTransformer

log = configure_logging()
__all__ = ["encode_image_batch", "encode_text_batch", "encode_directory"]

# --------------------------------------------------------------------------- #
# globals                                                                     #
# --------------------------------------------------------------------------- #
_MODEL: SentenceTransformer | None = None
_FRAME_RE = re.compile(r"^(?P<idx>\d+)_(?P<sec>\d+\.\d+)\.png$")  # 1_12.34.png


def _load_model() -> SentenceTransformer:
    """Singleton initialiser for jina-clip-v2."""
    global _MODEL
    if _MODEL is None:
        import os
        name = getattr(settings, "clip_model", "jinaai/jina-clip-v2")
        
        # Check CUDA availability at startup and log warning if not available
        if not torch.cuda.is_available():
            log.warning("⚠️ CUDA is not available! The model will run on CPU which may be significantly slower. "
                       "Please check your CUDA installation and GPU drivers.")
        
        # Check if CPU is forced via environment variable
        force_cpu = os.getenv("FORCE_CPU", "0") == "1"
        device = "cuda" if torch.cuda.is_available() and not force_cpu else "cpu"
        
        if force_cpu:
            log.info("🔧 FORCE_CPU is enabled - using CPU device even if CUDA is available")
        
        t0 = time.perf_counter()
        _MODEL = SentenceTransformer(
            name,
            device=device,
            trust_remote_code=True,
        )
        log.info(f"[clip] loaded {name} on {device} in {time.perf_counter()-t0:.1f}s")
    return _MODEL


# --------------------------------------------------------------------------- #
# public helpers                                                              #
# --------------------------------------------------------------------------- #


@profile
def encode_text_batch(
    texts: Sequence[str],
    *,
    batch_size: int | None = None,
    normalize: bool = True,
) -> List[List[float]]:
    """
    Encode a list of text strings to CLIP vectors.
    """
    model = _load_model()
    # This directly encodes text without trying to open files
    vecs = model.encode(
        texts,
        batch_size=batch_size or settings.batch_size,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
        show_progress_bar=False,
    )
    if vecs.shape[1] != settings.dim:
        vecs = vecs[:, : settings.dim]
    return [v.tolist() for v in vecs]


@profile
def encode_image_batch(
    images: Sequence[Union[str, Path, Image.Image]],
    *,
    batch_size: int | None = None,
    normalize: bool = True,
) -> List[List[float]]:
    """
    Encode images to 512-d CLIP vectors with automatic OOM back-off.

    Strategy
    --------
    1. Try the requested `batch_size` on GPU.
    2. On CUDA OOM → halve the batch until 1.
    3. If still OOM at 1 → move model to CPU, warn about ETA.
    4. Any other RuntimeError propagates upward.
    """
    # ---------- prepare inputs ------------------------------------
    pil_imgs: list[Image.Image] = [
        (
            img.convert("RGB")
            if isinstance(img, Image.Image)
            else Image.open(Path(img)).convert("RGB")
        )
        for img in images
    ]

    model = _load_model()
    device_type = model.device.type
    bs_requested = batch_size or settings.batch_size
    bs_current = max(1, bs_requested)
    tried_cpu = False
    warned_cpu = False

    # Log encoding start
    log.debug(
        f"🖼️ [embed] starting batch encoding of {len(pil_imgs)} images with batch_size={bs_current}"
    )

    while True:
        try:
            autocast_ctx = (
                torch.cuda.amp.autocast()
                if model.device.type == "cuda"
                else contextlib.nullcontext()
            )
            with torch.inference_mode(), autocast_ctx:
                vecs = model.encode(
                    pil_imgs,
                    batch_size=bs_current,
                    convert_to_numpy=True,
                    normalize_embeddings=normalize,
                    show_progress_bar=False,
                )
            torch.cuda.empty_cache()
            if vecs.shape[1] != settings.dim:
                vecs = vecs[:, : settings.dim]
            log.debug(f"✅ [embed] successfully encoded {len(vecs)} image vectors")
            return [v.tolist() for v in vecs]  # ← SUCCESS

        # ---------- CUDA OOM: back-off -----------------------------
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            if bs_current > 1:
                bs_current //= 2
                log.warning(f"[embed] CUDA OOM – retrying with batch_size={bs_current}")
                continue
            if not tried_cpu:
                log.warning("[embed] switching to CPU after repeated OOM")
                model.to("cpu")
                tried_cpu = True
                device_type = "cpu"
                continue
            raise  # already on CPU

        # ---------- CPU OOM (rare) -------------------------------
        except RuntimeError as e:
            if "out of memory" in str(e).lower() and device_type == "cpu":
                if not warned_cpu:
                    warned_cpu = True
                    eta = len(pil_imgs) * 6  # rough: 6 s / img on laptop
                    log.warning(
                        f"[embed] CPU out of mem but continuing; "
                        f"expect ~{eta}s for {len(pil_imgs)} frame(s)"
                    )
                raise
            raise  # propagate other errors


@profile
def encode_directory(
    frames_dir: Path, *, batch_size: int | None = None, normalize: bool = True
) -> List[List[float]]:
    """
    Convenience helper – encode **all** `<n>_<sec>.png` frames in a folder.

    Returns vectors in chronological order (same order as the filenames).
    """
    paths = sorted(
        [p for p in frames_dir.glob("*.png") if _FRAME_RE.match(p.name)],
        key=lambda p: int(_FRAME_RE.match(p.name)["idx"]),
    )
    if not paths:
        log.warning(f"[embed] no frames found in {frames_dir}")
        return []

    log.info(f"[embed] encoding {len(paths)} frames from {frames_dir.name}")
    return encode_image_batch(paths, batch_size=batch_size, normalize=normalize)


# --------------------------------------------------------------------------- #
# CLI convenience                                                             #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Encode frames in a directory with jina-clip-v2.")
    parser.add_argument("framedir", type=Path, help="directory of n_*.png frames")
    parser.add_argument("-o", "--out", type=Path, help="write embeddings to this JSON lines file")
    parser.add_argument("--no-normalize", action="store_true", help="skip L2 normalisation")
    parser.add_argument("--bs", type=int, help="override batch size")
    args = parser.parse_args()

    vecs = encode_directory(
        args.framedir,
        batch_size=args.bs,
        normalize=not args.no_normalize,
    )

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w") as f:
            for v in vecs:
                f.write(json.dumps(v) + "\n")
        print(f"Wrote {len(vecs)} vectors → {args.out}")
    else:
        print(f"Encoded {len(vecs)} frames (first vector length = {len(vecs[0])})")
