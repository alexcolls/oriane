#!/usr/bin/env python3
"""
Fast batch-cropper
──────────────────
Dependencies:  python 3.9+,  numpy,  opencv-python,  FFmpeg ≥ 4.0
Optional:      FFmpeg built with hwaccel (nvdec/qsv/v4l2)
"""

import os, re, sys, shutil, math, subprocess, multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from glob import glob
from pathlib import Path
from typing import Iterator, Tuple, Optional

import cv2
import numpy as np

# ─── CONFIG ───────────────────────────────────────────────────────────────────
INPUT_DIR      = Path("../videos")
OUTPUT_DIR     = Path("cropped_videos_fast")
SAMPLE_FPS     = 1          # frames per second to inspect
TOLERANCE      = 5          # median-border diff threshold
EDGE_THRESH    = 10         # Sobel heat threshold
MIN_CROP_RATIO = 0.10       # need ≥ 10 % trim to keep crop
DOWNSCALE      = 0.5        # 50 % resolution for analysis
FFMPEG         = "ffmpeg"
FFPROBE        = "ffprobe"
MAX_WORKERS    = os.cpu_count() or 4
# ───────────────────────────────────────────────────────────────────────────────


# ╭───────────────────────── Utility helpers ─────────────────────────╮
def ffprobe_json(path: str) -> dict:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-print_format", "json", "-show_format",
         "-show_streams", path],
        stdout=subprocess.PIPE, text=True, check=True
    ).stdout
    import json
    return json.loads(out)


def video_info(path: str) -> Tuple[int, int, float]:
    meta = ffprobe_json(path)
    vstream = next(s for s in meta["streams"] if s["codec_type"] == "video")
    w, h = int(vstream["width"]), int(vstream["height"])
    duration = float(meta["format"]["duration"])
    return w, h, duration


def even(x: int) -> int:                   # FFmpeg needs even dims for yuv
    return x if x % 2 == 0 else x + 1
# ╰───────────────────────────────────────────────────────────────────╯


# ╭───────────────── Frame generator via FFmpeg pipe ─────────────────╮
def iter_sampled_frames(path: str, orig_w: int, orig_h: int
                        ) -> Iterator[np.ndarray]:
    sw, sh = even(int(orig_w * DOWNSCALE)), even(int(orig_h * DOWNSCALE))
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error",
           "-hwaccel", "auto",          # falls back to software if unavailable
           "-i", path,
           "-vf", f"fps={SAMPLE_FPS},scale={sw}:{sh}",
           "-pix_fmt", "rgb24",
           "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=sw * sh * 3)
    frame_bytes = sw * sh * 3
    try:
        while True:
            raw = proc.stdout.read(frame_bytes)
            if len(raw) < frame_bytes:
                break
            yield np.frombuffer(raw, np.uint8).reshape(sh, sw, 3)
    finally:
        proc.stdout.close()
        proc.wait()
# ╰───────────────────────────────────────────────────────────────────╯


# ╭─────────────── Median-border crop (unchanged maths) ──────────────╮
def detect_median_crop(path: str, orig_w: int, orig_h: int
                       ) -> Optional[Tuple[int, int, int, int]]:
    rects = []
    for small in iter_sampled_frames(path, orig_w, orig_h):
        edges = np.vstack([small[0], small[-1], small[:, 0], small[:, -1]])
        median_border = np.median(edges, axis=0)
        diff = np.abs(small.astype(np.int16) - median_border.astype(np.int16)
                      ).sum(axis=2)
        mask = diff > TOLERANCE
        coords = np.column_stack(np.where(mask))
        if coords.size:
            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0)
            rects.append((x0, y0, x1 - x0, y1 - y0))

    if not rects:
        return None

    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    w1 = max(r[0] + r[2] for r in rects)
    h1 = max(r[1] + r[3] for r in rects)

    scale = 1 / DOWNSCALE
    return (int(x0 * scale), int(y0 * scale),
            int((w1 - x0) * scale), int((h1 - y0) * scale))
# ╰───────────────────────────────────────────────────────────────────╯


# ╭──────────────── Gradient-heat crop (unchanged maths) ─────────────╮
def detect_gradient_crop(path: str, orig_w: int, orig_h: int
                         ) -> Optional[Tuple[int, int, int, int]]:
    heatmap = None
    for small in iter_sampled_frames(path, orig_w, orig_h):
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
        sx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        edges = cv2.magnitude(sx, sy)
        heatmap = edges if heatmap is None else heatmap + edges

    if heatmap is None:
        return None

    norm = cv2.normalize(heatmap, None, 0, 255,
                         cv2.NORM_MINMAX).astype(np.uint8)
    _, mask = cv2.threshold(norm, EDGE_THRESH, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                               cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None

    x, y, w, h = cv2.boundingRect(max(cnts, key=cv2.contourArea))
    scale = 1 / DOWNSCALE
    return (int(x * scale), int(y * scale),
            int(w * scale), int(h * scale))
# ╰───────────────────────────────────────────────────────────────────╯


def should_crop(orig_w: int, orig_h: int, rect) -> bool:
    x, y, w, h = rect
    return ((orig_w - w) / orig_w >= MIN_CROP_RATIO or
            (orig_h - h) / orig_h >= MIN_CROP_RATIO)


# ╭────────────────────── Crop or copy with FFmpeg ───────────────────╮
def crop_video(src: str, rect, dst: str):
    x, y, w, h = rect
    dst = str(dst)
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error",
           "-hwaccel", "auto",
           "-i", src,
           "-vf", f"crop={w}:{h}:{x}:{y}",
           "-c:v", "libx264", "-preset", "fast", "-crf", "23",
           "-c:a", "copy",
           dst]
    subprocess.run(cmd, check=True)
# ╰───────────────────────────────────────────────────────────────────╯


# ╭──────────────────── Per-file worker function ─────────────────────╮
def process_video(src: str) -> str:
    fname = Path(src).name
    dst = OUTPUT_DIR / fname

    try:
        orig_w, orig_h, _ = video_info(src)

        rect = detect_median_crop(src, orig_w, orig_h)
        method = "median"

        if not rect or not should_crop(orig_w, orig_h, rect):
            rect2 = detect_gradient_crop(src, orig_w, orig_h)
            if rect2 and should_crop(orig_w, orig_h, rect2):
                rect, method = rect2, "gradient"
            else:
                rect = None

        if rect:
            crop_video(src, rect, dst)
            return f"{fname}: crop[{method}] {rect}"
        else:
            shutil.copy2(src, dst)
            return f"{fname}: no-crop copied"
    except Exception as e:
        return f"{fname}: FAILED – {e}"
# ╰───────────────────────────────────────────────────────────────────╯


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    videos = sorted(map(str, INPUT_DIR.glob("*.mp4")))
    if not videos:
        print("No .mp4 files found in", INPUT_DIR, file=sys.stderr)
        return

    print(f"Processing {len(videos)} videos "
          f"with {MAX_WORKERS} workers …", file=sys.stderr)

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for msg in pool.map(process_video, videos):
            print(msg)

    print("✅  All done.")


if __name__ == "__main__":
    mp.set_start_method("spawn")   # safer on macOS / Windows
    main()
