"""
Phase 0 – Raw-video download
────────────────────────────
*  Primary source  :   S3  (`s3://{S3_VIDEOS_BUCKET}/{platform}/{code}/video.mp4`)
*  Fallback        :   local file  (`workdir/{code}.mp4`) when platform == "local"

Public API
──────────
download_video(platform:str, code:str, workdir:Path, overwrite=False) → Path|None
batch_download(items:Iterable[dict], workdir:Path) → list[Path]

`items` must contain at least {"platform","code"}.
Network errors are swallowed and logged so the pipeline can keep going.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from botocore.exceptions import ClientError
from config.env_config import settings
from config.logging_config import configure_logging
from config.profiler import profile

log = configure_logging()
__all__ = ["download_video", "batch_download"]

# ─────────────────────── S3 client helper ──────────────────────────
_S3: boto3.client | None = None  # start empty


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
    if _S3 is None:  # build exactly once, but *after* .env loaded
        _S3 = _make_s3_client()
    return _S3  # singleton


# ─────────────────────── public helpers ────────────────────────────
@profile
def download_video(
    platform: str, code: str, workdir: Path, *, overwrite: bool = False
) -> Optional[Path]:

    workdir.mkdir(parents=True, exist_ok=True)
    dst = workdir / f"{code}.mp4"

    # local short-circuit
    if platform == "local":
        return dst if dst.exists() else None

    if dst.exists() and not overwrite:
        return dst

    key = f"{platform}/{code}/video.mp4"
    log.info(f"[download] ↓ s3://{settings.s3_videos_bucket}/{key}")

    try:
        _get_s3().download_file(settings.s3_videos_bucket, key, str(dst))
        return dst

    except ClientError as e:
        err_code = e.response.get("Error", {}).get("Code", "")
        if err_code in ("404", "NoSuchKey", "403", "Forbidden"):
            log.warning(f"[download] access denied or not found: {key} ({err_code})")
            return None
        raise

    except Exception as ex:
        log.exception(f"[download] failed: {ex}")
        return None


@profile
def batch_download(items: Iterable[Dict[str, str]], workdir: Path) -> List[Path]:
    """
    Download many videos; preserves order.  Missing files are *not*
    included in the returned list (they're simply skipped).
    """
    paths: List[Path] = []
    for itm in items:
        platform = itm.get("platform")
        code = itm.get("code")
        if not platform or not code:
            log.warning(f"[download] bad item {itm} – skipping")
            continue

        p = download_video(platform, code, workdir)
        if p is not None:
            paths.append(p)

    return paths


# ───────────────────────── CLI helper ──────────────────────────────
if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Download raw videos from S3.")
    parser.add_argument(
        "items", help='JSON string, e.g. \'[{"platform":"instagram","code":"abcd"}]\''
    )
    parser.add_argument(
        "-o",
        "--out",
        type=Path,
        default=Path("videos"),
        help="Local working directory for .mp4 files",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-download even if the file already exists locally",
    )
    args = parser.parse_args()

    try:
        items_obj = json.loads(args.items)
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON for --items: {e}")

    paths = batch_download(items_obj, args.out)
    print(f"Downloaded {len(paths)} file(s):")
    for p in paths:
        print(" •", p)
