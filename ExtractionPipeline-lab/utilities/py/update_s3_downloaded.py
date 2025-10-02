import logging
import math
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

import boto3
import psycopg2
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# ─── Configuration ────────────────────────────────────────────────────────────
load_dotenv()

S3_BUCKET = os.getenv("S3_VIDEOS_BUCKET", "oriane-contents")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

BATCH_SIZE = 1000
MAX_WORKERS = 12
CHUNK_SIZE = 100

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    raise RuntimeError("DB_HOST, DB_NAME, DB_USER and DB_PASSWORD must be set")

# ─── Logging & Clients ────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

s3_client = boto3.client("s3", region_name=AWS_REGION)

# open a single shared DB connection
_pg_conn = psycopg2.connect(
    host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
)
_pg_conn.autocommit = True


# ─── Helpers ──────────────────────────────────────────────────────────────────


def fetch_pending_codes(limit: int) -> List[str]:
    """Page through up to `limit` rows where is_downloaded is False."""
    with _pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT code
              FROM insta_content
             WHERE is_downloaded = FALSE
             LIMIT %s
            """,
            (limit,),
        )
        return [row[0] for row in cur.fetchall()]


def video_exists(code: str) -> bool:
    """Return True if instagram/<code>/video.mp4 exists in S3."""
    key = f"instagram/{code}/video.mp4"
    try:
        s3_client.head_object(Bucket=S3_BUCKET, Key=key)
        return True
    except ClientError as e:
        err = e.response["Error"]["Code"]
        if err in ("404", "NoSuchKey"):
            return False
        # transient error: re-raise so we can log+skip
        raise


# ─── Main Loop ────────────────────────────────────────────────────────────────


def main():
    total_checked = 0
    total_marked = 0

    while True:
        codes = fetch_pending_codes(BATCH_SIZE)
        if not codes:
            logger.info("✅ No more pending videos. All done!")
            break

        logger.info(f"🔎 Checking batch of {len(codes)} codes…")
        found: List[str] = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures: Dict = {pool.submit(video_exists, code): code for code in codes}
            for fut in as_completed(futures):
                code = futures[fut]
                try:
                    if fut.result():
                        found.append(code)
                except Exception as e:
                    logger.error(f"⚠️ Transient S3 error for {code}: {e}")

        # Batch-update all the found videos in chunks
        if found:
            num_chunks = math.ceil(len(found) / CHUNK_SIZE)
            logger.info(f"🚀 Marking {len(found)} videos as downloaded in {num_chunks} chunks")
            for idx in range(num_chunks):
                chunk = found[idx * CHUNK_SIZE : (idx + 1) * CHUNK_SIZE]
                with _pg_conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE insta_content
                           SET is_downloaded = TRUE
                         WHERE code = ANY(%s)
                        """,
                        (chunk,),
                    )
                logger.info(f"   → chunk {idx+1}/{num_chunks}: marked {len(chunk)} codes")
            total_marked += len(found)

        total_checked += len(codes)
        logger.info(f"➡️ Batch done: checked={len(codes)}, marked={len(found)}")

    logger.info(f"🏁 Finished: total_checked={total_checked}, total_marked={total_marked}")


if __name__ == "__main__":
    main()
