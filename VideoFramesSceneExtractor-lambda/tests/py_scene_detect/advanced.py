#!/usr/bin/env python3

"""
Script to extract the most significant frames (one per detected scene) from all MP4 videos in the "videos" folder.
Uses PySceneDetect (v0.6+) for scene detection via the `detect()` helper and OpenCV for frame extraction.
Selects the sharpest frame in each scene via variance of the Laplacian.
If no scenes are detected, falls back to extracting a single mid‐point frame.
Outputs images for each video under "<output_dir>/<video_name>/", named 0.jpg, 1.jpg, ...
Supports three detectors (content, threshold, histogram), parallel processing, progress bars, and configurable parameters via CLI.
"""

import os
import argparse
import logging
import cv2
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from scenedetect import detect
from scenedetect.detectors import ContentDetector, ThresholdDetector, HistogramDetector

def parse_args():
    p = argparse.ArgumentParser(
        description="Extract one key frame per scene from all MP4s in ./videos into a specified output folder"
    )
    p.add_argument(
        "--detector",
        choices=["content", "threshold", "histogram"],
        default="content",
        help="Which PySceneDetect detector to use"
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=30.0,
        help="Sensitivity threshold (lower = more scenes)"
    )
    p.add_argument(
        "--min-scene-len",
        type=int,
        default=1,
        help="Minimum number of frames per scene (default 1 to catch very short cuts)"
    )
    p.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count(),
        help="Number of parallel worker processes to use"
    )
    p.add_argument(
        "--output-dir",
        dest="output_dir",
        default="output",
        help="Base folder where per-video subfolders will be created"
    )
    return p.parse_args()

def pick_sharpest_frame(cap: cv2.VideoCapture, start_frame: int, end_frame: int) -> int:
    """
    Scan frames from start_frame to end_frame (inclusive),
    compute variance of the Laplacian (sharpness) on each,
    and return the frame index with the highest variance.
    """
    best_var = -1.0
    best_idx = start_frame
    for fno in range(start_frame, end_frame + 1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fno)
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        if sharpness > best_var:
            best_var, best_idx = sharpness, fno
    return best_idx

def extract_key_frames(video_path: str, args):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    out_dir = os.path.join('output/advanced', args.output_dir, video_name)
    os.makedirs(out_dir, exist_ok=True)
    # Choose detector instance
    if args.detector == "content":
        detector = ContentDetector(threshold=args.threshold, min_scene_len=args.min_scene_len)
    elif args.detector == "threshold":
        detector = ThresholdDetector(threshold=args.threshold, min_scene_len=args.min_scene_len)
    else:  # histogram
        detector = HistogramDetector(threshold=args.threshold, min_scene_len=args.min_scene_len)
    # Perform scene detection (new API; no VideoManager)
    try:
        scenes = detect(video_path, detector, show_progress=False)
    except Exception as e:
        logging.error("Scene detection failed for %s: %s", video_name, e)
        scenes = []
    # Open with OpenCV for frame extraction
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error("Failed to open video %s", video_name)
        return
    # Fallback: if no scenes, extract a single mid‐point frame
    if not scenes:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total > 0:
            mid = total // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
            ret, frame = cap.read()
            if ret:
                out_path = os.path.join(out_dir, "0.jpg")
                cv2.imwrite(out_path, frame)
                logging.info("Fallback: extracted mid‐point frame for %s", video_name)
        else:
            logging.warning("Video %s has no frames, skipping.", video_name)
        cap.release()
        return
    # For each detected scene, pick and save the sharpest frame
    for idx, (start_tc, end_tc) in enumerate(scenes):
        start_f = start_tc.get_frames()
        end_f   = end_tc.get_frames()
        best_frame = pick_sharpest_frame(cap, start_f, end_f)
        cap.set(cv2.CAP_PROP_POS_FRAMES, best_frame)
        ret, frame = cap.read()
        if not ret:
            logging.warning("Could not read frame %d from %s", best_frame, video_name)
            continue
        cv2.imwrite(os.path.join(out_dir, f"{idx}.jpg"), frame)
    cap.release()
    logging.info("Done %s: %d frames extracted", video_name, len(scenes))

def main():
    args = parse_args()
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO
    )
    input_dir = '../videos'
    os.makedirs(args.output_dir, exist_ok=True)
    video_files = [
        os.path.join(input_dir, fn)
        for fn in os.listdir(input_dir)
        if fn.lower().endswith(".mp4")
    ]
    if not video_files:
        logging.warning("No .mp4 files found in %s", input_dir)
        return
    logging.info(
        "Processing %d videos with %d workers (detector=%s, threshold=%.2f, min_scene_len=%d)...",
        len(video_files), args.workers, args.detector,
        args.threshold, args.min_scene_len
    )
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(extract_key_frames, path, args) for path in video_files]
        for _ in tqdm(futures, desc="Extracting key frames", unit="video"):
            _.result()
    logging.info("All done!")


if __name__ == "__main__":
    main()
