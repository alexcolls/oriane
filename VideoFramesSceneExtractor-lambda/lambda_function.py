import os
import json
import tempfile
import shutil
import logging
import time
import subprocess
import cv2
import numpy as np
import random
import boto3
import botocore
from glob import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional, Dict, Any
from supabase import create_client
from botocore.exceptions import ClientError
from logging import LoggerAdapter, Filter, StreamHandler, Formatter
from dotenv import load_dotenv

# ─── Load & Validate Environment ─────────────────────────────────────────────
load_dotenv()

AWS_REGION         = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET_VIDEOS   = os.getenv('S3_BUCKET_VIDEOS')
S3_BUCKET_FRAMES   = os.getenv('S3_BUCKET_FRAMES')
SUPABASE_URL       = os.getenv('SUPABASE_URL')
SUPABASE_KEY       = os.getenv('SUPABASE_KEY')

if not all([S3_BUCKET_VIDEOS, S3_BUCKET_FRAMES, SUPABASE_URL, SUPABASE_KEY]):
    raise RuntimeError("Missing one of required env vars")

# Optional tuning
S3_RETRIES         = int(os.getenv('S3_RETRIES', '3'))
S3_RETRY_DELAY_MS  = int(os.getenv('S3_RETRY_DELAY', '1000'))
S3_CONNECT_TIMEOUT = int(os.getenv('S3_CONNECT_TIMEOUT', '10'))
S3_READ_TIMEOUT    = int(os.getenv('S3_READ_TIMEOUT', '60'))
S3_UPLOAD_THREADS  = int(os.getenv('S3_UPLOAD_THREADS', '4'))

MIN_FRAMES         = int(os.getenv('MIN_FRAMES', '4'))
SCENE_THRESHOLD    = float(os.getenv('SCENE_THRESHOLD', '0.12'))
IMAGE_CROP_TOL     = int(os.getenv('IMAGE_CROP_TOL', '10'))
FFMPEG_PATH        = os.getenv('FFMPEG_PATH', 'ffmpeg')
CONCURRENCY_LIMIT  = int(os.getenv('CONCURRENCY_LIMIT', '2'))
MIN_REMAINING_MS   = int(os.getenv('MIN_REMAINING_MS', '60000'))
DEBUG              = os.getenv('DEBUG', 'true').lower() == 'true'

# ─── Clients & Logging ────────────────────────────────────────────────────────
botocore_cfg = botocore.config.Config(
    retries={'max_attempts': S3_RETRIES, 'mode': 'standard'},
    connect_timeout=S3_CONNECT_TIMEOUT,
    read_timeout=S3_READ_TIMEOUT,
)
s3 = boto3.client('s3', region_name=AWS_REGION, config=botocore_cfg)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

root = logging.getLogger()
root.setLevel(logging.DEBUG if DEBUG else logging.INFO)
handler = StreamHandler()
handler.setFormatter(Formatter("%(asctime)s %(levelname)s [%(shortcode)s] %(message)s"))
root.handlers = [handler]

class ShortcodeFilter(Filter):
    def filter(self, record):
        record.shortcode = getattr(record, 'shortcode', '-')
        return True

handler.addFilter(ShortcodeFilter())

def get_logger(code: Optional[str]=None) -> LoggerAdapter:
    return LoggerAdapter(root, {'shortcode': code or '-'})

# ─── S3 + DB Helpers ──────────────────────────────────────────────────────────

def s3_key_exists(bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] in ('404', 'NoSuchKey'):
            return False
        raise

