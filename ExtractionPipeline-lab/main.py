#!/usr/bin/env python3
"""
Batch Orchestrator - main.py
───────────────────────────
Implements batch processing orchestrator following the specified algorithm:

1. Read checkpoint → cursor_id (default 0)
2. Loop:
   a. rows = next_batch(1000, cursor_id) ordered by id asc
   b. If empty ➜ break
   c. Build job_input = [{"platform": r.platform, "code": r.code} for r in rows]
   d. Invoke pipeline through subprocess.run with JOB_INPUT=json.dumps(job_input)
   e. After success, call mark_extracted([r.id …]);
      Qdrant upsert from pipeline will be polled and then mark_embedded
   f. Update checkpoint with highest id
   g. Sleep small delay to avoid DB hammering
3. Catch subprocess.CalledProcessError — log and continue (do not advance checkpoint)
   Use tqdm progress bar for total processed count.
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
import tqdm
from dotenv import load_dotenv
from psycopg2.extras import DictCursor
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv(".env")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("batch_orchestrator.log"), logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Qdrant configuration
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_KEY = os.getenv("QDRANT_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "watched_frames")

# Processing configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
SLEEP_DELAY = float(os.getenv("SLEEP_DELAY", "0.5"))
CHECKPOINT_FILE = os.getenv("CHECKPOINT_FILE", "checkpoint.txt")
PIPELINE_SCRIPT = os.getenv("PIPELINE_SCRIPT", "core/py/pipeline/entrypoint.py")

# Ensure required environment variables are set
if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    log.error(
        "Missing required database environment variables: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD"
    )
    sys.exit(1)


class BatchOrchestrator:
    """Batch processing orchestrator for video extraction pipeline."""

    def __init__(self):
        self.db_conn = None
        self.qdrant_client = None
        self.checkpoint_id = 0
        self.total_processed = 0
        self.setup_connections()
        self.load_checkpoint()

    def setup_connections(self):
        """Initialize database and Qdrant connections."""
        try:
            # Setup database connection
            self.db_conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                cursor_factory=DictCursor,
            )
            self.db_conn.autocommit = True
            log.info(f"✅ Database connected: {DB_HOST}:{DB_PORT}/{DB_NAME}")

            # Setup Qdrant client if configured
            if QDRANT_URL:
                self.qdrant_client = QdrantClient(
                    url=QDRANT_URL.rstrip("/"), api_key=QDRANT_KEY or None, prefer_grpc=True
                )
                log.info(f"✅ Qdrant connected: {QDRANT_URL}")
            else:
                log.warning("⚠️ QDRANT_URL not configured, skipping Qdrant connection")

        except Exception as e:
            log.error(f"❌ Connection setup failed: {e}")
            sys.exit(1)

    def load_checkpoint(self):
        """Load checkpoint from file."""
        try:
            if Path(CHECKPOINT_FILE).exists():
                with open(CHECKPOINT_FILE, "r") as f:
                    self.checkpoint_id = int(f.read().strip())
                log.info(f"📍 Loaded checkpoint: cursor_id={self.checkpoint_id}")
            else:
                log.info(f"📍 No checkpoint found, starting from cursor_id=0")
        except Exception as e:
            log.warning(f"⚠️ Failed to load checkpoint: {e}, starting from 0")
            self.checkpoint_id = 0

    def save_checkpoint(self, cursor_id: int):
        """Save checkpoint to file."""
        try:
            with open(CHECKPOINT_FILE, "w") as f:
                f.write(str(cursor_id))
            self.checkpoint_id = cursor_id
            log.debug(f"💾 Checkpoint saved: cursor_id={cursor_id}")
        except Exception as e:
            log.error(f"❌ Failed to save checkpoint: {e}")

    def next_batch(self, limit: int, cursor_id: int) -> List[Dict[str, Any]]:
        """
        Fetch next batch of rows from the database.

        Args:
            limit: Maximum number of rows to fetch
            cursor_id: Starting ID for the batch

        Returns:
            List of rows with 'id', 'platform', 'code' fields
        """
        try:
            with self.db_conn.cursor() as cur:
                # Query for unprocessed content ordered by id ASC
                cur.execute(
                    """
                    SELECT id, 'instagram' as platform, code
                    FROM insta_content
                    WHERE id > %s
                      AND is_downloaded = true
                      AND (is_extracted IS NULL OR is_extracted = false)
                    ORDER BY id ASC
                    LIMIT %s
                """,
                    [cursor_id, limit],
                )

                rows = cur.fetchall()
                log.debug(f"🔍 Fetched {len(rows)} rows from database (cursor_id > {cursor_id})")
                return [dict(row) for row in rows]

        except Exception as e:
            log.error(f"❌ Database query failed: {e}")
            return []

    def mark_extracted(self, row_ids: List[int]):
        """Mark rows as extracted in the database."""
        if not row_ids:
            return

        try:
            with self.db_conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE insta_content
                    SET is_extracted = true
                    WHERE id = ANY(%s)
                """,
                    [row_ids],
                )

                log.debug(f"✅ Marked {len(row_ids)} rows as extracted")

        except Exception as e:
            log.error(f"❌ Failed to mark rows as extracted: {e}")

    def mark_embedded(self, row_ids: List[int]):
        """Mark rows as embedded in the database."""
        if not row_ids:
            return

        try:
            with self.db_conn.cursor() as cur:
                # Check if we have an is_embedded column, if not, we'll skip this step
                cur.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'insta_content'
                      AND column_name = 'is_embedded'
                """
                )

                if cur.fetchone():
                    cur.execute(
                        """
                        UPDATE insta_content
                        SET is_embedded = true
                        WHERE id = ANY(%s)
                    """,
                        [row_ids],
                    )
                    log.debug(f"✅ Marked {len(row_ids)} rows as embedded")
                else:
                    log.debug("⚠️ No is_embedded column found, skipping embedding status update")

        except Exception as e:
            log.error(f"❌ Failed to mark rows as embedded: {e}")

    def wait_for_qdrant_upsert(self, expected_count: int, timeout: int = 60) -> bool:
        """
        Poll Qdrant to verify that embeddings have been upserted.

        Args:
            expected_count: Expected number of new points
            timeout: Maximum time to wait in seconds

        Returns:
            True if upsert verified, False if timeout
        """
        if not self.qdrant_client:
            log.debug("⚠️ No Qdrant client, skipping upsert verification")
            return True

        try:
            initial_count = self.qdrant_client.count(collection_name=QDRANT_COLLECTION).count
            start_time = time.time()

            while time.time() - start_time < timeout:
                current_count = self.qdrant_client.count(collection_name=QDRANT_COLLECTION).count
                new_points = current_count - initial_count

                if new_points >= expected_count:
                    log.debug(f"✅ Qdrant upsert verified: {new_points} new points")
                    return True

                time.sleep(1)  # Poll every second

            log.warning(
                f"⚠️ Qdrant upsert timeout: expected {expected_count}, got {current_count - initial_count}"
            )
            return False

        except Exception as e:
            log.error(f"❌ Failed to verify Qdrant upsert: {e}")
            return False

    def run_pipeline(self, job_input: List[Dict[str, str]]) -> bool:
        """
        Run the extraction pipeline via subprocess.

        Args:
            job_input: List of {"platform": str, "code": str} items

        Returns:
            True if pipeline succeeded, False otherwise
        """
        try:
            # Convert job input to JSON
            job_input_json = json.dumps(job_input, separators=(",", ":"))

            # Prepare environment with JOB_INPUT
            env = os.environ.copy()
            env["JOB_INPUT"] = job_input_json

            # Construct command
            cmd = [sys.executable, PIPELINE_SCRIPT]

            log.info(f"🚀 Running pipeline with {len(job_input)} items")
            log.debug(f"Command: {' '.join(cmd)}")

            # Run pipeline
            result = subprocess.run(
                cmd, env=env, capture_output=True, text=True, timeout=3600  # 1 hour timeout
            )

            if result.returncode == 0:
                log.info(f"✅ Pipeline completed successfully")
                log.debug(f"Pipeline stdout: {result.stdout[-500:]}")  # Last 500 chars
                return True
            else:
                log.error(f"❌ Pipeline failed with return code {result.returncode}")
                log.error(f"Pipeline stderr: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            log.error(f"❌ Pipeline timeout after 1 hour")
            return False
        except subprocess.CalledProcessError as e:
            log.error(f"❌ Pipeline subprocess error: {e}")
            return False
        except Exception as e:
            log.error(f"❌ Pipeline execution error: {e}")
            return False

    def run(self):
        """Main orchestrator loop."""
        log.info("🎬 Starting batch orchestrator")
        log.info(f"📊 Configuration: batch_size={BATCH_SIZE}, sleep_delay={SLEEP_DELAY}s")

        # Initialize progress bar
        pbar = tqdm.tqdm(desc="Processing batches", unit="items", initial=self.total_processed)

        try:
            while True:
                # Fetch next batch
                rows = self.next_batch(BATCH_SIZE, self.checkpoint_id)

                if not rows:
                    log.info("🏁 No more rows to process, stopping")
                    break

                # Build job input
                job_input = [{"platform": row["platform"], "code": row["code"]} for row in rows]

                row_ids = [row["id"] for row in rows]
                highest_id = max(row_ids)

                log.info(
                    f"📦 Processing batch: {len(rows)} items (ids {min(row_ids)}-{highest_id})"
                )

                # Run pipeline
                success = self.run_pipeline(job_input)

                if success:
                    # Mark as extracted
                    self.mark_extracted(row_ids)

                    # Wait for Qdrant upsert and mark as embedded
                    if self.wait_for_qdrant_upsert(len(rows)):
                        self.mark_embedded(row_ids)

                    # Update checkpoint
                    self.save_checkpoint(highest_id)

                    # Update progress
                    self.total_processed += len(rows)
                    pbar.update(len(rows))

                    log.info(f"✅ Batch completed: {len(rows)} items processed")
                else:
                    log.error(f"❌ Batch failed, not advancing checkpoint")

                # Small delay to avoid DB hammering
                time.sleep(SLEEP_DELAY)

        except KeyboardInterrupt:
            log.info("🛑 Received interrupt signal, stopping gracefully")
        except Exception as e:
            log.error(f"❌ Orchestrator error: {e}")
        finally:
            pbar.close()
            self.cleanup()

        log.info(f"🎯 Orchestrator finished: {self.total_processed} total items processed")

    def cleanup(self):
        """Clean up connections."""
        try:
            if self.db_conn:
                self.db_conn.close()
                log.debug("🔌 Database connection closed")
        except Exception as e:
            log.error(f"❌ Cleanup error: {e}")


def main():
    """Entry point for the batch orchestrator."""
    orchestrator = BatchOrchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
