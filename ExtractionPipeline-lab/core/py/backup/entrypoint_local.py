#!/usr/bin/env python3
"""
Local test wrapper: instead of downloading from S3, processes all videos in ../videos/
and uploads extracted frames to S3 oriane-frames.
"""
import importlib
import os
import sys
import traceback
from pathlib import Path

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from dotenv import load_dotenv

# load AWS credentials (if present) and S3 target bucket
load_dotenv()
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_FRAMES_BUCKET = os.getenv("S3_FRAMES_BUCKET", "oriane-frames")


# choose signed or unsigned S3 access depending on whether creds exist
def _make_s3_client():
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        return boto3.client("s3", region_name=AWS_REGION)
    return boto3.client("s3", region_name=AWS_REGION, config=Config(signature_version=UNSIGNED))


s3 = _make_s3_client()

# import the crop & frame extraction module
crop_mod = importlib.import_module("crop_n_frame")


# upload helper (similar to entrypoint.py upload_frames) fileciteturn5file0
def upload_frames(platform: str, code: str, framedir: Path) -> None:
    for p in framedir.glob("*.png"):
        key = f"{platform}/{code}/{p.name}"
        print(f"  ↑ {S3_FRAMES_BUCKET}/{key}")
        s3.upload_file(str(p), S3_FRAMES_BUCKET, key, ExtraArgs={"ContentType": "image/png"})


def main() -> None:
    # you can override PLATFORM via env, default to 'instagram'
    platform = os.getenv("PLATFORM", "instagram")

    # Phase 1: crop all videos under INPUT_DIR (default ../videos) fileciteturn5file4
    crop_mod.phase1_crop()

    # Phase 2: extract frames into FRAMES_DIR (default ../output) fileciteturn5file4
    crop_mod.phase2_extract_sorted_frames()

    # Phase 3: deduplicate frames
    crop_mod.phase3_deduplicate_frames()

    # upload frames for each video subfolder under FRAMES_DIR
    for code_dir in crop_mod.FRAMES_DIR.iterdir():
        if code_dir.is_dir():
            code = code_dir.name
            upload_frames(platform, code, code_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
