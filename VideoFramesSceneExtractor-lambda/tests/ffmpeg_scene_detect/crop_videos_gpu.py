#!/usr/bin/env python3
"""
Fast batch-cropper with optional GPU kernels
────────────────────────────────────────────
Dependencies
  • Python 3.9+        • numpy      • opencv-python-headless (built WITH CUDA)
  • FFmpeg ≥ 4.0 ( + NVDEC / QSV / V4L2 for hw decode if available )
"""

import os, sys, shutil, subprocess, multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from glob import glob
from pathlib import Path
from typing import Iterator, Tuple, Optional

import numpy as np
import cv2

# ─── CONFIG ───────────────────────────────────────────────────────────────────
INPUT_DIR      = Path("../videos")
OUTPUT_DIR     = Path("cropped_videos_gpu")
SAMPLE_FPS     = 1
TOLERANCE      = 5
EDGE_THRESH    = 10
MIN_CROP_RATIO = 0.10
DOWNSCALE      = 0.5
FFMPEG         = "ffmpeg"
FFPROBE        = "ffprobe"
MAX_WORKERS    = os.cpu_count() or 4
# ──────────────────────────────────────────────────────────────────────────────

# auto-detect CUDA
GPU_AVAILABLE = (hasattr(cv2, "cuda") and
                 cv2.cuda.getCudaEnabledDeviceCount() > 0)

# ╭───────────────────────── Utility helpers ─────────────────────────╮
def ffprobe_json(path: str) -> dict:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", path],
        stdout=subprocess.PIPE, text=True, check=True).stdout
    import json
    return json.loads(out)

def video_info(path: str) -> Tuple[int, int, float]:
    meta = ffprobe_json(path)
    vs = next(s for s in meta["streams"] if s["codec_type"] == "video")
    return int(vs["width"]), int(vs["height"]), float(meta["format"]["duration"])

def even(n: int) -> int:           # FFmpeg insists on even dims
    return n if n % 2 == 0 else n + 1
# ╰───────────────────────────────────────────────────────────────────╯

# ╭──────── Frame generator (single FFmpeg pipe, cpu host memory) ────╮
def iter_sampled_frames(path: str, w0: int, h0: int) -> Iterator[np.ndarray]:
    w_s, h_s = even(int(w0 * DOWNSCALE)), even(int(h0 * DOWNSCALE))
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error",
           "-hwaccel", "auto", "-i", path,
           "-vf", f"fps={SAMPLE_FPS},scale={w_s}:{h_s}",
           "-pix_fmt", "rgb24", "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            bufsize=w_s * h_s * 3)
    try:
        while True:
            raw = proc.stdout.read(w_s * h_s * 3)
            if len(raw) < w_s * h_s * 3:
                break
            yield np.frombuffer(raw, np.uint8).reshape(h_s, w_s, 3)
    finally:
        proc.stdout.close()
        proc.wait()
# ╰───────────────────────────────────────────────────────────────────╯

# ╭────────────── Median-border crop (unchanged – CPU) ───────────────╮
def detect_median_crop(path: str, w0: int, h0: int
                       ) -> Optional[Tuple[int,int,int,int]]:
    rects = []
    for small in iter_sampled_frames(path, w0, h0):
        border = np.vstack([small[0], small[-1], small[:,0], small[:,-1]])
        mb = np.median(border, axis=0)
        diff = np.abs(small.astype(np.int16) - mb.astype(np.int16)).sum(2)
        mask = diff > TOLERANCE
        coords = np.column_stack(np.where(mask))
        if coords.size:
            y0, x0 = coords.min(0)
            y1, x1 = coords.max(0)
            rects.append((x0, y0, x1-x0, y1-y0))
    if not rects:
        return None
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    w1 = max(r[0]+r[2] for r in rects)
    h1 = max(r[1]+r[3] for r in rects)
    s   = 1/DOWNSCALE
    return (int(x0*s), int(y0*s), int((w1-x0)*s), int((h1-y0)*s))
# ╰───────────────────────────────────────────────────────────────────╯

