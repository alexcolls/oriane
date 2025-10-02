import os
import json
import tempfile
import shutil
import logging
import time
import cv2
import random
import boto3
import botocore
from botocore.exceptions import ClientError
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional, Dict, Any
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from supabase import create_client
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
    raise RuntimeError("Missing one of required env vars: "
                       "S3_BUCKET_VIDEOS, S3_BUCKET_FRAMES, SUPABASE_URL, SUPABASE_KEY")

# Optional tuning
S3_RETRIES         = int(os.getenv('S3_RETRIES', '3'))
S3_RETRY_DELAY_MS  = int(os.getenv('S3_RETRY_DELAY', '1000'))
S3_CONNECT_TIMEOUT = int(os.getenv('S3_CONNECT_TIMEOUT', '10'))
S3_READ_TIMEOUT    = int(os.getenv('S3_READ_TIMEOUT', '60'))
S3_UPLOAD_THREADS  = int(os.getenv('S3_UPLOAD_THREADS', '4'))

MIN_FRAMES         = int(os.getenv('MIN_FRAMES', '3'))
SCENE_THRESHOLD    = float(os.getenv('SCENE_THRESHOLD', '27.0'))

CONCURRENCY_LIMIT  = int(os.getenv('CONCURRENCY_LIMIT', '2'))
MIN_REMAINING_MS   = int(os.getenv('MIN_REMAINING_MS', '60000'))

DEBUG              = os.getenv('DEBUG', 'true').lower() == 'true'
DEBUG_DEEP         = os.getenv('DEBUG_DEEP', 'false').lower() == 'true'

# ─── Clients & Logging ────────────────────────────────────────────────────────
botocore_cfg = botocore.config.Config(
    retries={'max_attempts': S3_RETRIES, 'mode': 'standard'},
    connect_timeout=S3_CONNECT_TIMEOUT,
    read_timeout=S3_READ_TIMEOUT,
)
s3_client = boto3.client('s3', region_name=AWS_REGION, config=botocore_cfg)
supabase  = create_client(SUPABASE_URL, SUPABASE_KEY)

root_logger = logging.getLogger()
if DEBUG_DEEP:
    root_logger.setLevel(logging.DEBUG)
elif DEBUG:
    root_logger.setLevel(logging.INFO)
else:
    root_logger.setLevel(logging.WARNING)

class ShortcodeFilter(Filter):
    def filter(self, record):
        record.shortcode = getattr(record, 'shortcode', '-')
        return True

handler = StreamHandler()
handler.addFilter(ShortcodeFilter())
handler.setFormatter(Formatter("%(asctime)s %(levelname)s [%(shortcode)s] %(message)s"))
root_logger.handlers = [handler]

def get_logger(shortcode: Optional[str] = None) -> LoggerAdapter:
    return LoggerAdapter(root_logger, {'shortcode': shortcode or '-'})

# ─── Supabase Helpers ─────────────────────────────────────────────────────────

def fetch_video_info(code: str) -> Tuple[bool, bool]:
    log = get_logger(code)
    try:
        resp = (supabase.table('insta_content')
                          .select('is_downloaded,is_extracted')
                          .eq('code', code)
                          .maybe_single()
                          .execute())
        row = resp.data
        if not row:
            log.info("No record found")
            return False, False
        return bool(row['is_downloaded']), bool(row['is_extracted'])
    except Exception as e:
        log.error(f"Supabase fetch error: {e}")
        return False, False

def update_supabase_extracted(code: str, frame_count: int) -> None:
    log = get_logger(code)
    try:
        supabase.table('insta_content') \
                .update({'is_extracted': True, 'frames': frame_count}) \
                .eq('code', code) \
                .execute()
        log.info(f"Marked is_extracted, frames={frame_count}")
    except Exception as e:
        log.error(f"Error marking extracted: {e}")

# ─── S3 Helpers ───────────────────────────────────────────────────────────────

def s3_video_exists(platform: str, code: str) -> bool:
    key = f"{platform}/{code}/video.mp4"
    try:
        s3_client.head_object(Bucket=S3_BUCKET_VIDEOS, Key=key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] in ('404', 'NoSuchKey'):
            return False
        raise

def download_video(platform: str, code: str) -> Optional[str]:
    log = get_logger(code)
    key = f"{platform}/{code}/video.mp4"
    for attempt in range(1, S3_RETRIES + 1):
        fd, local_path = tempfile.mkstemp(suffix='.mp4')
        os.close(fd)
        try:
            s3_client.download_file(S3_BUCKET_VIDEOS, key, local_path)
            log.info(f"Downloaded {key} (attempt {attempt})")
            return local_path
        except Exception as e:
            log.error(f"Download attempt {attempt} failed: {e}")
            if os.path.exists(local_path):
                os.remove(local_path)
            if attempt < S3_RETRIES:
                time.sleep(S3_RETRY_DELAY_MS / 1000.0)
    log.error(f"All download attempts failed for {key}")
    return None

