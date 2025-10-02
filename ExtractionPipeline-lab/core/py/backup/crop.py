#!/usr/bin/env python3
"""
crop.py  –  smart border-cropper with full-GPU encode

• Detection: median border + Sobel heat-map (NumPy / OpenCV on down-scaled frames)
• Sampling  : FFmpeg with -hwaccel auto for frame generation
• Cropping  : CUVID -crop (GPU only), or crop_cuda filter, ensuring no unwanted scaling.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator, Optional, Tuple

import cv2
import numpy as np

# ─── Configuration ──────────────────────────────────────────────────
INPUT_DIR = Path("../videos")  # Adjust if your videos are elsewhere
OUTPUT_DIR = Path("../tmp/cropped")  # Adjust output directory
SAMPLE_FPS = 0.1  # 0.1 = 1 frame every 10 seconds
TOLERANCE = 5
EDGE_THRESH = 10
MIN_CROP_RATIO = (
    0.10  # Minimum ratio of (original_dim - new_dim) / original_dim to be considered a crop
)
DOWNSCALE = 0.5  # Factor to downscale frames for detection (0.5 means half size)
MAX_WORKERS = 3  # max(1, os.cpu_count() - 1)
FFMPEG_PROBES = 3  # how many different moments to scan
PROBE_CLIP_SECS = 2  # seconds analysed in each probe
SAFE_MARGIN_PX = 4  # pad the final rect on every side
FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"
# --------------------------------------------------------------------

DECODER = {  # Map common video codecs to their NVIDIA CUVID decoder counterparts
    "h264": "h264_cuvid",
    "hevc": "hevc_cuvid",
    "vp9": "vp9_cuvid",
    "av1": "av1_cuvid",
    "mpeg2video": "mpeg2_cuvid",
}


# ─── FFmpeg helpers ─────────────────────────────────────────────────
def ffprobe_val(src: str, key: str) -> str:
    """Gets a specific metadata value (e.g., 'width,height', 'codec_name') from a video stream using ffprobe."""
    # Use -v quiet to suppress all ffprobe console output except the value itself
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


def ff_has_filter(name: str) -> bool:
    """Checks if a specific ffmpeg filter (e.g., 'crop_cuda') is available in the current ffmpeg build."""
    try:
        # -hide_banner keeps the output clean, stderr=DEVNULL suppresses warnings if ffmpeg itself has issues
        result = subprocess.check_output(
            [FFMPEG, "-hide_banner", "-filters"], text=True, stderr=subprocess.DEVNULL
        )
        return name in result
    except subprocess.CalledProcessError:
        # This warning is useful if the ffmpeg -filters command fails for some reason
        print(
            f"Warning: Could not execute '{FFMPEG} -filters' to check for filter '{name}'. Assuming not available.",
            file=sys.stderr,
        )
        return False
    except FileNotFoundError:
        # This error occurs if FFMPEG command itself is not found
        print(
            f"Error: FFMPEG command '{FFMPEG}' not found when checking for filters.",
            file=sys.stderr,
        )
        return False  # Should ideally be handled by main's initial check


HAS_CROP_CUDA = ff_has_filter("crop_cuda")


# ─── Utility ────────────────────────────────────────────────────────
def even(x: int) -> int:
    """Ensures an integer is even, typically by adding 1 if odd. Important for video dimensions for some encoders."""
    return x if x % 2 == 0 else x + 1


# ─── Frame generator ────────────────────────────────────────────────
def iter_sampled_frames(src: str, ow: int, oh: int) -> Iterator[np.ndarray]:
    """
    Generates downscaled frames from a video file using FFmpeg.
    Uses -hwaccel auto to attempt GPU decoding for this sampling step.
    """
    sw = even(int(ow * DOWNSCALE))  # Scaled width
    sh = even(int(oh * DOWNSCALE))  # Scaled height
    frame_bytes = sw * sh * 3  # Bytes per frame (RGB24 format)

    vf_string = f"fps={SAMPLE_FPS},scale={sw}:{sh}"  # FFmpeg video filter string
    cmd = [
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",  # Minimize FFmpeg's console output
        "-hwaccel",
        "auto",  # Attempt hardware acceleration for decoding
        "-i",
        str(src),  # Input file
        "-vf",
        vf_string,  # Apply FPS sampling and scaling
        "-pix_fmt",
        "rgb24",  # Output pixel format for OpenCV compatibility
        "-f",
        "rawvideo",  # Output format
        "-",  # Output to stdout
    ]

    # Start FFmpeg process. bufsize can be tuned; larger might help with pipe performance.
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=frame_bytes * 10
    )
    try:
        while True:
            buf = proc.stdout.read(frame_bytes)  # Read one frame's worth of data
            if len(buf) < frame_bytes:
                # If less data than a full frame is read, it's likely the end of the stream or an error.
                stderr_output = proc.stderr.read().decode(errors="ignore").strip()
                if stderr_output:
                    # Log any error messages from FFmpeg during this frame generation.
                    print(
                        f"WARNING: iter_sampled_frames FFMPEG STDERR for {Path(src).name}:\n{stderr_output}",
                        file=sys.stderr,
                    )
                break  # Exit the loop
            # Convert the raw byte buffer to a NumPy array and yield it.
            yield np.frombuffer(buf, np.uint8).reshape(sh, sw, 3)
    finally:
        # Ensure FFmpeg process resources are cleaned up.
        if proc.stdout:
            proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()
        proc.wait()


# ─── Detection logic ────────────────────────────────────────────────
def detect_crop_ffmpeg_simple(src: str, probe_secs=3):
    cmd = [
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "info",
        "-hwaccel",
        "cuda",
        "-i",
        src,
        "-t",
        str(probe_secs),
        "-vf",
        "cropdetect=24:16:0",
        "-f",
        "null",
        "-",
    ]
    out = subprocess.run(cmd, capture_output=True, text=True).stderr
    crops = re.findall(r"crop=([0-9:]+)", out)
    if crops:
        w, h, x, y = map(int, crops[-1].split(":"))
        return x, y, w, h
    return None


def detect_crop_ffmpeg(src: str, probes=FFMPEG_PROBES, probe_secs=PROBE_CLIP_SECS):
    """
    Run cropdetect `probes` times at evenly-spaced timestamps and return
    the UNION (max-extent) rectangle so no content is ever lost.
    """
    # 1) Get full length (in seconds) once
    dur = float(ffprobe_val(src, "duration") or 0)
    if dur == 0:
        return None  # ffprobe failed

    # 2) Collect rectangles from multiple short segments
    rects = []
    for k in range(probes):
        ts = dur * (k + 1) / (probes + 1)  # ~ middle of each segment
        cmd = [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{ts:.3f}",
            "-t",
            str(probe_secs),
            "-hwaccel",
            "cuda",
            "-i",
            src,
            "-vf",
            "cropdetect=24:16:0",
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

    # 3) Build the *union* rectangle and add a small safety margin
    x0 = min(r[0] for r in rects) - SAFE_MARGIN_PX
    y0 = min(r[1] for r in rects) - SAFE_MARGIN_PX
    x1w = max(r[0] + r[2] for r in rects) + SAFE_MARGIN_PX
    y1h = max(r[1] + r[3] for r in rects) + SAFE_MARGIN_PX

    # clamp to positive values – the main loop already clamps against ow/oh
    return max(0, x0), max(0, y0), x1w - x0, y1h - y0


def detect_median(src: str, ow: int, oh: int) -> Optional[Tuple[int, int, int, int]]:
    """
    Detects content area by comparing frame pixels to the median color of the frame's outer borders.
    """
    rects = []  # List to store detected rectangles from each sampled frame
    frame_iter_count = 0  # Count frames actually processed by the iterator
    for small in iter_sampled_frames(str(src), ow, oh):
        frame_iter_count += 1
        try:
            # Collect border pixels: top row, bottom row, left column, right column.
            # Each part should be a 2D array of (N_pixels, 3_channels).
            # small[0, :, :] is the top row.
            # small[-1, :, :] is the bottom row.
            # small[:, 0, :] is the left column.
            # small[:, -1, :] is the right column.
            edges = np.vstack(
                [
                    small[0, :, :],  # Top row
                    small[-1, :, :],  # Bottom row
                    small[:, 0, :],  # Left column
                    small[:, -1, :],  # Right column
                ]
            )
        except ValueError as e:
            # This can occur if a frame is empty, malformed, or dimensions are unexpected.
            print(
                f"ERROR: [{Path(src).name}] np.vstack failed in detect_median. Small frame shape: {small.shape}. Error: {e}",
                file=sys.stderr,
            )
            continue  # Skip this problematic frame

        median_border = np.median(edges, axis=0)  # Calculate median color of all border pixels
        # Calculate absolute difference between each pixel and the median border color, sum across channels.
        diff = np.abs(small.astype(np.int16) - median_border.astype(np.int16)).sum(axis=2)
        mask = (
            diff > TOLERANCE
        )  # Create a mask where difference exceeds tolerance (these are content pixels)
        coords = np.column_stack(np.where(mask))  # Get coordinates of content pixels

        if coords.size:
            # If content pixels are found, determine their bounding box.
            y0_small, x0_small = coords.min(axis=0)
            y1_small, x1_small = coords.max(axis=0)
            # Rectangle is (x_start, y_start, width, height)
            detected_rect_small = (
                x0_small,
                y0_small,
                x1_small - x0_small + 1,
                y1_small - y0_small + 1,
            )
            rects.append(detected_rect_small)

    if frame_iter_count == 0:
        # This indicates an issue with iter_sampled_frames for this video.
        print(
            f"WARNING: [{Path(src).name}] iter_sampled_frames yielded no frames for detect_median.",
            file=sys.stderr,
        )

    if not rects:
        return None  # No valid rectangles found across all sampled frames.

    # Combine all detected rectangles to find the overall content bounding box.
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    # Max of (x_start + width) to get the rightmost extent.
    x1_plus_w = max(r[0] + r[2] for r in rects)
    # Max of (y_start + height) to get the bottommost extent.
    y1_plus_h = max(r[1] + r[3] for r in rects)

    s = 1 / DOWNSCALE  # Scaling factor to convert back to original dimensions.
    # Final rectangle (x, y, width, height) in original video dimensions.
    final_rect = (int(x0 * s), int(y0 * s), int((x1_plus_w - x0) * s), int((y1_plus_h - y0) * s))
    return final_rect


def detect_gradient(src: str, ow: int, oh: int) -> Optional[Tuple[int, int, int, int]]:
    """
    Detects content area using Sobel gradient magnitude to find edges, then finds the largest contour.
    """
    heat = None  # Accumulator for gradient magnitudes (heat map)
    frame_iter_count = 0
    for small in iter_sampled_frames(str(src), ow, oh):
        frame_iter_count += 1
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)  # Convert to grayscale
        # Calculate Sobel gradients in x and y directions
        sx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(sx, sy)  # Calculate gradient magnitude
        heat = mag if heat is None else heat + mag  # Accumulate magnitudes

    if frame_iter_count == 0:
        print(
            f"WARNING: [{Path(src).name}] iter_sampled_frames yielded no frames for detect_gradient.",
            file=sys.stderr,
        )

    if heat is None:
        return None  # No frames processed or all frames were empty.

    # Normalize heat map to 0-255 range and convert to 8-bit unsigned integer.
    norm = cv2.normalize(heat, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    # Threshold the heat map to create a binary mask of significant edges.
    _, mask = cv2.threshold(norm, EDGE_THRESH, 255, cv2.THRESH_BINARY)
    # Apply morphological closing to fill gaps and connect nearby edges.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    # Find contours in the binary mask.
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not cnts:
        return None  # No contours found.

    # Get the bounding rectangle of the largest contour found.
    x_small, y_small, w_small, h_small = cv2.boundingRect(max(cnts, key=cv2.contourArea))
    s = 1 / DOWNSCALE  # Scaling factor
    # Final rectangle in original video dimensions.
    final_rect = int(x_small * s), int(y_small * s), int(w_small * s), int(h_small * s)
    return final_rect


def good(rect, ow, oh) -> bool:
    """
    Checks if a detected crop rectangle is 'good' based on configuration.
    A crop is 'good' if it's not None, has positive dimensions,
    removes a significant portion (MIN_CROP_RATIO) of width OR height,
    and doesn't crop away too much (e.g., leaves at least 5% of original dimension).
    """
    if not rect:
        return False
    if not (isinstance(rect, tuple) and len(rect) == 4):
        return False  # Basic type check
    x, y, w, h = rect

    if w <= 0 or h <= 0:
        return False  # Crop dimensions must be positive.

    # A crop is significant if the new width/height is less than original * (1.0 - MIN_CROP_RATIO)
    is_significant_width_crop = w < ow * (1.0 - MIN_CROP_RATIO)
    is_significant_height_crop = h < oh * (1.0 - MIN_CROP_RATIO)
    is_significant_crop = is_significant_width_crop or is_significant_height_crop

    # A crop is sensible if it doesn't remove almost everything.
    # (e.g., cropped width/height should be at least 5% of original).
    is_sensible_crop = w > ow * 0.05 and h > oh * 0.05

    return is_significant_crop and is_sensible_crop


# ─── Crop + encode (GPU-only for crop operation) ───────────────────
def crop_gpu(src: str, dst: str, rect: Tuple[int, int, int, int], ow: int, oh: int):
    """Crops and re-encodes a video using GPU acceleration (NVIDIA CUVID/NVENC)."""
    x, y, w, h = rect
    w_even, h_even = even(w), even(h)  # Ensure even dimensions for encoder compatibility.

    if w_even <= 0 or h_even <= 0:
        # This check is important if rect adjustments lead to invalid dimensions.
        raise ValueError(
            f"Calculated crop dimensions are invalid after making even: w={w_even}, h={h_even}"
        )

    codec = ffprobe_val(str(src), "codec_name")  # Get input video codec.
    cuvid_decoder = DECODER.get(codec)  # Get specific NVIDIA CUVID decoder if available.

    ffmpeg_base_cmd = [FFMPEG, "-hide_banner", "-loglevel", "error"]
    hw_init_opts = ["-hwaccel_device", "0"]  # Assume GPU device 0.

    input_decoder_opts = []  # Options for input decoding.
    input_file_opts = ["-i", str(src)]  # Input file.
    video_filter_opts = []  # Video filter options.

    # Encoder options: NVIDIA NVENC for H.264.
    # -preset p5 (medium speed, good quality), -tune hq (high quality tune)
    # -cq 23 (constant quality). Copy audio. Faststart for web playback.
    encoder_opts = [
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p5",
        "-tune",
        "hq",
        "-cq",
        "23",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        "-y",
        str(dst),  # Overwrite output file if it exists.
    ]

    if HAS_CROP_CUDA:
        # Preferred method: Use crop_cuda filter for GPU-side cropping.
        if cuvid_decoder:
            # If specific CUVID decoder, use it and specify CUDA output format.
            input_decoder_opts.extend(
                ["-c:v", cuvid_decoder] + hw_init_opts + ["-hwaccel_output_format", "cuda"]
            )
        else:
            # Generic CUDA hardware acceleration if no specific CUVID decoder.
            input_decoder_opts.extend(
                ["-hwaccel", "cuda"] + hw_init_opts + ["-hwaccel_output_format", "cuda"]
            )
        # Apply crop_cuda filter, set SAR (Sample Aspect Ratio) to 1:1, and ensure NV12 pixel format for NVENC.
        video_filter_opts.extend(
            ["-vf", f"crop_cuda=w={w_even}:h={h_even}:x={x}:y={y},setsar=1:1,format=nv12"]
        )

    elif cuvid_decoder:
        # Fallback: Use CUVID decoder's built-in -crop option.
        # This option takes pixels to remove from top:bottom:left:right.
        pixels_to_crop_top = y
        pixels_to_crop_bottom = oh - (y + h_even)  # Original height - (crop_y + crop_height_even)
        pixels_to_crop_left = x
        pixels_to_crop_right = ow - (x + w_even)  # Original width - (crop_x + crop_width_even)

        # Ensure crop values are not negative (can happen with slight miscalculations or edge cases).
        pixels_to_crop_top = max(0, pixels_to_crop_top)
        pixels_to_crop_bottom = max(0, pixels_to_crop_bottom)
        pixels_to_crop_left = max(0, pixels_to_crop_left)
        pixels_to_crop_right = max(0, pixels_to_crop_right)

        input_decoder_opts.extend(["-c:v", cuvid_decoder] + hw_init_opts)
        input_decoder_opts.extend(
            [
                "-crop",
                f"{pixels_to_crop_top}x{pixels_to_crop_bottom}x{pixels_to_crop_left}x{pixels_to_crop_right}",
            ]
        )
        # Set SAR and ensure NV12 format for NVENC compatibility. format=nv12 might be redundant if cuvid outputs it, but safe.
        video_filter_opts.extend(["-vf", "setsar=1:1,format=nv12"])

    else:
        # If neither crop_cuda nor a CUVID decoder is available, GPU crop is not possible with this script's logic.
        error_message = (
            f"Cannot perform GPU-only crop for {Path(src).name} (codec: {codec}):\n"
            f"  - 'crop_cuda' filter is not available (HAS_CROP_CUDA: {HAS_CROP_CUDA}).\n"
            f"  - No specific CUVID decoder found for input codec '{codec}'.\n"
            f"  This script requires an NVIDIA GPU and an FFmpeg build with NVIDIA support."
        )
        raise RuntimeError(error_message)

    final_cmd = (
        ffmpeg_base_cmd + input_decoder_opts + input_file_opts + video_filter_opts + encoder_opts
    )

    print(f"INFO: [{Path(src).name}] Executing FFmpeg crop command: {' '.join(final_cmd)}")
    try:
        process = subprocess.run(final_cmd, check=True, capture_output=True, text=True)
        if process.stderr.strip():
            # Log any stderr output from FFmpeg, even on success (can contain warnings).
            print(
                f"INFO: [{Path(src).name}] FFmpeg stderr (crop_gpu success):\n{process.stderr.strip()}",
                file=sys.stderr,
            )
    except subprocess.CalledProcessError as e:
        # Log detailed error information if FFmpeg command fails.
        print(f"ERROR: [{Path(src).name}] FFmpeg command failed (crop_gpu):", file=sys.stderr)
        print(f"  Command: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"  Return code: {e.returncode}", file=sys.stderr)
        print(f"  Stdout: {e.stdout.strip() if e.stdout else 'N/A'}", file=sys.stderr)
        print(f"  Stderr: {e.stderr.strip() if e.stderr else 'N/A'}", file=sys.stderr)
        raise  # Re-raise the exception to be caught by the main handler.


# ─── Per-video worker ────────────────────────────────────────────────
def handle(src_path: Path) -> str:
    """Processes a single video file: detects crop, crops if needed, or copies."""
    video_start_time = time.time()
    dst_path = OUTPUT_DIR / src_path.name
    src_str = str(src_path)
    dst_str = str(dst_path)
    status_message = ""  # Status of the processing for this video.
    detection_time = 0.0  # Time spent in detection phase.

    print(f"INFO: Processing {src_path.name}...")
    try:
        wh_str = ffprobe_val(src_str, "width,height")  # Get original video dimensions.
        ow, oh = map(int, wh_str.split(","))

        if ow <= 0 or oh <= 0:  # Basic validation of dimensions.
            status_message = f"FAILED - Invalid dimensions from ffprobe ({ow}x{oh})"
            raise ValueError(status_message)

        # --- Detection Phase ---
        detection_start_time = time.time()
        rect = detect_crop_ffmpeg(src_str)
        mode = "ffmpeg"
        is_good_median = good(rect, ow, oh)

        if not is_good_median:
            # If median detection is not good, try gradient detection.
            alt_rect = detect_gradient(src_str, ow, oh)
            is_good_gradient = good(alt_rect, ow, oh)
            if is_good_gradient:
                rect, mode = alt_rect, "gradient"  # Use gradient result.
            else:
                rect = None  # Neither method found a good crop.
        detection_time = time.time() - detection_start_time
        # --- End Detection Phase ---

        if rect:
            # A potentially good crop rectangle was found.
            crop_x, crop_y, crop_w, crop_h = rect

            # Validate and clamp crop rectangle to be within original video dimensions.
            # Ensure x, y are within bounds [0, original_dim - 1].
            crop_x = max(0, min(crop_x, ow - 1))
            crop_y = max(0, min(crop_y, oh - 1))
            # Ensure width, height are positive and don't extend beyond original boundaries from new x,y.
            crop_w = max(1, min(crop_w, ow - crop_x))
            crop_h = max(1, min(crop_h, oh - crop_y))

            final_valid_rect = (crop_x, crop_y, crop_w, crop_h)

            # Final check: is the *adjusted* rectangle still good and valid (w/h > 0)?
            if good(final_valid_rect, ow, oh) and (
                final_valid_rect[2] > 0 and final_valid_rect[3] > 0
            ):
                crop_gpu(src_str, dst_str, final_valid_rect, ow, oh)
                status_message = f"crop[{mode}] {final_valid_rect} -> {dst_path.name}"
            else:
                # If adjusted rect is no longer good or became invalid.
                shutil.copy2(src_path, dst_path)  # Copy original file.
                status_message = "no-crop (adjusted rect not good/invalid)"
        else:
            # No good crop was detected by either method.
            shutil.copy2(src_path, dst_path)  # Copy original file.
            status_message = "no-crop (copied original, no good detection)"

        video_time_taken = time.time() - video_start_time
        final_log = (
            f"INFO: {src_path.name} {status_message}. "
            f"Detection: {detection_time:.2f}s. Total: {video_time_taken:.2f}s"
        )
        print(final_log)
        return status_message  # Return status for summary.

    except Exception as e:
        video_time_taken = time.time() - video_start_time
        failure_reason = (
            status_message
            if status_message and "FAILED" in status_message
            else f"{type(e).__name__}: {e}"
        )

        # Uncomment for full traceback during debugging:
        # import traceback
        # traceback.print_exc(file=sys.stderr)

        error_log = f"ERROR: {src_path.name} FAILED - {failure_reason}. Detection: {detection_time:.2f}s. Total: {video_time_taken:.2f}s"
        print(error_log, file=sys.stderr)
        return f"FAILED - {failure_reason}"  # Return failure status for summary.


# ─── Main runner ─────────────────────────────────────────────────────
def main():
    if not FFMPEG or not shutil.which(FFMPEG):
        sys.exit(
            f"Error: ffmpeg command ('{FFMPEG}') not found or not executable. Please install ffmpeg and ensure it's in your PATH."
        )
    if not FFPROBE or not shutil.which(FFPROBE):
        sys.exit(
            f"Error: ffprobe command ('{FFPROBE}') not found or not executable. Please install ffprobe (usually part of ffmpeg) and ensure it's in your PATH."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    video_extensions = ["*.mp4", "*.mkv", "*.mov", "*.avi", "*.webm"]
    vids = []
    for ext in video_extensions:
        vids.extend(list(Path(INPUT_DIR).glob(ext)))
    vids = sorted(list(set(vids)))  # Sort and remove duplicates.

    if not vids:
        sys.exit(f"No video files found in input directory: {INPUT_DIR}")

    print(f"Found {len(vids)} video(s) in '{INPUT_DIR}'. Processing...")
    print(f"Using ffmpeg: {FFMPEG}")
    print(f"crop_cuda filter available: {'YES' if HAS_CROP_CUDA else 'NO'}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Max parallel workers: {MAX_WORKERS}")
    print("-" * 30)

    overall_start_time = time.time()
    results_summary = []

    if MAX_WORKERS <= 1:  # Use 0 or 1 for sequential processing (easier debugging).
        print("INFO: Running in single-worker mode.")
        for v_path in vids:
            results_summary.append(handle(v_path))
    else:
        from concurrent.futures import ProcessPoolExecutor

        # Note: GPU contention can be an issue if MAX_WORKERS is too high for the GPU's capacity.
        try:
            with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
                results_summary = list(pool.map(handle, vids))
        except Exception as e:  # Catch errors during parallel execution setup.
            print(f"Error during parallel processing setup: {e}", file=sys.stderr)

    overall_time_taken = time.time() - overall_start_time
    print("-" * 30)
    print(f"✅ All processing complete in {overall_time_taken:.2f}s")

    # Summarize results based on status messages.
    successful_crops = sum(1 for r in results_summary if r and "crop[" in r)
    no_crops_no_detection = sum(
        1 for r in results_summary if r and "no-crop (copied original, no good detection)" in r
    )
    no_crops_bad_adjust = sum(
        1 for r in results_summary if r and "no-crop (adjusted rect not good/invalid)" in r
    )
    failures = sum(1 for r in results_summary if r and "FAILED" in r)

    print(
        f"Summary: {successful_crops} successful crops, "
        f"{no_crops_no_detection + no_crops_bad_adjust} no-crops (copied), "
        f"{failures} failures."
    )


if __name__ == "__main__":
    main()
