#!/usr/bin/env python3
import os
import subprocess
import cv2
import numpy as np
from glob import glob

# ─── Config ──────────────────────────────────────────────────────────────────
INPUT_DIR    = 'cropped_videos2'
OUTPUT_DIR   = 'output/cropped_12'
MIN_FRAMES   = 4             # at least this many frames per video
THRESHOLD    = 0.12          # FFmpeg scene threshold
FFMPEG_PATH  = 'ffmpeg'      # or full path to ffmpeg binary

# ─── Helpers ─────────────────────────────────────────────────────────────────

def is_blank_frame(path: str) -> bool:
    """
    Returns True if the image at `path` is a uniform color.
    """
    img = cv2.imread(path)
    if img is None:
        return False
    # check if all pixels equal the first pixel
    return np.all(img == img[0, 0])

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

    # 2) Rename & filter blank frames, sequentially
    idx = 1
    for old_path, frame_no in entries:
        seconds = frame_no / fps
        if is_blank_frame(old_path):
            os.remove(old_path)
            continue
        new_name = f"{idx}_{seconds:.2f}.jpg"
        os.rename(old_path, os.path.join(out_dir, new_name))
        idx += 1

    # 3) Fallback if too few
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
            # skip if blank
            if np.all(frame == frame[0,0]):
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
