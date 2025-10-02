"""
Phase 3 – Duplicate-frame removal
─────────────────────────────────
Duplicate detection uses a perceptual Difference-Hash (dHash) on
the *processed* PNGs produced by scene_extract.py.

Public API
──────────
remove_duplicates(frames: Iterable[Path],
                  *,
                  delete: bool = True) -> list[Path]

Returns the list of **kept** frame paths in chronological order.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import cv2
import numpy as np
from config.env_config import settings  # global, frozen Settings dataclass
from config.logging_config import configure_logging
from config.profiler import profile

log = configure_logging()
__all__ = ["remove_duplicates"]

# --------------------------------------------------------------------------- #
# internal helpers – perceptual hash                                          #
# (ported 1-to-1 from crop_n_frame.py)                                         #
# --------------------------------------------------------------------------- #


def dhash(image: np.ndarray, hash_size: int = getattr(settings, "dhash_size", 8)) -> int:
    """
    Compute the Difference Hash (dHash) for an image.

    Equivalent to the original helper in crop_n_frame.py (Phase-3). :contentReference[oaicite:0]{index=0}
    """
    if image is None:
        raise ValueError("Input image for dhash cannot be None.")

    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (hash_size + 1, hash_size))
    except cv2.error:  # fallback on broken frames
        return hash(image.tobytes()[:128])

    diff = resized[:, 1:] > resized[:, :-1]
    return int(sum(2**i for i, v in enumerate(diff.flatten()) if v))


def _sorted_frame_paths(frames: Iterable[Path]) -> List[Path]:
    """
    Chronological sort by the integer prefix “<idx>_…png”.
    """
    return sorted(frames, key=lambda p: int(p.stem.split("_")[0]) if "_" in p.stem else -1)


# --------------------------------------------------------------------------- #
# public API                                                                  #
# --------------------------------------------------------------------------- #


@profile
def remove_duplicates(frames: Iterable[Path], *, delete: bool = True) -> List[Path]:
    """
    Remove perceptually duplicate frames.

    Parameters
    ----------
    frames : Iterable[Path]
        PNG paths (as returned by scene_extract.extract_frames).
    delete : bool, default True
        When True, duplicate files are unlinked from disk; otherwise they
        are left untouched but excluded from the returned list.

    Returns
    -------
    list[Path]
        The paths that were retained, sorted chronologically.
    """
    frame_paths = _sorted_frame_paths(frames)
    if not frame_paths:
        log.warning("[dedup] no frames supplied – skipping")
        return []

    log.info(f"🔍 [dedup] processing {len(frame_paths)} frames for duplicates")

    hashes: Dict[int, Path] = {}
    kept: List[Path] = []
    removed = 0

    for p in frame_paths:
        img = cv2.imread(str(p))
        if img is None:  # unreadable → keep to inspect later
            log.warning(f"[dedup] could not read {p.name}, keeping")
            kept.append(p)
            continue

        h = dhash(img)
        if h in hashes:
            log.debug(f"[dedup] {p.name} duplicate of {hashes[h].name}")
            removed += 1
            if delete:
                try:
                    p.unlink()
                except OSError as e:
                    log.error(f"[dedup] could not delete {p.name}: {e}")
            # do NOT add to kept list
        else:
            hashes[h] = p
            kept.append(p)

    log.info(f"✅ [dedup] kept {len(kept)}, removed {removed} duplicates")
    return kept


# --------------------------------------------------------------------------- #
# CLI convenience                                                             #
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Remove duplicate frames via dHash.")
    parser.add_argument("folders", nargs="+", help="folders or individual PNGs")
    parser.add_argument(
        "--keep", action="store_true", help="keep duplicate PNG files on disk (just report)"
    )
    args = parser.parse_args()

    for target in map(Path, args.folders):
        if target.is_dir():
            frames = list(target.glob("*.png"))
        else:
            frames = [target]

        kept = remove_duplicates(frames, delete=not args.keep)
        print(f"{target}: kept {len(kept)} frame(s)")
