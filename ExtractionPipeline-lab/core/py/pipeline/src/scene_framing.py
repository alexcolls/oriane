"""
Phase 2 – Scene-frame extraction
────────────────────────────────
1. Use `ffmpeg` scene-change detection to grab candidate key-frames.
2. Remove obvious black / solid-colour / letter-boxed frames.
3. Guarantee ≥ settings.min_frames by falling back to uniform sampling.
4. Crop inner borders per frame.
5. Save cleaned PNGs in chronological order: `1_<sec>.png`, `2_<sec>.png`, …

Public API
──────────
* `extract_frames(video: Path, outdir: Path | None = None) -> list[Path]`

Returns the list of written frame paths (chronological order).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import cv2
import numpy as np
from config.env_config import settings
from config.logging_config import configure_logging
from config.profiler import profile

log = configure_logging()
__all__ = ["extract_frames"]


# ────────────────────────── non-informational checks ───────────────────
def _is_solid_color(img: np.ndarray) -> bool:
    if img is None:
        return True
    h, w = img.shape[:2]
    if h < settings.solid_min_dim or w < settings.solid_min_dim:
        return _is_mono(img)
    b, g, r = cv2.split(img)
    return (
        np.std(b) < settings.solid_std_thresh
        and np.std(g) < settings.solid_std_thresh
        and np.std(r) < settings.solid_std_thresh
    )


def _is_mono(img: np.ndarray) -> bool:
    if img is None:
        return True
    if img.ndim == 3 and img.shape[2] == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif img.ndim == 2:
        gray = img
    else:
        return False
    return np.all(gray == gray[0, 0])


# ───────────────────────── internal crop detector ──────────────────────
def _detect_inner_crop(
    img: np.ndarray, tol: int = settings.tolerance
) -> Optional[Tuple[int, int, int, int]]:
    """Detect letter-box / pillar-box borders – return (x, y, w, h) or None."""
    if img is None:
        return None
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return None

    # ensure 3-channel BGR
    if img.ndim == 2:
        img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    else:
        img_bgr = img

    def _blank(line: np.ndarray) -> bool:
        med = np.median(line, axis=0)
        return np.all(np.sum(np.abs(line.astype(np.int32) - med.astype(np.int32)), axis=1) <= tol)

    x0 = next((x for x in range(w) if not _blank(img_bgr[:, x, :])), w)
    x1 = next((x for x in range(w - 1, -1, -1) if not _blank(img_bgr[:, x, :])), 0)
    y0 = next((y for y in range(h) if not _blank(img_bgr[y, :, :])), h)
    y1 = next((y for y in range(h - 1, -1, -1) if not _blank(img_bgr[y, :, :])), 0)

    if x0 >= x1 or y0 >= y1:
        return None
    return x0, y0, x1 - x0, y1 - y0


# ───────────────────────── ffmpeg scene helper ──────────────────────────
@profile
def _ffmpeg_scene_frames(src: str, tmp: Path, thresh: float) -> List[Path]:
    """
    Call ffmpeg’s scene filter and return PNG files in `tmp`, sorted by PTS.
    """
    import subprocess
    from shutil import which

    ffmpeg = which("ffmpeg") or "ffmpeg"

    tmp.mkdir(parents=True, exist_ok=True)
    pattern = str(tmp / "%d.png")

    # escape comma inside select filter
    select = f"select='gt(scene\\,{thresh})'"

    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        src,
        "-vf",
        select,
        "-vsync",
        "vfr",
        "-frame_pts",
        "1",
        "-q:v",
        "2",
        pattern,
    ]
    subprocess.run(cmd, check=True)

    return sorted(tmp.glob("*.png"), key=lambda p: int(p.stem))


# ───────────────────────── frame save helper ────────────────────────────
def _process_and_save(img: np.ndarray, outdir: Path, ts: float, seq_idx: int) -> bool:
    """
    Crop inner borders, re-check informativeness, write PNG.
    Returns True when the frame is kept.
    """
    if img is None:
        return False

    # internal crop (letter-box / pillar-box)
    rect = _detect_inner_crop(img)
    if rect:
        x, y, w, h = rect
        if w <= 0 or h <= 0:
            return False
        img = img[y : y + h, x : x + w]

    if img.shape[0] < 1 or img.shape[1] < 1:
        return False
    if _is_solid_color(img) or _is_mono(img):
        return False

    fname = f"{seq_idx}_{ts:.2f}.png"
    try:
        cv2.imwrite(str(outdir / fname), img)
        return True
    except Exception as e:  # pragma: no cover
        log.warning(f"[frame-save] could not write {fname}: {e}")
        return False


# ─────────────────────────── public API ────────────────────────────────
@profile
def extract_frames(
    video: Path,
    outdir: Path | None = None,
    min_frames: int | None = None,
    scene_thresh: float | None = None,
) -> List[Path]:
    """
    Extract cleaned, chronological PNG frames for *one* video.

    • `outdir` defaults to settings.frames_dir / <video-stem>
    • Returns list of written frame paths.
    """
    min_frames = min_frames or settings.min_frames
    scene_thresh = scene_thresh or settings.scene_thresh

    outdir = outdir or (settings.frames_dir / video.stem)
    outdir.mkdir(parents=True, exist_ok=True)

    log.info(
        f"🎬 [extract] Starting scene extraction for {video.name} ➡ {outdir.relative_to(outdir.parent.parent)}"
    )

    # ------------------------------------------------------------------ #
    # 1) initial candidate frames via ffmpeg scene detection             #
    # ------------------------------------------------------------------ #
    log.debug(f"🔍 [extract] Initiating ffmpeg scene detection with threshold={scene_thresh}.")
    tmp_scene = outdir / "_scene_tmp"
    scene_paths = _ffmpeg_scene_frames(str(video), tmp_scene, scene_thresh)
    log.debug(f"✅ [extract] ffmpeg identified {len(scene_paths)} potential scene changes.")

    # ------------------------------------------------------------------ #
    # 2) FPS / total frame probe                                         #
    # ------------------------------------------------------------------ #
    cap_probe = cv2.VideoCapture(str(video))
    fps = cap_probe.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap_probe.get(cv2.CAP_PROP_FRAME_COUNT))
    cap_probe.release()

    # ------------------------------------------------------------------ #
    # 3) collect candidates (timestamp, image)                           #
    # ------------------------------------------------------------------ #
    candidates: List[Tuple[float, np.ndarray]] = []
    for p in scene_paths:
        idx_raw = p.stem
        try:
            ts = (float(idx_raw) / fps) if fps > 0 else float(idx_raw)
        except ValueError:
            log.debug(f"[{video.name}] skip unparsable {p.name}")
            continue
        img = cv2.imread(str(p))
        if img is None or _is_solid_color(img) or _is_mono(img):
            continue
        candidates.append((ts, img))

    # ------------------------------------------------------------------ #
    # 4) fallback: uniform sampling if too few frames                    #
    # ------------------------------------------------------------------ #
    if len(candidates) < min_frames:
        need = min_frames - len(candidates)
        step = max(1, total_frames // (need + 1)) if total_frames else 1
        cap = cv2.VideoCapture(str(video))
        added = 0
        attempts = 0
        while added < need and attempts < need * 5:
            pos = (attempts * step) % total_frames if total_frames else attempts
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ok, frame = cap.read()
            attempts += 1
            if not ok:
                break
            ts = pos / fps if fps > 0 else float(pos)
            if _is_solid_color(frame) or _is_mono(frame):
                continue
            candidates.append((ts, frame))
            added += 1
        cap.release()

    # ------------------------------------------------------------------ #
    # 5) chronological sort & save                                       #
    # ------------------------------------------------------------------ #
    candidates.sort(key=lambda x: x[0])  # by timestamp
    saved: List[Path] = []
    seq = 1
    for ts, img in candidates:
        if _process_and_save(img, outdir, ts, seq):
            saved.append(outdir / f"{seq}_{ts:.2f}.png")
            seq += 1

    log.info(f"[extract] {video.name}: kept {len(saved)} frames")
    # clean up tmp
    if tmp_scene.exists():
        try:
            import shutil

            shutil.rmtree(tmp_scene)
        except OSError:
            pass

    return saved