def upload_frames(paths: List[str], platform: str, code: str, record_error) -> bool:
    log = get_logger(code)

    def _upload(path: str) -> bool:
        name = os.path.basename(path)
        key  = f"{platform}/{code}/frames/{name}"
        backoff = 1.0

        if not os.path.exists(path) or os.path.getsize(path) == 0:
            msg = f"Local frame missing or empty: {path}"
            record_error(msg)
            return False

        for attempt in range(1, S3_RETRIES + 1):
            try:
                s3_client.upload_file(path, S3_BUCKET_FRAMES, key)
                os.remove(path)
                log.info(f"Uploaded {key} (attempt {attempt})")
                return True
            except Exception as e:
                msg = f"S3 upload error on attempt {attempt}: {e}"
                log.error(msg)
                record_error(msg)
            if attempt < S3_RETRIES:
                sleep = backoff * (1 + random.random()*0.1)
                time.sleep(sleep)
                backoff *= 2

        record_error(f"Failed all {S3_RETRIES} uploads for {key}")
        return False

    with ThreadPoolExecutor(max_workers=S3_UPLOAD_THREADS) as pool:
        results = pool.map(_upload, paths)
    return all(results)

# ─── Frame Extraction ────────────────────────────────────────────────────────

def detect_scenes(video_path: str) -> List[Tuple[Any,Any]]:
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=SCENE_THRESHOLD))
    manager.detect_scenes(open_video(video_path))
    return manager.get_scene_list()

def extract_key_frames(
    video_path: str,
    out_dir: str,
    context,
    code: str,
    record_error
) -> List[str]:
    log = get_logger(code)

    # Timeout guard
    if context and context.get_remaining_time_in_millis() < MIN_REMAINING_MS:
        record_error("Aborted: low remaining time")
        return []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        record_error("Cannot open video")
        return []

    try:
        scenes = detect_scenes(video_path)
    except Exception as e:
        record_error(f"Scene detection failed: {e}")
        cap.release()
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = [
        (s.get_frames()+e.get_frames())//2
        for s,e in scenes
    ]
    if len(indices) < MIN_FRAMES:
        step = max(1, total_frames // (MIN_FRAMES+1))
        fallback = [i*step for i in range(1, MIN_FRAMES+1)]
        indices = sorted(set(indices + fallback))

    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for idx, frame_no in enumerate(indices):
        if frame_no<0 or frame_no>=total_frames:
            record_error(f"Frame {frame_no} out of bounds")
            continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = cap.read()
        if not ret or frame is None:
            record_error(f"Failed to read frame at {frame_no}")
            continue
        path = os.path.join(out_dir, f"{idx}.jpg")
        if not cv2.imwrite(path, frame):
            record_error(f"cv2.imwrite failed at frame {frame_no}")
            continue
        saved.append(path)
    cap.release()
    log.info(f"Extracted {len(saved)} frames")
    return saved

# ─── Record Processing ───────────────────────────────────────────────────────

def process_record(record, context):
    # now each record.body = '{"items":[{"platform":"instagram","code":"ABC123"},…]}'
    batch = json.loads(record.get('body','{}')).get('items', [])
    results = []
    for item in batch:
        results.append(process_single(item['platform'], item['code'], context))
    return results

def process_single(platform: str, code: str, context) -> Dict[str,Any]:
    log = get_logger(code)
    errors: List[str] = []
    def record_error(msg: str):
        errors.append(msg)

    # 1) Quick timeout bail-out
    if context and context.get_remaining_time_in_millis() < MIN_REMAINING_MS:
        record_error("Skipped: low remaining time at start")
        status = {'status':'skipped','shortcode':code}
    else:
        # 2) Check S3
        try:
            if not s3_video_exists(platform, code):
                record_error("Video not found in S3")
                supabase.table('insta_content') \
                        .update({'is_downloaded': False}) \
                        .eq('code', code).execute()
                status = {'status':'skipped','shortcode':code}
            else:
                # 3) Download
                path = download_video(platform, code)
                if not path:
                    record_error("Download failed")
                    status = {'status':'skipped','shortcode':code}
                else:
                    # 4) DB state
                    downloaded, extracted = fetch_video_info(code)
                    if extracted:
                        record_error("Already extracted")
                        status = {'status':'skipped','shortcode':code}
                    else:
                        # 5) Extract & upload
                        tmp = tempfile.mkdtemp()
                        try:
                            frames = extract_key_frames(path, tmp, context, code, record_error)
                            if not frames or not upload_frames(frames, platform, code, record_error):
                                raise RuntimeError("Extraction/upload failure")
                            update_supabase_extracted(code, len(frames))
                            status = {'status':'extracted','shortcode':code,'frames':len(frames)}
                        except Exception as e:
                            record_error(str(e))
                            status = {'status':'error','shortcode':code,'message':str(e)}
                        finally:
                            shutil.rmtree(tmp, ignore_errors=True)
                            os.remove(path)
        except Exception as e:
            record_error(f"Unexpected error: {e}")
            status = {'status':'error','shortcode':code,'message':str(e)}

    # 6) Persist all errors
    if errors:
        try:
            supabase.table('extraction_errors') \
                    .insert([{'code':code,'error':msg} for msg in errors]) \
                    .execute()
        except Exception as e:
            log.error(f"Failed to persist errors: {e}")

    return status

# ─── Lambda Entry Point ─────────────────────────────────────────────────────

def lambda_handler(event, context):
    raw = event.get('Records', [])
    results = []
    with ThreadPoolExecutor(max_workers=CONCURRENCY_LIMIT) as pool:
        futures = []
        for rec in raw:
            try:
                body = json.loads(rec.get('body','{}'))
                items = body.get('items', [])
                for it in items:
                    futures.append(
                        pool.submit(process_single, it.get('platform',''), it.get('code',''), context)
                    )
            except Exception as e:
                get_logger().error(f"Bad SQS payload: {e}")
        for f in as_completed(futures):
            results.append(f.result())
    return {'status':'completed', 'results': results}
