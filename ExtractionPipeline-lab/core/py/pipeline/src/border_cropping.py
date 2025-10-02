"""
Phase 1 – Border-crop (GPU accelerated)
───────────────────────────────────────
Public helpers
──────────────
crop_video(src:Path, dst:Path|None=None)  → Path
batch_crop(videos:Iterable[Path])         → list[Path]

All ffmpeg parameters are picked from `settings` so you can tweak them in
environment variables without touching code.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, List, Optional

from config.env_config import settings
from config.logging_config import configure_logging
from config.profiler import profile
from lib.ffmpeg_utils import detect_crop_ffmpeg, run_ffmpeg_crop

log = configure_logging()
__all__ = ["crop_video", "batch_crop"]


# ───────────────────── helper utils ──────────────────────
def _dst_for(src: Path, tmp_dir: Optional[Path] = None) -> Path:
    """Return destination path inside tmp/videos preserving file-name."""
    base = tmp_dir or settings.tmp_dir
    base.mkdir(parents=True, exist_ok=True)
    return base / src.name


def _copy(src: Path, dst: Path) -> None:
    dst.write_bytes(src.read_bytes())


# ─────────────────────── public API ──────────────────────
@profile
def crop_video(src: Path, dst: Path | None = None) -> Path:
    """
    Detect crop rectangle and re-encode one video.

    • If detection fails, the original file is copied 1-to-1.
    • Returns the path that now contains the processed clip.
    """
    dst = _dst_for(src) if dst is None else dst
    if dst.exists():
        log.debug(f"[crop] skip existing {dst.name}")
        return dst

    # 1) detect borders --------------------------------------------
    rect = detect_crop_ffmpeg(
        str(src),
        probes=settings.crop_probes,
        clip_secs=settings.crop_clip_secs,
        safe_margin_px=settings.crop_safe_margin,
        hwaccel=settings.crop_hwaccel,
        cropdetect_params=settings.crop_detect_args,
    )

    # 2) act on result ---------------------------------------------
    if rect:
        log.debug(f"🎬 [crop] {src.name} detected borders ✂️ applying crop {rect}")
        try:
            run_ffmpeg_crop(
                src,
                dst,
                rect,
                encoder=settings.crop_encoder,
                preset=settings.crop_preset,
                tune=settings.crop_tune,
                cq=settings.crop_cq,
            )
        except Exception as e:
            log.exception(f"❌ [crop] ffmpeg failed – falling back to copy: {e}")
            _copy(src, dst)
    else:
        log.warning(f"⚠️ [crop] {src.name} no borders detected 📋 copying original")
        _copy(src, dst)

    return dst


@profile
def batch_crop(videos: Iterable[Path], max_workers: int | None = None) -> List[Path]:
    """
    Crop many videos concurrently, preserving input order.
    """
    vids = list(videos)
    if not vids:
        return []

    max_workers = max_workers or settings.max_workers
    out: List[Path] = [None] * len(vids)  # type: ignore

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        fut_map = {pool.submit(crop_video, v): idx for idx, v in enumerate(vids)}
        for fut in as_completed(fut_map):
            idx = fut_map[fut]
            try:
                out[idx] = fut.result()
            except Exception:
                log.exception(f"[crop] error processing {vids[idx].name}")

    return out


# ───────────────────── CLI convenience ───────────────────
if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Border-crop one or more videos.")
    p.add_argument("files", nargs="+", help="input .mp4 files")
    p.add_argument("-o", "--out", type=Path, help="override tmp directory")
    args = p.parse_args()

    targets = [Path(f).expanduser().resolve() for f in args.files]
    if len(targets) == 1:
        res = crop_video(targets[0], _dst_for(targets[0], args.out))
        print(res)
    else:
        outs = batch_crop(targets, settings.max_workers)
        print("\n".join(str(p) for p in outs))
