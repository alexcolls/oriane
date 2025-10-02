#!/usr/bin/env python3
"""
Video-pipeline job driver
─────────────────────────
Reads JOB_INPUT (JSON list of {"platform","code"})
┌── Phase 0 ── download video from S3  (or use existing local .mp4)
├── Phase 1-4 ─ process video through     video_pipeline.*
└── Phase 5 ──  upload frames to S3  +  mark row in Aurora PG

Everything heavy lives in *video_pipeline/*.  This script is just glue.

Resource Throttling:
- Sequential batch processing within pipeline to avoid GPU/memory exhaustion
- Configurable via CLI flags: --batch-size, --sleep
- Internal parallelism limited to max_workers (default: 4)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import psycopg2
from botocore import UNSIGNED
from botocore.client import Config

# ── internal packages ───────────────────────────────────────────
from config.env_config import settings
from config.logging_config import configure_logging

# ── third-party deps ────────────────────────────────────────────────
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.errors import ForeignKeyViolation
from src.download_videos import download_video
from src.pipeline import VideoPipeline
from src.verify_embedded import mark_embedded_codes

# ── initialisation ─────────────────────────────────────────────────
# Try to load .env from multiple possible locations
env_paths = [".env", "/app/.env", "/app/pipeline/.env"]
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break
        
log = configure_logging()

# ---------- ENV / secrets ----------
# Enforce environment-based authentication - remove AWS_PROFILE to prevent profile override
os.environ.pop("AWS_PROFILE", None)  # enforce env-based auth

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_VIDEOS_BUCKET = os.getenv("S3_VIDEOS_BUCKET", "oriane-contents")
S3_FRAMES_BUCKET = os.getenv("S3_FRAMES_BUCKET", "oriane-frames")

DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

LOCAL_MODE = bool(int(os.getenv("LOCAL_MODE", "0")))  # 1 → skip Aurora writes
SKIP_UPLOAD = bool(int(os.getenv("SKIP_UPLOAD", "0")))  # 1 → skip S3 frame upload

# ---------- AWS clients ----------
def _make_s3_client():
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        return boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        )
    return boto3.client("s3", region_name=AWS_REGION, config=Config(signature_version=UNSIGNED))

s3 = _make_s3_client()

# ---------- Aurora PG ----------
_pg = None
if not LOCAL_MODE:
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        sys.exit("DB_* env-vars must be set (or LOCAL_MODE=1)")

    _pg = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )
    _pg.autocommit = True


# ───────────── Postgres helpers (no-ops when LOCAL_MODE) ────────────
def _exec(query: str, params: List[Any]) -> None:
    if LOCAL_MODE:
        return
    with _pg.cursor() as cur:
        cur.execute(query, params)


def mark_done(code: str, cropped: bool, frame_count: int) -> None:
    _exec(
        """
        UPDATE insta_content
           SET is_extracted = TRUE,
               is_cropped   = %s,
               frames       = %s
         WHERE code = %s
        """,
        [cropped, frame_count, code],
    )


def record_err(code: str, err: Exception) -> None:
    try:
        _exec(
            "INSERT INTO extraction_errors(code, error) VALUES (%s, %s)",
            [code, str(err)],
        )
    except ForeignKeyViolation:
        log.warning(f"[db] FK violation while recording error for {code}")


# ───────────── S3 upload helper (no-op when SKIP_UPLOAD) ────────────
def upload_frames(platform: str, code: str) -> int:
    if SKIP_UPLOAD:
        return 0

    frame_dir = settings.frames_dir / code
    if not frame_dir.exists():
        return 0

    uploaded = 0
    for p in frame_dir.glob("*.png"):
        key = f"{platform}/{code}/{p.name}"
        s3.upload_file(str(p), S3_FRAMES_BUCKET, key, ExtraArgs={"ContentType": "image/png"})
        uploaded += 1

    log.info(f"[upload] {uploaded} frames → s3://{S3_FRAMES_BUCKET}/{platform}/{code}/")
    return uploaded


# ───────────── single item orchestrator ────────────────────────────
def process_item(item: Dict[str, Any], workdir: Path, item_idx: int, total_items: int) -> bool:
    """Process a single item and return True on success, False on failure."""
    platform = item["platform"]
    code = item["code"]

    # Log item progress
    item_progress = ((item_idx + 1) / total_items) * 100
    log.info(
        f"🔄 [item {item_idx + 1}/{total_items}] processing {code} ({item_progress:.1f}% total)"
    )
    log.info(f"⬇️ [download] ↓ s3://{S3_VIDEOS_BUCKET}/{platform}/{code}/video.mp4")
    try:
        # ----- 0) fetch or locate source video -----------------------
        log.info(f"[download] ↓ s3://{S3_VIDEOS_BUCKET}/{platform}/{code}/video.mp4")
        local_mp4 = workdir / f"{code}.mp4"
        if not local_mp4.exists():
            # download (handles anonymous or signed clients automatically)
            found = download_video(platform, code, workdir, overwrite=False)
            if found is None:
                raise FileNotFoundError(f"S3 key {platform}/{code}/video.mp4 not found")
            local_mp4 = found

        # ----- 1-4) computer-vision pipeline -------------------------
        VideoPipeline().run(local_mp4)

        # ----- 5) upload frames & DB status -------------------------
        frames = upload_frames(platform, code)
        cropped = (settings.tmp_dir / local_mp4.name).exists()
        mark_done(code, cropped, frames)

        log.info(f"✅ [ok] {code}: frames={frames}")
        return True
    except Exception as exc:
        log.error(f"❌ [fail] {code}: {exc}")
        traceback.print_exc()
        record_err(code, exc)
        return False


# ───────────── entrypoint ───────────────────────────────────────────
def main() -> None:
    # Parse CLI arguments for batch processing configuration
    parser = argparse.ArgumentParser(
        description="Video extraction pipeline entrypoint with resource throttling"
    )
    parser.add_argument(
        "--batch-size", type=int, default=8, help="Batch size for frame processing (default: 8)"
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Sleep duration between batches in seconds (default: 0.5)",
    )
    args = parser.parse_args()

    # Override environment settings with CLI arguments
    if args.batch_size:
        os.environ["VP_BATCH_SIZE"] = str(args.batch_size)
    if args.sleep:
        os.environ["VP_SLEEP_BETWEEN_BATCHES"] = str(args.sleep)

    log.info(
        f"[entrypoint] Resource throttling config: "
        f"batch_size={args.batch_size}, sleep_between_batches={args.sleep}s"
    )

    raw = os.getenv("JOB_INPUT")
    if not raw:
        sys.exit("JOB_INPUT env var missing (should be JSON list of {platform,code})")

    try:
        items: List[Dict[str, Any]] = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"JOB_INPUT is not valid JSON: {e}")

    log.info(
        f"📎 [batch] {len(items)} item(s) received  |  "
        f"LOCAL_MODE={LOCAL_MODE}  SKIP_UPLOAD={SKIP_UPLOAD}"
    )

    # use a temp dir for videos; frames/tmp dirs are already configured in settings
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        processed_codes = []
        failed_count = 0

        for idx, itm in enumerate(items):
            if not {"platform", "code"} <= itm.keys():
                log.warning(f"[skip] bad item structure: {itm}")
                failed_count += 1
                continue

            try:
                success = process_item(itm, workdir, idx, len(items))
                if success:
                    processed_codes.append(itm["code"])
                else:
                    failed_count += 1

                # Add a small delay between items to allow resource recovery
                if idx < len(items) - 1:  # Don't sleep after last item
                    time.sleep(0.1)  # Brief pause between items

            except Exception as e:
                log.error(
                    f"[batch] Uncaught exception processing {itm.get('code', 'unknown')}: {e}"
                )
                failed_count += 1

        # Step 6: Embedded status verification
        if processed_codes:
            log.info(
                f"🔍 [verify] checking embedded status for {len(processed_codes)} processed codes"
            )
            try:
                mark_embedded_codes(processed_codes)
                log.info("✅ [verify] embedded status verification complete")
            except Exception as e:
                log.error(f"❌ [verify] embedded status verification failed: {e}")
                traceback.print_exc()
                failed_count += 1

        # Exit with non-zero status if any items failed
        if failed_count > 0:
            log.error(f"[batch] {failed_count}/{len(items)} items failed in this batch")
            sys.exit(1)


if __name__ == "__main__":
    main()
