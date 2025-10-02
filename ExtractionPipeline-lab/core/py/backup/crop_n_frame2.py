#!/usr/bin/env python3
"""
 crop_n_frame.py – ONE‑SHOT pipeline
 ======================================
 ▸ Phase 1 – smart GPU border crop (see original gpu_batch_crop.py)
 ▸ Phase 2 – scene‑frame extraction (logic copied from frames.py)

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
from typing import Iterator, List, Optional, Tuple

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
TOLERANCE = 5
EDGE_THRESH = 10
MIN_CROP_RATIO = 0.10
DOWNSCALE = 0.5
FFMPEG_PROBES = 3
PROBE_CLIP_SECS = 2
SAFE_MARGIN_PX = 4

# scene‑frame extract
MIN_FRAMES = 4
SCENE_THRESH = 0.18

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
    codec = ffprobe_val(src, "codec_name")
    cuvid = DECODER.get(codec)
    # base=[FFMPEG,'-hide_banner','-loglevel','error']
    # inopts=[]
    # if HAS_CROP_CUDA:
    #     inopts += ['-hwaccel','cuda','-hwaccel_device','0','-hwaccel_output_format','cuda']
    #     vf = f'crop_cuda=w={w}:h={h}:x={x}:y={y},setsar=1:1,format=nv12'
    #     vfopts = ['-vf', vf]
    # elif cuvid:
    #     top,y1 = y, oh-(y+h)
    #     left,x1 = x, ow-(x+w)
    #     inopts += [
    #         '-hwaccel', 'cuda',
    #         '-hwaccel_device', '0',
    #         '-hwaccel_output_format', 'cuda',
    #         '-c:v', cuvid,
    #         '-crop', f'{top}x{y1}x{left}x{x1}'
    #     ]
    #     vfopts = ['-vf', 'setsar=1:1,format=nv12']
    # else:
    #     raise RuntimeError('No GPU crop path available')
    # ————————————————————————————————————————————————————————————
    # ALWAYS do CPU decode + crop, then GPU encode via h264_nvenc
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


def handle(src: Path) -> str:
    ow, oh = map(int, ffprobe_val(str(src), "width,height").split(","))
    dst = CROPPED_DIR / src.name
    rect = detect_crop_ffmpeg(str(src))
    mode = "ffmpeg"
    if not good(rect, ow, oh):
        alt = detect_gradient(str(src), ow, oh)
        if good(alt, ow, oh):
            rect, mode = alt, "gradient"
    if rect:
        crop_gpu(str(src), str(dst), rect, ow, oh)
        return f"crop[{mode}]"
    shutil.copy2(src, dst)
    return "copy"


# ─── Phase 2 – bring functions from frames.py (slightly trimmed) ─────────────


def detect_image_crop(img: np.ndarray, tol: int = 10):
    h, w = img.shape[:2]

    def blank(line):
        med = np.median(line, 0)
        return np.all(np.abs(line.astype(int) - med.astype(int)).sum(1) <= tol)

    x0 = next((x for x in range(w) if not blank(img[:, x, :])), w)
    x1 = next((x for x in range(w - 1, -1, -1) if not blank(img[:, x, :])), 0)
    y0 = next((y for y in range(h) if not blank(img[y, :, :])), h)
    y1 = next((y for y in range(h - 1, -1, -1) if not blank(img[y, :, :])), 0)
    if x0 >= x1 or y0 >= y1:
        return None
    return x0, y0, x1 - x0, y1 - y0


def ffmpeg_scene_jpgs(video: str, tmpdir: Path, thresh: float) -> List[Path]:
    tmpdir.mkdir(parents=True, exist_ok=True)
    pat = str(tmpdir / "%d.png")
    cmd = [
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        video,
        "-vf",
        f"select='gt(scene\,{thresh})'",
        "-vsync",
        "vfr",
        "-frame_pts",
        "1",
        "-q:v",
        "2",
        pat,
    ]
    subprocess.run(cmd, check=True)
    return sorted(Path(tmpdir).glob("*.png"), key=lambda p: int(p.stem.split("_", 1)[0]))


def extract_frames(video: Path):
    base = video.stem
    outdir = FRAMES_DIR / base
    print(f"  extracting frames for {video.name} → {outdir}")
    jpgs = ffmpeg_scene_jpgs(str(video), Path(outdir), SCENE_THRESH)
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.release()
    idx = 1
    for jpg in jpgs:
        img = cv2.imread(str(jpg))
        if img is None:
            jpg.unlink()
            continue
        rect = detect_image_crop(img)
        if rect:
            x, y, w, h = rect
            img = img[y : y + h, x : x + w]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if np.all(gray == gray[0, 0]):
            jpg.unlink()
            continue
        prefix = jpg.stem.split("_", 1)[0]
        frame_no = int(prefix)
        ts = frame_no / fps
        newname = f"{idx}_{ts:.2f}.png"
        cv2.imwrite(str(Path(outdir) / newname), img)
        jpg.unlink()
        idx += 1
    if idx <= MIN_FRAMES:
        print("    fallback grabbing more frames…")
        cap = cv2.VideoCapture(str(video))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, total // (MIN_FRAMES + 1))
        while idx <= MIN_FRAMES:
            pos = (idx - 1) * step
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            if not ret:
                break
            rect = detect_image_crop(frame) or (0, 0, frame.shape[1], frame.shape[0])
            x, y, w, h = rect
            frame = frame[y : y + h, x : x + w]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if np.all(gray == gray[0, 0]):
                continue
            ts = pos / fps
            outname = f"{idx}_{ts:.2f}.png"
            cv2.imwrite(str(Path(outdir) / outname), frame)
            idx += 1
        cap.release()
    print(f"    kept {idx-1} frames")


# ─── Main orchestrator ───────────────────────────────────────────────────────


def phase1_crop():
    vids = sorted(
        {p for ext in ("*.mp4", "*.mkv", "*.mov", "*.avi", "*.webm") for p in INPUT_DIR.glob(ext)}
    )
    if not vids:
        print("No videos found.")
        return
    CROPPED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Cropping {len(vids)} videos with {MAX_WORKERS} workers…")
    start = time.time()
    if MAX_WORKERS <= 1:
        for v in vids:
            handle(v)
    else:
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
            list(pool.map(handle, vids))
    print(f"Phase 1 done in {time.time()-start:.1f}s")


def phase2_extract():
    cropped = list(CROPPED_DIR.glob("*.mp4"))
    if not cropped:
        print("No cropped videos to extract from.")
        return
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Extracting scene frames from {len(cropped)} cropped videos…")
    for vid in cropped:
        extract_frames(vid)
    print("Phase 2 done.")
    if REMOVE_TMP:
        print("REMOVE_TMP = True → deleting temporary cropped videos…")
        for vid in cropped:
            vid.unlink()
        try:
            CROPPED_DIR.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    if not shutil.which(FFMPEG) or not shutil.which(FFPROBE):
        sys.exit("ffmpeg/ffprobe not found in PATH")
    start = time.time()
    phase1_crop()
    phase2_extract()
    print(f"Total time: {time.time() - start:.1f}s")
