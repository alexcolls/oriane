"""
────────────────
Asynchronous, fault-tolerant upload of final PNG frames to S3.

Public API
──────────
upload_frames_async(
    frames: Iterable[pathlib.Path],
    platform: str,          # e.g. "instagram"
    code: str,              # the content-code / short-code
    *,
    max_workers: int = 4    # concurrent uploads
)  → None   # fire-and-forget
"""

from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, List

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from config.env_config import settings
from config.logging_config import configure_logging

log = configure_logging()

# ---------------------------------------------------------------------
# Lazy S3 client  – only built when the first upload starts
# ---------------------------------------------------------------------
_S3 = None  # type: boto3.client | None


def _make_s3_client():
    """Create S3 client with environment credentials if available, otherwise use unsigned."""
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        return boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        )
    return boto3.client("s3", region_name=settings.aws_region, config=Config(signature_version=UNSIGNED))


def _get_s3():
    global _S3
    if _S3 is None:
        _S3 = _make_s3_client()
        if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
            log.debug("[upload] using signed S3 client")
        else:
            log.debug("[upload] using unsigned S3 client")
    return _S3


# ---------------------------------------------------------------------
# Internal helper – upload a single file
# ---------------------------------------------------------------------
def _upload_one(p: Path, bucket: str, key_prefix: str) -> None:
    key = f"{key_prefix}/{p.name}"
    try:
        _get_s3().upload_file(
            str(p),
            bucket,
            key,
            ExtraArgs={
                "ContentType": "image/png",
                "ACL": "bucket-owner-full-control",
            },
        )
    except Exception as e:
        log.warning(f"[upload] {p.name} → {key} failed: {e}")


# ---------------------------------------------------------------------
# Public API – fire-and-forget upload
# ---------------------------------------------------------------------
def upload_frames_async(
    frames: Iterable[Path],
    platform: str,
    code: str,
    *,
    max_workers: int = None,
) -> None:
    """
    Start a daemon thread that streams all `frames` to

        s3://{settings.s3_frames_bucket}/{platform}/{code}/

    Returns immediately; caller should NOT await.
    """
    paths: List[Path] = [Path(f) for f in frames]
    if not paths:
        return

    # Use configured max_workers if not specified
    max_workers = max_workers or settings.max_workers
    bucket = settings.s3_frames_bucket
    prefix = f"{platform}/{code}"

    def _bg():
        log.info(f"🚀 [upload] → s3://{bucket}/{prefix}/  ({len(paths)} frames)")
        completed = 0
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="s3u") as pool:
            futures = [pool.submit(_upload_one, p, bucket, prefix) for p in paths]
            for future in futures:
                try:
                    future.result()  # Wait for completion and catch exceptions
                    completed += 1
                    if len(paths) > 5 and completed % max(1, len(paths) // 5) == 0:
                        progress = (completed / len(paths)) * 100
                        log.debug(
                            f"📤 [upload] progress: {completed}/{len(paths)} ({progress:.0f}%)"
                        )
                except Exception as e:
                    log.warning(f"❌ [upload] frame upload failed: {e}")
        log.info(f"✅ [upload] done  {code}")

    threading.Thread(target=_bg, name=f"uploader-{code}", daemon=True).start()