# ╭──── Gradient-heat crop – two versions, GPU or CPU fallback ───────╮
def _gradient_crop_cpu(path: str, w0: int, h0: int
                       ) -> Optional[Tuple[int,int,int,int]]:
    heat = None
    for small in iter_sampled_frames(path, w0, h0):
        g = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
        sx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
        sy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(sx, sy)
        heat = mag if heat is None else heat + mag
    if heat is None: return None
    norm = cv2.normalize(heat, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, mask = cv2.threshold(norm, EDGE_THRESH, 255, cv2.THRESH_BINARY)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    cnts,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts: return None
    x,y,w,h = cv2.boundingRect(max(cnts, key=cv2.contourArea))
    s = 1/DOWNSCALE
    return (int(x*s), int(y*s), int(w*s), int(h*s))

def _gradient_crop_gpu(path: str, w0: int, h0: int
                       ) -> Optional[Tuple[int,int,int,int]]:
    heat_gpu = None
    for small in iter_sampled_frames(path, w0, h0):
        gmat = cv2.cuda_GpuMat()
        gmat.upload(small)
        gray = cv2.cuda.cvtColor(gmat, cv2.COLOR_RGB2GRAY)
        sx = cv2.cuda.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sy = cv2.cuda.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.cuda.magnitude(sx, sy)
        if heat_gpu is None:
            heat_gpu = mag.clone()
        else:
            cv2.cuda.add(heat_gpu, mag, heat_gpu)
        # free scratch mats
        del gmat, gray, sx, sy, mag
    if heat_gpu is None:
        return None
    heat = heat_gpu.download()
    norm = cv2.normalize(heat, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, mask = cv2.threshold(norm, EDGE_THRESH, 255, cv2.THRESH_BINARY)
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (15,15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    cnts,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts: return None
    x,y,w,h = cv2.boundingRect(max(cnts, key=cv2.contourArea))
    s = 1/DOWNSCALE
    return (int(x*s), int(y*s), int(w*s), int(h*s))

def detect_gradient_crop(path: str, w0: int, h0: int
                         ) -> Optional[Tuple[int,int,int,int]]:
    if GPU_AVAILABLE:
        return _gradient_crop_gpu(path, w0, h0)
    return _gradient_crop_cpu(path, w0, h0)
# ╰───────────────────────────────────────────────────────────────────╯

def should_crop(w0: int, h0: int, rect) -> bool:
    x,y,w,h = rect
    return ((w0-w)/w0 >= MIN_CROP_RATIO) or ((h0-h)/h0 >= MIN_CROP_RATIO)

# ╭────────────────────── Crop or copy with FFmpeg ───────────────────╮
def crop_video(src: str, rect, dst: str):
    x,y,w,h = rect
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error",
           "-hwaccel", "auto", "-i", src,
           "-vf", f"crop={w}:{h}:{x}:{y}",
           "-c:v", "libx264", "-preset", "fast", "-crf", "23",
           "-c:a", "copy", str(dst)]
    subprocess.run(cmd, check=True)
# ╰───────────────────────────────────────────────────────────────────╯

# ╭──────────────────── Per-file worker function ─────────────────────╮
def process_video(src: str) -> str:
    fname = Path(src).name
    dst   = OUTPUT_DIR / fname
    try:
        w0, h0, _ = video_info(src)
        rect = detect_median_crop(src, w0, h0)
        method = "median"
        if not rect or not should_crop(w0,h0,rect):
            rect2 = detect_gradient_crop(src, w0, h0)
            if rect2 and should_crop(w0,h0,rect2):
                rect, method = rect2, "gradient-GPU" if GPU_AVAILABLE else "gradient"
            else:
                rect = None
        if rect:
            crop_video(src, rect, dst)
            return f"{fname}: {method} {rect}"
        shutil.copy2(src, dst)
        return f"{fname}: no-crop copied"
    except Exception as e:
        return f"{fname}: FAILED – {e}"
# ╰───────────────────────────────────────────────────────────────────╯

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    vids = sorted(map(str, INPUT_DIR.glob("*.mp4")))
    if not vids:
        print("No .mp4 files in", INPUT_DIR, file=sys.stderr); return
    print(f"GPU available: {GPU_AVAILABLE}  |  "
          f"Workers: {MAX_WORKERS}", file=sys.stderr)
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for msg in pool.map(process_video, vids):
            print(msg)
    print("✅  All done.")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
