#!/usr/bin/env python3

import os
import cv2
import numpy as np
import subprocess
from glob import glob

# ─── CONFIG ───────────────────────────────────────────────────────────────────
INPUT_DIR      = '../videos'          # folder of original MP4s
OUTPUT_DIR     = 'cropped_videos_py'     # where to write cropped MP4s
SAMPLE_FPS     = 1                    # sample one frame per second
TOLERANCE      = 5                    # median‐border diff threshold
EDGE_THRESH    = 10                   # Sobel edge‐mask threshold
MIN_CROP_RATIO = 0.10                 # require ≥10% trim to apply
DOWNSCALE      = 0.5                 # process at 25% resolution
FFMPEG         = 'ffmpeg'             # path to ffmpeg
FFPROBE        = 'ffprobe'            # path to ffprobe
# ───────────────────────────────────────────────────────────────────────────────

def get_duration(path: str) -> float:
    """Return video duration in seconds via ffprobe."""
    out = subprocess.run(
        [FFPROBE, '-v', 'error',
         '-show_entries', 'format=duration',
         '-of', 'default=nw=1:nk=1', path],
        stdout=subprocess.PIPE, text=True, check=True
    ).stdout.strip()
    return float(out)

def detect_median_crop(path: str):
    """
    Median‐border crop: sample 1fps, downscale, union all content bboxes.
    Returns (x, y, w, h) or None.
    """
    dur = get_duration(path)
    cap = cv2.VideoCapture(path)
    rects = []
    for t in np.arange(0, dur, 1.0 / SAMPLE_FPS):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ret, frame = cap.read()
        if not ret:
            continue
        small = cv2.resize(frame, (0,0), fx=DOWNSCALE, fy=DOWNSCALE)
        # sample border pixels
        edges = np.vstack([
            small[0], small[-1],
            small[:,0], small[:,-1]
        ])
        median_border = np.median(edges, axis=0)
        # mask content
        diff = np.abs(small.astype(int) - median_border.astype(int)).sum(axis=2)
        mask = diff > TOLERANCE
        coords = np.column_stack(np.where(mask))
        if coords.size:
            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0)
            # scale coords back up
            rects.append((
                int(x0 / DOWNSCALE),
                int(y0 / DOWNSCALE),
                int((x1 - x0) / DOWNSCALE),
                int((y1 - y0) / DOWNSCALE),
            ))
    cap.release()
    if not rects:
        return None
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    w1 = max(r[0] + r[2] for r in rects)
    h1 = max(r[1] + r[3] for r in rects)
    return (x0, y0, w1 - x0, h1 - y0)

def detect_gradient_crop(path: str):
    """
    Edge‐based crop: sample 1fps, downscale, accumulate Sobel edges,
    threshold + close → largest contour bbox.
    """
    dur = get_duration(path)
    cap = cv2.VideoCapture(path)
    heatmap = None
    for t in np.arange(0, dur, 1.0 / SAMPLE_FPS):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ret, frame = cap.read()
        if not ret:
            continue
        small = cv2.resize(frame, (0,0), fx=DOWNSCALE, fy=DOWNSCALE)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        sx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        edges = cv2.magnitude(sx, sy)
        heatmap = edges if heatmap is None else heatmap + edges
    cap.release()
    if heatmap is None:
        return None
    norm = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, mask = cv2.threshold(norm, EDGE_THRESH, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15,15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    return (int(x / DOWNSCALE), int(y / DOWNSCALE),
            int(w / DOWNSCALE), int(h / DOWNSCALE))

def should_crop(orig_w: int, orig_h: int, rect) -> bool:
    """Only crop if trim ≥ MIN_CROP_RATIO of width or height."""
    x, y, w, h = rect
    return ((orig_w - w) / orig_w >= MIN_CROP_RATIO or
            (orig_h - h) / orig_h >= MIN_CROP_RATIO)

def crop_video(src: str, rect, dst: str):
    """Apply the crop via FFmpeg."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    x, y, w, h = rect
    subprocess.run([
        FFMPEG, '-hide_banner', '-loglevel', 'error',
        '-i', src,
        '-vf', f'crop={w}:{h}:{x}:{y}',
        '-c:a', 'copy',
        dst
    ], check=True)

def batch_crop():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for src in sorted(glob(os.path.join(INPUT_DIR, '*.mp4'))):
        fname = os.path.basename(src)
        dst   = os.path.join(OUTPUT_DIR, fname)
        print(f"→ {fname}", end=' ')

        # probe original size
        cap = cv2.VideoCapture(src)
        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        # try median‐border first
        rect = detect_median_crop(src)
        method = 'median'

        # if too small or None, try gradient
        if not rect or not should_crop(orig_w, orig_h, rect):
            rect2 = detect_gradient_crop(src)
            if rect2 and should_crop(orig_w, orig_h, rect2):
                rect, method = rect2, 'gradient'
            else:
                rect = None

        if not rect:
            print("no crop → copy")
            subprocess.run(['cp', src, dst], check=True)
        else:
            print(f"crop[{method}]={rect}", end=' ')
            try:
                crop_video(src, rect, dst)
                print("done")
            except Exception as e:
                print(f"FAILED ({e})")

    print("✅ All videos processed.")

if __name__ == '__main__':
    batch_crop()
