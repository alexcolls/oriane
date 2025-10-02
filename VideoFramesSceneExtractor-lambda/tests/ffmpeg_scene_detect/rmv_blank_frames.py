#!/usr/bin/env python3
import os
import cv2
import numpy as np
import shutil

# ─── Global parameters ────────────────────────────────────────────────────────
INPUT_ROOT  = 'output/no_cropped'          # root folder containing subfolders of frames
OUTPUT_ROOT = 'output/no_cropped_filtered'  # root folder to write filtered frames into

# ─── Functions ───────────────────────────────────────────────────────────────

def is_blank_frame(path: str) -> bool:
    """
    Returns True if the image at `path` is a uniform color (all pixels identical).
    """
    img = cv2.imread(path)
    if img is None:
        # unreadable images are treated as non-blank
        return False
    # Compare every pixel to the top-left pixel
    return np.all(img == img[0, 0])

def filter_frames():
    """
    Walk INPUT_ROOT and mirror its directory structure under OUTPUT_ROOT,
    copying only non-blank frames.
    """
    for dirpath, _, filenames in os.walk(INPUT_ROOT):
        rel_dir = os.path.relpath(dirpath, INPUT_ROOT)
        out_dir = os.path.join(OUTPUT_ROOT, rel_dir)
        os.makedirs(out_dir, exist_ok=True)

        for fname in sorted(filenames):
            if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue

            in_path  = os.path.join(dirpath, fname)
            if is_blank_frame(in_path):
                # skip uniform-color frames
                continue

            out_path = os.path.join(out_dir, fname)
            shutil.copy2(in_path, out_path)

# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    filter_frames()
    print(f"Done filtering blank frames from '{INPUT_ROOT}' → '{OUTPUT_ROOT}'.")