def download_video(platform: str, code: str) -> Optional[str]:
    log = get_logger(code)
    key = f"{platform}/{code}/video.mp4"
    for attempt in range(1, S3_RETRIES+1):
        fd, tmp_path = tempfile.mkstemp(suffix='.mp4')
        os.close(fd)
        try:
            s3.download_file(S3_BUCKET_VIDEOS, key, tmp_path)
            log.info(f"Downloaded {key}")
            return tmp_path
        except Exception as e:
            log.error(f"Download attempt {attempt} failed: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            if attempt < S3_RETRIES:
                time.sleep(S3_RETRY_DELAY_MS/1000.0)
    log.error(f"All downloads failed for {key}")
    return None

def upload_frame(path: str, platform: str, code: str, errors: List[str]) -> bool:
    key = f"{platform}/{code}/frames/{os.path.basename(path)}"
    for attempt in range(1, S3_RETRIES+1):
        try:
            s3.upload_file(path, S3_BUCKET_FRAMES, key)
            os.remove(path)
            return True
        except Exception as e:
            msg = f"Upload error attempt {attempt} for {key}: {e}"
            errors.append(msg)
            if attempt < S3_RETRIES:
                time.sleep((2 ** attempt) * (1 + random.random()*0.1))
    errors.append(f"Failed to upload {key}")
    return False

def update_db_extracted(code: str, count: int):
    supabase.table('insta_content') \
            .update({'is_extracted': True, 'frames': count}) \
            .eq('code', code) \
            .execute()

def record_errors(code: str, errors: List[str]):
    if not errors:
        return
    rows = [{'code': code, 'error': e} for e in errors]
    supabase.table('extraction_errors').insert(rows).execute()

# ─── Frame-Extraction Helpers ─────────────────────────────────────────────────

def detect_image_crop(img: np.ndarray, tol: int = IMAGE_CROP_TOL):
    h, w = img.shape[:2]

    def is_blank_line(line: np.ndarray) -> bool:
        """All pixels within tol of this line's median color?"""
        median_col = np.median(line, axis=0)
        diffs = np.abs(line.astype(int) - median_col.astype(int)).sum(axis=1)
        return np.all(diffs <= tol)

    # left
    x0 = 0
    for x in range(w):
        if is_blank_line(img[:, x, :]):
            x0 += 1
        else:
            break
    # right
    x1 = w
    for x in range(w - 1, -1, -1):
        if is_blank_line(img[:, x, :]):
            x1 -= 1
        else:
            break
    # top
    y0 = 0
    for y in range(h):
        if is_blank_line(img[y, :, :]):
            y0 += 1
        else:
            break
    # bottom
    y1 = h
    for y in range(h - 1, -1, -1):
        if is_blank_line(img[y, :, :]):
            y1 -= 1
        else:
            break

    # if nothing left, no crop
    if x0 >= x1 or y0 >= y1:
        return None
    return (x0, y0, x1 - x0, y1 - y0)

def ffmpeg_extract_with_pts(video_path: str, out_dir: str, threshold: float):
    os.makedirs(out_dir, exist_ok=True)
    pattern = os.path.join(out_dir, '%d.jpg')
    cmd = [
        FFMPEG_PATH, '-hide_banner', '-loglevel', 'error',
        '-i', video_path,
        '-vf', f"select='gt(scene,{threshold})'",
        '-vsync', 'vfr', '-frame_pts', '1', '-q:v', '2',
        pattern
    ]
    subprocess.run(cmd, check=True)
    imgs = []
    for file in glob(os.path.join(out_dir, '*.jpg')):
        frame_no = int(os.path.splitext(os.path.basename(file))[0])
        imgs.append((file, frame_no))
    imgs.sort(key=lambda x: x[1])
    return imgs

def extract_key_frames(video_path: str, out_dir: str, code: str, errors: List[str]):
    log = get_logger(code)
    # FFmpeg pass
    raw = ffmpeg_extract_with_pts(video_path, out_dir, SCENE_THRESHOLD)
    log.info(f"FFmpeg detected {len(raw)} scenes")
    # Probe FPS
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.release()
    # Crop, drop fully-blank, rename
    saved = 0
    for old_path, frame_no in raw:
        img = cv2.imread(old_path)
        if img is None:
            os.remove(old_path)
            continue
        rect = detect_image_crop(img)
        if rect:
            x,y,w,h = rect
            img = img[y:y+h, x:x+w]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if np.all(gray == gray[0,0]):
            os.remove(old_path)
            continue
        seconds = frame_no/fps
        new = os.path.join(out_dir, f"{saved+1}_{seconds:.2f}.jpg")
        cv2.imwrite(new, img)
        os.remove(old_path)
        saved += 1
    # Fallback sampling if too few frames
    if saved < MIN_FRAMES:
        log.info("Fallback to OpenCV sampling")
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(1, total//(MIN_FRAMES+1))
        for i in range(1, MIN_FRAMES+1):
            if saved >= MIN_FRAMES:
                break
            fn = i*step
            cap.set(cv2.CAP_PROP_POS_FRAMES, fn)
            ret, frame = cap.read()
            if not ret:
                continue
            # optional crop
            rect = detect_image_crop(frame)
            if rect:
                x,y,w,h = rect
                frame = frame[y:y+h, x:x+w]
            # drop fully-blank
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if np.all(gray == gray[0,0]):
                continue
            # save
            sec = fn/fps
            out = os.path.join(out_dir, f"{saved+1}_{sec:.2f}.jpg")
            cv2.imwrite(out, frame)
            saved += 1
        cap.release()
        log.info(f"Total after fallback: {saved}")
    else:
        log.info(f"Kept {saved} frames (>= {MIN_FRAMES})")

    # if we STILL got nothing, error out
    if saved == 0:
        raise RuntimeError("No frames extracted (FFmpeg & fallback both failed)")

    return [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith('.jpg')]

# ─── Core Processing ──────────────────────────────────────────────────────────

def process_single(item: Dict[str,str], context) -> Dict[str,Any]:
    platform, code = item['platform'], item['code']
    log = get_logger(code)
    errors: List[str] = []
    status = {}
    # Timeout guard
    if context and context.get_remaining_time_in_millis() < MIN_REMAINING_MS:
        errors.append("Timeout: low remaining time")
        status = {'shortcode': code, 'status': 'skipped'}
    else:
        # Check S3 source
        if not s3_key_exists(S3_BUCKET_VIDEOS, f"{platform}/{code}/video.mp4"):
            errors.append("Source video missing")
            status = {'shortcode': code, 'status': 'skipped'}
        else:
            vid = download_video(platform, code)
            if not vid:
                errors.append("Download failed")
                status = {'shortcode': code, 'status': 'skipped'}
            else:
                tmpdir = tempfile.mkdtemp()
                try:
                    frames = extract_key_frames(vid, tmpdir, code, errors)
                    ok = True
                    # upload with ThreadPool
                    with ThreadPoolExecutor(max_workers=S3_UPLOAD_THREADS) as pool:
                        futures = [ pool.submit(upload_frame, p, platform, code, errors) for p in frames ]
                        for f in as_completed(futures):
                            if not f.result():
                                ok = False
                    if not ok:
                        raise RuntimeError("One or more uploads failed")
                    update_db_extracted(code, len(frames))
                    status = {'shortcode': code, 'status': 'extracted', 'frames': len(frames)}
                except Exception as e:
                    log.error(f"Processing error: {e}")
                    errors.append(str(e))
                    status = {'shortcode': code, 'status': 'error', 'message': str(e)}
                finally:
                    shutil.rmtree(tmpdir, ignore_errors=True)
                    os.remove(vid)
    # persist errors
    record_errors(code, errors)
    return status

def lambda_handler(event, context):
    # Support two shapes:
    # 1) API-style:   { "items": [ { platform, code }, … ] }
    # 2) SQS-style:   { "Records": [ { body: '{"platform":"…","code":"…"}' }, … ] }
    if "items" in event:
        items = event["items"]
    elif "Records" in event:
        items = []
        for rec in event["Records"]:
            try:
                body = rec.get("body", "")
                data = json.loads(body)
                # if body itself has an "items" array, unpack it; else treat as single item
                if isinstance(data, dict) and "items" in data:
                    items.extend(data["items"])
                else:
                    items.append(data)
            except Exception:
                # ignore bad record
                continue
    else:
        items = []

    results = []
    # Sequential processing (no threads)
    for item in items:
        try:
            res = process_single(item, context)
        except Exception as e:
            # Catch any unexpected error so one bad video
            # doesn't abort the whole batch
            get_logger(item.get('code')).error(f"Unhandled error: {e}")
            res = {
                'shortcode': item.get('code'),
                'status': 'error',
                'message': str(e)
            }
        results.append(res)

    return {
        'status': 'completed',
        'results': results
    }
