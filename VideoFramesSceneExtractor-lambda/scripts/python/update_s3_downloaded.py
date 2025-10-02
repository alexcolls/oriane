import math
import os
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.exceptions import ClientError
from supabase import create_client
from dotenv import load_dotenv

# ─── Configuration ────────────────────────────────────────────────────────────
load_dotenv()

S3_BUCKET         = os.getenv('S3_BUCKET_VIDEOS', 'oriane-contents')
AWS_REGION        = os.getenv('AWS_REGION', 'us-east-1')
SUPABASE_URL      = os.getenv('SUPABASE_URL')
SUPABASE_KEY      = os.getenv('SUPABASE_KEY')

BATCH_SIZE        = 1000
MAX_WORKERS       = 12
CHUNK_SIZE        = 100

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")

# ─── Logging & Clients ────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

s3_client = boto3.client('s3', region_name=AWS_REGION)
supabase  = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def fetch_pending_codes(limit: int) -> List[str]:
    """Page through up to `limit` rows where is_downloaded is False."""
    resp = (
        supabase
          .table('insta_content')
          .select('code')
          .eq('is_downloaded', False)
          .limit(limit)
          .execute()
    )
    data = resp.data or []
    return [row['code'] for row in data if 'code' in row]

def video_exists(code: str) -> bool:
    """Return True if instagram/<code>/video.mp4 exists in S3."""
    key = f"instagram/{code}/video.mp4"
    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=key)
        return True
    except ClientError as e:
        err = e.response['Error']['Code']
        if err in ('404', 'NoSuchKey'):
            return False
        # transient error: re-raise so we can log+skip
        raise

# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    total_checked = 0
    total_marked  = 0

    while True:
        codes = fetch_pending_codes(BATCH_SIZE)
        if not codes:
            logger.info("✅ No more pending videos. All done!")
            break

        logger.info(f"🔎 Checking batch of {len(codes)} codes…")
        found = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures: Dict = { pool.submit(video_exists, code): code for code in codes }
            for fut in as_completed(futures):
                code = futures[fut]
                try:
                    if fut.result():
                        found.append(code)
                except Exception as e:
                    logger.error(f"⚠️ Transient S3 error for {code}: {e}")

        # Batch-update all the found videos in one Supabase call:
        if found:
          logger.info(f"🚀 Marking {len(found)} videos as downloaded in {math.ceil(len(found)/CHUNK_SIZE)} chunks")
          for i in range(0, len(found), CHUNK_SIZE):
              chunk = found[i:i+CHUNK_SIZE]
              supabase \
                .table('insta_content') \
                .update({'is_downloaded': True}) \
                .in_('code', chunk) \
                .execute()
              logger.info(f"   → chunk {i//CHUNK_SIZE+1}: marked {len(chunk)} codes")

        total_checked += len(codes)
        logger.info(f"➡️ Batch done: checked={len(codes)}, marked={len(found)}")

    logger.info(f"🏁 Finished: total_checked={total_checked}, total_marked={total_marked}")

if __name__ == '__main__':
    main()
