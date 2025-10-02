#!/usr/bin/env python3
import os
import subprocess
import cv2
import numpy as np
from glob import glob

# ─── Config ──────────────────────────────────────────────────────────────────
INPUT_DIR       = 'cropped_videos2'
OUTPUT_DIR      = 'output/cropped_12_advanced_py'
MIN_FRAMES      = 4             # at least this many frames per video
THRESHOLD       = 0.12          # FFmpeg scene threshold
FFMPEG_PATH     = 'ffmpeg'      # or full path to ffmpeg binary
IMAGE_CROP_TOL  = 10            # pixel‐difference threshold for cropping margins
# ───────────────────────────────────────────────────────────────────────────────

def detect_image_crop(img: np.ndarray, tol: int = IMAGE_CROP_TOL):
    """
    Crop away any uniform‐color margins (even partial): examines each border
    row/column and strips those where all pixels are within tol of the border's
    median color.
    Returns (x, y, w, h) or None if no cropping needed.
    """
    h, w = img.shape[:2]

    def is_blank_line(line: np.ndarray) -> bool:
        # line: N x 3 array of BGR pixels
        median_col = np.median(line, axis=0)
        diffs = np.abs(line.astype(int) - median_col.astype(int)).sum(axis=1)
        return np.all(diffs <= tol)

    # left margin
    x0 = 0
    for x in range(w):
        if is_blank_line(img[:, x, :]):
            x0 += 1
        else:
            break

    # right margin
    x1 = w
    for x in range(w - 1, -1, -1):
        if is_blank_line(img[:, x, :]):
            x1 -= 1
        else:
            break

    # top margin
    y0 = 0
    for y in range(h):
        if is_blank_line(img[y, :, :]):
            y0 += 1
        else:
            break

    # bottom margin
    y1 = h
    for y in range(h - 1, -1, -1):
        if is_blank_line(img[y, :, :]):
            y1 -= 1
        else:
            break

    # ensure valid crop
    if x0 >= x1 or y0 >= y1:
        return None

    return (x0, y0, x1 - x0, y1 - y0)

def ffmpeg_extract_with_pts(video_path: str, out_dir: str, threshold: float):
    """
    Dump one JPG per scene cut into out_dir, file named by frame number.
    Returns list of (file_path, frame_no).
    """
    os.makedirs(out_dir, exist_ok=True)
    pattern = os.path.join(out_dir, '%d.jpg')
    cmd = [
        FFMPEG_PATH,
        '-hide_banner', '-loglevel', 'error',
        '-i', video_path,
        '-vf', f"select='gt(scene,{threshold})'",
        '-vsync', 'vfr',
        '-frame_pts', '1',
        '-q:v', '2',
        pattern
    ]
    subprocess.run(cmd, check=True)

    entries = []
    for p in glob(os.path.join(out_dir, '*.jpg')):
        frame_no = int(os.path.splitext(os.path.basename(p))[0])
        entries.append((p, frame_no))
    entries.sort(key=lambda x: x[1])
    return entries

def process_video(path: str):
    base = os.path.splitext(os.path.basename(path))[0]
    out_dir = os.path.join(OUTPUT_DIR, base)
    print(f"Processing {path} → {out_dir}...")

    # probe FPS once
    cap_probe = cv2.VideoCapture(path)
    fps = cap_probe.get(cv2.CAP_PROP_FPS) or 25.0
    cap_probe.release()

    # 1) FFmpeg pass
    entries = ffmpeg_extract_with_pts(path, out_dir, THRESHOLD)
    print(f"  FFmpeg produced {len(entries)} raw frames")

    # 2) Rename, crop image margins, filter fully blank frames
    idx = 1
    for old_path, frame_no in entries:
        img = cv2.imread(old_path)
        if img is None:
            os.remove(old_path)
            continue

        # crop margins dynamically
        rect = detect_image_crop(img)
        if rect:
            x, y, w, h = rect
            img = img[y:y+h, x:x+w]

        # drop if fully blank after crop
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if np.all(gray == gray[0,0]):
            os.remove(old_path)
            continue

        # save with sequential index and timestamp
        seconds = frame_no / fps
        new_name = f"{idx}_{seconds:.2f}.jpg"
        cv2.imwrite(os.path.join(out_dir, new_name), img)
        os.remove(old_path)
        idx += 1

    # 3) Fallback if too few frames
    if idx <= MIN_FRAMES:
        print(f"  << fallback to OpenCV to reach {MIN_FRAMES} frames >>")
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, total // (MIN_FRAMES + 1))
        for frame_no in (i * step for i in range(1, MIN_FRAMES + 1)):
            if idx > MIN_FRAMES:
                break
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
            ret, frame = cap.read()
            if not ret:
                continue

            # crop margins
            rect = detect_image_crop(frame)
            if rect:
                x, y, w, h = rect
                frame = frame[y:y+h, x:x+w]

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if np.all(gray == gray[0,0]):
                continue

            seconds = frame_no / fps
            out_name = f"{idx}_{seconds:.2f}.jpg"
            cv2.imwrite(os.path.join(out_dir, out_name), frame)
            idx += 1
        cap.release()
        print(f"  Total after fallback: {idx-1} frames")
    else:
        print(f"  Done with {idx-1} frames (≥{MIN_FRAMES})")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.lower().endswith('.mp4'):
            continue
        process_video(os.path.join(INPUT_DIR, fname))
    print("All done.")

if __name__ == '__main__':
    main()
