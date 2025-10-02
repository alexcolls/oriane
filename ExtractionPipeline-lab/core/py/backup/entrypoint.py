#!/usr/bin/env python3
"""
AWS Batch job wrapper
Expects one env var, JOB_INPUT:
  '[{"platform":"instagram", "code":"abddb8"}, …]'
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict

import boto3
import psycopg2
from botocore import UNSIGNED
from botocore.client import Config
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.errors import ForeignKeyViolation

# ---------------------------------------------------------------------------
# initialisation
# ---------------------------------------------------------------------------
load_dotenv(".env")

# AWS / S3 config
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_VIDEOS_BUCKET = os.getenv("S3_VIDEOS_BUCKET", "oriane-contents")
S3_FRAMES_BUCKET = os.getenv("S3_FRAMES_BUCKET", "oriane-frames")

# DB config (Aurora Postgres)
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    raise RuntimeError("DB_HOST, DB_NAME, DB_USER and DB_PASSWORD must be set")

# choose signed or unsigned S3 access depending on whether credentials exist
if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
    s3 = boto3.client("s3", region_name=AWS_REGION)
else:
    s3 = boto3.client("s3", region_name=AWS_REGION, config=Config(signature_version=UNSIGNED))

# open a single shared DB connection
_pg_conn = psycopg2.connect(
    host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
)
_pg_conn.autocommit = True  # we commit per statement

# heavy CV pipeline – import lazily to avoid CUDA init if job fails early
crop_n_frame = importlib.import_module("crop_n_frame")
frames_embeddings = importlib.import_module("frames_embeddings")


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# S3 helpers
# ---------------------------------------------------------------------------


def download_video(platform: str, code: str, workdir: Path) -> Path:
    key = f"{platform}/{code}/video.mp4"
    dst = workdir / f"{code}.mp4"
    log(f"  ↓ {S3_VIDEOS_BUCKET}/{key}")
    try:
        s3.download_file(S3_VIDEOS_BUCKET, key, dst)
    except s3.exceptions.NoSuchKey:
        print(f"[warn] {S3_VIDEOS_BUCKET}/{key} does not exist – skipping")
        return None
    return dst


def upload_frames(platform: str, code: str, framedir: Path) -> None:
    for p in framedir.glob("*.png"):
        key = f"{platform}/{code}/{p.name}"
        log(f"  ↑ {S3_FRAMES_BUCKET}/{key}")
        s3.upload_file(str(p), S3_FRAMES_BUCKET, key, ExtraArgs={"ContentType": "image/png"})


# ---------------------------------------------------------------------------
# Aurora Postgres helpers
# ---------------------------------------------------------------------------


def mark_done(code: str, cropped: bool, number_of_frames: int) -> None:
    """Update insta_content row for this code."""
    with _pg_conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """
                UPDATE insta_content
                SET is_extracted = TRUE,
                    is_cropped   = %s,
                    frames       = %s
                WHERE code = %s
            """
            ),
            [cropped, number_of_frames, code],
        )


def record_err(code: str, err: Exception) -> None:
    """
    Insert into extraction_errors; skip if FK constraint blocks us.
    """
    try:
        with _pg_conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    """
                  INSERT INTO extraction_errors(code, error)
                  VALUES (%s, %s)
                """
                ),
                [code, str(err)],
            )
    except ForeignKeyViolation:
        # insta_content row may not exist yet—ignore
        log(f"[warn] could not record error for {code}: foreign key violation")


# ---------------------------------------------------------------------------
# main pipeline
# ---------------------------------------------------------------------------


def process_item(item: Dict[str, Any], workdir: Path) -> None:
    platform: str = item["platform"]
    code: str = item["code"]
    try:
        video_path = download_video(platform, code, workdir)

        # configure crop module directories
        crop_n_frame.INPUT_DIR = workdir
        crop_n_frame.CROPPED_DIR = workdir / "tmp"
        crop_n_frame.FRAMES_DIR = workdir / "frames"

        crop_n_frame.phase1_crop()
        crop_n_frame.phase2_extract_sorted_frames()
        crop_n_frame.phase3_deduplicate_frames()

        cropped_file = crop_n_frame.CROPPED_DIR / f"{code}.mp4"
        cropped = cropped_file.exists()

        frame_dir = crop_n_frame.FRAMES_DIR / code
        upload_frames(platform, code, frame_dir)

        frames_embeddings.embed_directory(frame_dir, platform=platform, video=code)

        frame_count = len(list(frame_dir.glob("*.png")))
        mark_done(code, cropped, frame_count)

    except Exception as e:  # noqa: BLE001  (broad but we then log)
        traceback.print_exc()
        record_err(code, e)


def main() -> None:
    items = json.loads(os.environ["JOB_INPUT"])
    with tempfile.TemporaryDirectory() as td:
        workdir = Path(td)
        for item in items:
            process_item(item, workdir)


if __name__ == "__main__":
    main()
