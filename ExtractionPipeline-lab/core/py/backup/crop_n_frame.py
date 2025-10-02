#!/usr/binbin/env python3
"""
 crop_n_frame.py – ONE‑SHOT pipeline
 ======================================
 ▸ Phase 1 – smart GPU border crop (see original gpu_batch_crop.py)
 ▸ Phase 2 – scene‑frame extraction with non-informational frame removal (chronologically sorted, corrected timestamp calculation)
 ▸ Phase 3 – duplicate frame removal

 After the frames are written you can optionally wipe the temporary
 cropped videos by setting `REMOVE_TMP = True`.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple, Union

import cv2
import numpy as np

# ─── Global Config ────────────────────────────────────────────────────────────
INPUT_DIR = Path("../videos")  # raw originals
CROPPED_DIR = Path("../tmp")  # tmp mp4s after GPU crop
FRAMES_DIR = Path("../output")  # final jpgs per video

# speed / quality knobs
SAMPLE_FPS = 0.1  # 1 frame every 10 s for median & gradient
MAX_WORKERS = 4  # parallel GPU workers for Phase 1

# crop‑detect
TOLERANCE = 5  # For detect_image_crop (original script)
EDGE_THRESH = 10  # For detect_gradient
MIN_CROP_RATIO = 0.10
DOWNSCALE = 0.5  # Used to reduce the size for cropping detection
FFMPEG_PROBES = 3
PROBE_CLIP_SECS = 2
SAFE_MARGIN_PX = 4

# scene‑frame extract
MIN_FRAMES = 3
SCENE_THRESH = 0.22

# Non-informational frame detection
SOLID_COLOR_STD_THRESHOLD = 5.0  # Std dev below this per channel suggests solid color
MIN_IMAGE_DIM_FOR_SOLID_CHECK = 10  # Min H/W to use std dev check for solid color

# Duplicate frame detection
DHASH_SIZE = 8  # For dHash algorithm (e.g., 8x8 hash)

# housekeeping
REMOVE_TMP = False  # ← flip to True to delete CROPPED_DIR/**.mp4 at end

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"

# ─── tiny helpers ─────────────────────────────────────────────────────────────
DECODER = {
    "h264": "h264_cuvid",
    "hevc": "hevc_cuvid",
    "vp9": "vp9_cuvid",
    "av1": "av1_cuvid",
    "mpeg2video": "mpeg2_cuvid",
}


def ffprobe_val(src: str, key: str) -> str:
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
    try:
        out = subprocess.check_output([FFMPEG, "-hide_banner", "-filters"], text=True)
        return name in out
    except Exception:
        return False


HAS_CROP_CUDA = ff_has_filter("crop_cuda")


def even(x: int) -> int:
    return x if x % 2 == 0 else x + 1


# ─── sampling iterator (unchanged) ────────────────────────────────────────────


def iter_sampled_frames(src: str, ow: int, oh: int) -> Iterator[np.ndarray]:
    sw, sh = even(int(ow * DOWNSCALE)), even(int(oh * DOWNSCALE))
    frame_bytes = sw * sh * 3
    vf = f"fps={SAMPLE_FPS},scale={sw}:{sh}"
    cmd = [
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",
        "-hwaccel",
        "auto",
        "-i",
        src,
        "-vf",
        vf,
        "-pix_fmt",
        "rgb24",
        "-f",
        "rawvideo",
        "-",
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=frame_bytes * 8
    )
    try:
        while True:
            buf = proc.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            yield np.frombuffer(buf, np.uint8).reshape(sh, sw, 3)
    finally:
        proc.stdout.close()
        proc.stderr.close()
        proc.wait()


# ─── ffmpeg cropdetect union (Phase 1 detector) ──────────────────────────────


def detect_crop_ffmpeg(src: str) -> Optional[Tuple[int, int, int, int]]:
    dur = float(ffprobe_val(src, "duration") or 0)
    if dur == 0:
        return None
    rects: List[Tuple[int, int, int, int]] = []
    for k in range(FFMPEG_PROBES):
        ts = dur * (k + 1) / (FFMPEG_PROBES + 1)
        cmd = [
            FFMPEG,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{ts:.3f}",
            "-t",
            str(PROBE_CLIP_SECS),
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
    x0 = min(r[0] for r in rects) - SAFE_MARGIN_PX
    y0 = min(r[1] for r in rects) - SAFE_MARGIN_PX
    x1 = max(r[0] + r[2] for r in rects) + SAFE_MARGIN_PX
    y1 = max(r[1] + r[3] for r in rects) + SAFE_MARGIN_PX
    return max(0, x0), max(0, y0), x1 - x0, y1 - y0


# ─── gradient fallback (simpler, reused) ─────────────────────────────────────


def detect_gradient(src: str, ow: int, oh: int) -> Optional[Tuple[int, int, int, int]]:
    heat = None
    for small in iter_sampled_frames(src, ow, oh):
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
        sx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(sx, sy)
        heat = mag if heat is None else heat + mag
    if heat is None:
        return None
    norm = cv2.normalize(heat, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, mask = cv2.threshold(norm, EDGE_THRESH, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    x, y, w, h = cv2.boundingRect(max(cnts, key=cv2.contourArea))
    s = 1 / DOWNSCALE
    return int(x * s), int(y * s), int(w * s), int(h * s)


# good‑enough check
def good(rect, ow, oh):
    if not rect:
        return False
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return False
    sig = (w < ow * (1 - MIN_CROP_RATIO)) or (h < oh * (1 - MIN_CROP_RATIO))
    sens = w > 0.05 * ow and h > 0.05 * oh
    return sig and sens


# ─── GPU crop+encode ─────────────────────────────────────────────────────────


def crop_gpu(src: str, dst: str, rect: Tuple[int, int, int, int], ow: int, oh: int):
    x, y, w, h = rect
    w, h = even(w), even(h)
    base = [FFMPEG, "-hide_banner", "-loglevel", "error"]
    inopts = ["-i", src]
    vfopts = ["-vf", f"crop=w={w}:h={h}:x={x}:y={y},setsar=1:1,format=nv12"]
    outopts = [
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
        dst,
    ]
    cmd = base + inopts + vfopts + outopts
    subprocess.run(cmd, check=True)


# ─── worker for Phase 1 ──────────────────────────────────────────────────────


def handle(src: Path):
    """
    Phase-1 worker executed via ProcessPoolExecutor.

    * Reads the source video’s width/height with ffprobe.
    * Decides whether to copy or crop it.
    * Saves the result inside the shared TMP_DIR.
    * Returns a tuple describing the action, or None when the
      video is unreadable (so the caller can filter it out).

    A corrupt or 0-byte file is **skipped** instead of crashing
    the whole batch.
    """
    # ------------------------------------------------------------ #
    # 1) probe the file                                            #
    # ------------------------------------------------------------ #
    dims = ffprobe_val(str(src), "width,height")

    if not dims or "," not in dims:  # empty / missing stream
        print(f"[warn] ffprobe returned no dimensions for {src}")
        return None

    try:
        ow, oh = map(int, dims.split(","))
    except ValueError:  # malformed output
        print(f"[warn] malformed ffprobe output for {src}: {dims!r}")
        return None

    # ------------------------------------------------------------ #
    # 2) choose the processing mode                                #
    # ------------------------------------------------------------ #
    if ow < 320 or oh < 320:  # tiny clip → just copy
        mode = "copy"
        dst = TMP_DIR / src.name
        shutil.copy2(src, dst)

    elif oh > ow * 1.33:  # tall story → smart-crop
        mode = "crop[gradient]"
        dst = TMP_DIR / src.name
        crop_vertical_with_gradient(src, dst)

    else:  # regular landscape/square
        mode = "copy"
        dst = TMP_DIR / src.name
        shutil.copy2(src, dst)

    # ------------------------------------------------------------ #
    # 3) report back to the caller                                #
    # ------------------------------------------------------------ #
    return mode, src, dst


# ─── Phase 2 Helper Functions: Non-Informational Frame Detection ─────────────


def is_solid_color_frame(img: np.ndarray) -> bool:
    """Checks if an image is predominantly a single solid color."""
    if img is None:
        return True
    h, w = img.shape[:2]
    if h < MIN_IMAGE_DIM_FOR_SOLID_CHECK or w < MIN_IMAGE_DIM_FOR_SOLID_CHECK:
        return is_monochrome_solid_frame(img)

    try:
        b, g, r = cv2.split(img)
        return (
            np.std(b) < SOLID_COLOR_STD_THRESHOLD
            and np.std(g) < SOLID_COLOR_STD_THRESHOLD
            and np.std(r) < SOLID_COLOR_STD_THRESHOLD
        )
    except cv2.error:
        return is_monochrome_solid_frame(img)


def is_monochrome_solid_frame(img: np.ndarray) -> bool:
    """Checks if an image is a single solid shade of gray (including black or white)."""
    if img is None:
        return True
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return True

    if len(img.shape) == 3 and img.shape[2] == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif len(img.shape) == 2:
        gray = img
    else:
        return False

    return np.all(gray == gray[0, 0])


def detect_image_crop(img: np.ndarray, tol: int = TOLERANCE):
    """Detects letterbox/pillarbox borders in an image (from original script)."""
    if img is None:
        return None
    h, w = img.shape[:2]
    if h == 0 or w == 0:
        return None

    if len(img.shape) == 2 or img.shape[2] == 1:
        img_bgr = cv2.cvtColor(
            img, cv2.COLOR_GRAY2BGR if len(img.shape) == 2 else cv2.COLOR_GRAY2BGR
        )
    elif img.shape[2] == 4:
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    elif img.shape[2] == 3:
        img_bgr = img
    else:
        return None

    def blank(line):
        med = np.median(line, axis=0)
        return np.all(np.sum(np.abs(line.astype(np.int32) - med.astype(np.int32)), axis=1) <= tol)

    x0 = next((x for x in range(w) if not blank(img_bgr[:, x, :])), w)
    x1 = next((x for x in range(w - 1, -1, -1) if not blank(img_bgr[:, x, :])), 0)
    y0 = next((y for y in range(h) if not blank(img_bgr[y, :, :])), h)
    y1 = next((y for y in range(h - 1, -1, -1) if not blank(img_bgr[y, :, :])), 0)

    if x0 >= x1 or y0 >= y1:
        return None
    return x0, y0, x1 - x0, y1 - y0


def _process_and_save_frame(
    img_to_process: np.ndarray,
    outdir: Path,
    source_frame_id_log: str,
    timestamp: float,
    sequential_idx: int,
) -> bool:
    """
    Helper to process a single frame (crop, check non-informational) and save it.
    Returns True if frame was saved, False otherwise.
    `source_frame_id_log` is for logging.
    `sequential_idx` is the strictly sequential number for the output filename prefix.
    """
    if img_to_process is None:
        return False

    processed_img = img_to_process
    rect = detect_image_crop(img_to_process)
    if rect:
        x, y, w_crop, h_crop = rect
        if w_crop <= 0 or h_crop <= 0:
            print(
                f"    Skipping frame from source {source_frame_id_log} due to invalid internal crop dimensions ({w_crop}x{h_crop})"
            )
            return False
        processed_img = img_to_process[y : y + h_crop, x : x + w_crop]

    if processed_img.shape[0] < 1 or processed_img.shape[1] < 1:
        print(f"    Skipping frame from source {source_frame_id_log} as it became empty after crop")
        return False

    if is_solid_color_frame(processed_img):
        print(
            f"    Skipping save for non-informational (solid color) post-crop frame from source {source_frame_id_log}"
        )
        return False
    if is_monochrome_solid_frame(processed_img):
        print(
            f"    Skipping save for non-informational (monochrome) post-crop frame from source {source_frame_id_log}"
        )
        return False

    newname = f"{sequential_idx}_{timestamp:.2f}.png"
    try:
        cv2.imwrite(str(outdir / newname), processed_img)
        return True
    except Exception as e:
        print(f"    Error saving frame {newname} from source {source_frame_id_log}: {e}")
        return False


# ─── Phase 2 – Frame Extraction with Non-Informational Removal & Chronological Sort ───────────────


def ffmpeg_scene_jpgs(video: str, tmpdir: Path, thresh: float) -> List[Path]:
    """Extracts scene keyframes using ffmpeg."""
    tmpdir.mkdir(parents=True, exist_ok=True)
    pat = str(tmpdir / "%d.png")

    # Corrected f-string to avoid SyntaxWarning for invalid escape sequence
    # The comma in gt(scene,0.18) needs to be escaped for ffmpeg's select filter.
    # Using \\, ensures Python produces a literal string with \ before ,
    select_filter_expression = f"select='gt(scene\\,{thresh})'"

    cmd_final = [
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video,
        "-vf",
        select_filter_expression,
        "-vsync",
        "vfr",
        "-frame_pts",
        "1",
        "-q:v",
        "2",
        pat,
    ]
    subprocess.run(cmd_final, check=True)

    return sorted(tmpdir.glob("*.png"), key=lambda p: int(p.stem))


def extract_frames(video_path: Path):
    """Extracts, processes, and saves frames from a single video, ensuring chronological order."""
    base_name = video_path.stem
    output_dir = FRAMES_DIR / base_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Extracting frames for {video_path.name} → {output_dir}")

    ffmpeg_temp_outdir = output_dir / "_ffmpeg_scene_frames"
    if ffmpeg_temp_outdir.exists():
        shutil.rmtree(ffmpeg_temp_outdir)
    ffmpeg_temp_outdir.mkdir(parents=True, exist_ok=True)

    initial_ffmpeg_png_paths = ffmpeg_scene_jpgs(str(video_path), ffmpeg_temp_outdir, SCENE_THRESH)

    cap_check = cv2.VideoCapture(str(video_path))
    fps = cap_check.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames_in_video = int(cap_check.get(cv2.CAP_PROP_FRAME_COUNT))
    cap_check.release()

    candidate_frames_data: List[Tuple[float, Union[str, np.ndarray], str, Optional[np.ndarray]]] = (
        []
    )

    for ffmpeg_png_path in initial_ffmpeg_png_paths:
        try:
            original_frame_number_str = ffmpeg_png_path.stem

            if fps > 0:
                actual_timestamp = float(original_frame_number_str) / fps
            else:
                print(
                    f"    Warning: Invalid FPS ({fps}) for {video_path.name}. Treating ffmpeg stem '{original_frame_number_str}' as seconds for now."
                )
                actual_timestamp = float(original_frame_number_str)

        except ValueError:
            print(
                f"    Warning: Could not parse frame number from ffmpeg filename {ffmpeg_png_path.name}, skipping."
            )
            continue

        img_original = cv2.imread(str(ffmpeg_png_path))
        if img_original is None:
            print(f"    Warning: Could not read ffmpeg frame {ffmpeg_png_path.name}, skipping.")
            continue

        if is_solid_color_frame(img_original) or is_monochrome_solid_frame(img_original):
            print(
                f"    Skipping non-informational ffmpeg frame {ffmpeg_png_path.name} (TS: {actual_timestamp:.2f}s) during collection."
            )
            continue

        candidate_frames_data.append(
            (actual_timestamp, str(ffmpeg_png_path), "ffmpeg_scene", img_original)
        )

    current_candidate_count = len(candidate_frames_data)
    if current_candidate_count < MIN_FRAMES:
        print(
            f"    Too few frames ({current_candidate_count}), fallback grabbing more to reach {MIN_FRAMES}…"
        )
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"    Error: Could not open video {video_path.name} for fallback.")
        else:
            frames_needed_from_fallback = MIN_FRAMES - current_candidate_count
            step = (
                max(1, total_frames_in_video // (frames_needed_from_fallback + 1))
                if total_frames_in_video > 0
                else 1
            )
            attempted_fallback_grabs = 0
            max_attempts_for_fallback = (
                frames_needed_from_fallback * 5 if total_frames_in_video > 0 else 0
            )
            fallback_added_count = 0

            while (
                fallback_added_count < frames_needed_from_fallback
                and attempted_fallback_grabs < max_attempts_for_fallback
            ):
                current_pos = attempted_fallback_grabs * step
                if total_frames_in_video > 0:
                    current_pos %= total_frames_in_video
                else:
                    break

                cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
                ret, frame_raw = cap.read()
                attempted_fallback_grabs += 1

                if not ret:
                    print(
                        f"    Fallback: cap.read() failed at pos {current_pos}. May be end of video."
                    )
                    break

                actual_timestamp_fallback = current_pos / fps if fps > 0 else float(current_pos)

                if is_solid_color_frame(frame_raw) or is_monochrome_solid_frame(frame_raw):
                    print(
                        f"    Skipping non-informational fallback frame at TS: {actual_timestamp_fallback:.2f}s during collection."
                    )
                    continue

                candidate_frames_data.append(
                    (actual_timestamp_fallback, frame_raw, "fallback", frame_raw)
                )
                fallback_added_count += 1
            cap.release()

    candidate_frames_data.sort(key=lambda x: x[0])

    final_saved_count = 0
    for idx, (actual_ts, frame_source_or_data, source_type, img_for_processing) in enumerate(
        candidate_frames_data
    ):
        log_source_id = f"{source_type}_origTS_{actual_ts:.2f}"

        if _process_and_save_frame(
            img_for_processing, output_dir, log_source_id, actual_ts, final_saved_count + 1
        ):
            final_saved_count += 1

    print(
        f"    Kept {final_saved_count} frames for {base_name} (after sorting and final processing)."
    )

    if ffmpeg_temp_outdir.exists():
        try:
            shutil.rmtree(ffmpeg_temp_outdir)
        except OSError as e:
            print(f"    Warning: Could not remove temp dir {ffmpeg_temp_outdir}: {e}")


# ─── Phase 3 Helper Functions: Duplicate Frame Detection ───────────────────


def dhash(image: np.ndarray, hash_size: int = DHASH_SIZE) -> int:
    """Computes the Difference Hash (dHash) for an image."""
    if image is None:
        raise ValueError("Input image for dhash cannot be None.")
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (hash_size + 1, hash_size))
    except cv2.error as e:
        return hash(image.tobytes()[:128])

    diff = resized[:, 1:] > resized[:, :-1]
    return sum([2**i for i, v in enumerate(diff.flatten()) if v])


def remove_duplicates_in_folder(folder_path: Path):
    """Removes duplicate image files in a given folder based on dHash."""
    hashes = {}
    frames_to_remove: List[Path] = []

    frame_files = sorted(
        list(folder_path.glob("*.png")),
        key=lambda p: int(p.stem.split("_")[0]) if "_" in p.stem else -1,
    )

    if not frame_files:
        print(f"    No .png frames found in {folder_path.name} to deduplicate.")
        return

    print(f"    Processing {len(frame_files)} frames in {folder_path.name} for duplicates...")
    kept_count = 0
    removed_count = 0

    for frame_file in frame_files:
        try:
            img = cv2.imread(str(frame_file))
            if img is None:
                print(
                    f"      Warning: Could not read {frame_file.name} during deduplication, skipping."
                )
                continue

            current_hash = dhash(img)

            if current_hash in hashes:
                frames_to_remove.append(frame_file)
                removed_count += 1
                print(
                    f"      Marking duplicate: {frame_file.name} (same as {hashes[current_hash].name})"
                )
            else:
                hashes[current_hash] = frame_file
                kept_count += 1
        except Exception as e:
            print(f"      Error processing {frame_file.name} for dhash: {e}. Keeping file.")
            hashes[str(frame_file.name)] = frame_file
            kept_count += 1

    for frame_file in frames_to_remove:
        print(f"      Removing duplicate: {frame_file.name}")
        try:
            frame_file.unlink()
        except OSError as e:
            print(f"      Error unlinking duplicate {frame_file.name}: {e}")

    print(
        f"    Finished deduplication for {folder_path.name}. Kept: {kept_count}, Removed: {removed_count}"
    )


# ─── Main orchestrator ───────────────────────────────────────────────────────


def phase1_crop() -> None:
    """Phase 1 – copy or crop every video in INPUT_DIR."""
    vids: List[Path] = sorted(
        {p for ext in ("*.mp4", "*.mkv", "*.mov", "*.avi", "*.webm") for p in INPUT_DIR.glob(ext)}
    )
    if not vids:
        print("No videos found in INPUT_DIR.")
        return

    CROPPED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Phase 1: Cropping {len(vids)} videos with up to {MAX_WORKERS} workers…")
    t0 = time.time()

    # ---------- run the workers ----------
    if MAX_WORKERS <= 1:
        raw_results = [handle(v) for v in vids]
    else:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
            raw_results = list(pool.map(handle, vids))

    # ---------- summarise ----------
    action_counts: Dict[str, int] = {}
    skipped = 0

    for res in raw_results:
        if res is None:  # corrupt or unreadable file
            skipped += 1
            continue
        mode, _src, _dst = res
        action_counts[mode] = action_counts.get(mode, 0) + 1

    print(f"Phase 1 summary: {action_counts}  (skipped: {skipped})")
    print(f"Phase 1 done in {time.time() - t0:.1f}s")


def phase2_extract_sorted_frames():
    """Phase 2: Extract, sort, and save frames from cropped videos."""
    cropped_videos = sorted(list(CROPPED_DIR.glob("*.mp4")))
    if not cropped_videos:
        print("No cropped videos found in CROPPED_DIR to extract frames from.")
        return

    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nPhase 2: Extracting, sorting, and saving frames from {len(cropped_videos)} videos…")
    start_time = time.time()

    for video_path in cropped_videos:
        extract_frames(video_path)

    print(f"Phase 2 (Frame Extraction & Sorting) done in {time.time()-start_time:.1f}s")

    if REMOVE_TMP:
        print("REMOVE_TMP is True → Deleting temporary cropped videos…")
        for vid_path in cropped_videos:
            try:
                vid_path.unlink()
            except OSError as e:
                print(f"  Error deleting {vid_path}: {e}")
        try:
            CROPPED_DIR.rmdir()
            print(f"  Removed {CROPPED_DIR}")
        except OSError:
            print(f"  {CROPPED_DIR} not removed (might not be empty or other issue).")
            pass


def phase3_deduplicate_frames():
    """Phase 3: Remove duplicate frames from each video's output directory."""
    print(f"\nPhase 3: Deduplicating frames in {FRAMES_DIR}...")
    start_time = time.time()
    processed_video_dirs = 0

    if not FRAMES_DIR.exists():
        print(f"  Frames directory {FRAMES_DIR} does not exist. Skipping deduplication.")
        return

    for video_frame_dir in FRAMES_DIR.iterdir():
        if video_frame_dir.is_dir() and not video_frame_dir.name.startswith("_"):
            remove_duplicates_in_folder(video_frame_dir)
            processed_video_dirs += 1

    if processed_video_dirs == 0:
        print("  No frame directories found to deduplicate.")

    print(f"Phase 3 (Deduplication) done in {time.time()-start_time:.1f}s")


if __name__ == "__main__":
    if not shutil.which(FFMPEG) or not shutil.which(FFPROBE):
        sys.exit("Error: ffmpeg and/or ffprobe not found in PATH. Please install them.")

    try:
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        sys.exit(f"Error creating base directory {INPUT_DIR}: {e}")

    overall_start_time = time.time()

    phase1_crop()
    phase2_extract_sorted_frames()
    phase3_deduplicate_frames()

    print(f"\nAll phases complete. Total time: {time.time() - overall_start_time:.1f}s")
