"""
Low-level ffmpeg helpers
────────────────────────
detect_crop_ffmpeg(...)  – probe three spots with cropdetect and union boxes
run_ffmpeg_crop(...)     – NVENC (or CPU) crop-&-re-encode

Every threshold / encoder knob is a *function arg* instead of a module constant,
so the caller can pass env-driven values from `video_pipeline.config.settings`.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# discover binaries once
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"


# ───────────────────────── helpers ──────────────────────────
def _ffprobe_val(src: str, key: str) -> str:
    return (
        subprocess.check_output(
            [
                FFPROBE,
                "-v",
                "quiet",
                "-select_streams",
                "v:0",
                "-show_entries",
                f"stream={key}",
                "-of",
                "csv=p=0",
                src,
            ],
            text=True,
        )
        .strip()
        .lower()
    )


# ─────────────────────── public API ─────────────────────────
def detect_crop_ffmpeg(
    src: str,
    *,
    probes: int = 3,
    clip_secs: int = 2,
    safe_margin_px: int = 4,
    hwaccel: str = "cuda",  # "cuda" | "vaapi" | "" (CPU)
    cropdetect_params: str = "24:16:0",
) -> Optional[Tuple[int, int, int, int]]:
    """
    Estimate crop rectangle.

    Parameters
    ----------
    src : str
        Input video path.
    probes : int
        How many evenly-spaced timestamps to analyse.
    clip_secs : int
        Seconds of video to search at each timestamp.
    safe_margin_px : int
        Pixels added as safety to each edge of the union box.
    hwaccel : str
        ffmpeg `-hwaccel` value; empty string disables HW accel.
    cropdetect_params : str
        Value passed to cropdetect filter, e.g. "24:16:0".

    Returns
    -------
    (x, y, w, h) or None
    """
    dur = float(_ffprobe_val(src, "duration") or 0)
    if dur == 0:
        return None

    rects = []
    for k in range(probes):
        ts = dur * (k + 1) / (probes + 1)
        cmd = [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{ts:.3f}",
            "-t",
            str(clip_secs),
        ]
        if hwaccel:
            cmd += ["-hwaccel", hwaccel]
        cmd += [
            "-i",
            src,
            "-vf",
            f"cropdetect={cropdetect_params}",
            "-an",
            "-f",
            "null",
            "-",
        ]
        out = subprocess.run(cmd, capture_output=True, text=True).stderr
        m = re.findall(r"crop=([0-9:]+)", out)
        if m:
            w, h, x, y = map(int, m[-1].split(":"))
            rects.append((x, y, w, h))

    if not rects:
        return None

    x0 = min(r[0] for r in rects) - safe_margin_px
    y0 = min(r[1] for r in rects) - safe_margin_px
    x1 = max(r[0] + r[2] for r in rects) + safe_margin_px
    y1 = max(r[1] + r[3] for r in rects) + safe_margin_px
    return max(0, x0), max(0, y0), x1 - x0, y1 - y0


def run_ffmpeg_crop(
    src: Path,
    dst: Path,
    rect: Tuple[int, int, int, int],
    *,
    encoder: str = "h264_nvenc",
    preset: str = "p5",
    tune: str = "hq",
    cq: str = "23",
) -> Path:
    """
    Crop and re-encode one video.

    All encoder settings are keyword args so callers can override easily.
    """
    x, y, w, h = rect
    w += w % 2  # NVENC requires even width/height
    h += h % 2

    cmd = [
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-vf",
        f"crop=w={w}:h={h}:x={x}:y={y},setsar=1:1,format=nv12",
        "-c:v",
        encoder,
        "-preset",
        preset,
        "-tune",
        tune,
        "-cq",
        cq,
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        "-y",
        str(dst),
    ]
    subprocess.run(cmd, check=True)
    return dst
