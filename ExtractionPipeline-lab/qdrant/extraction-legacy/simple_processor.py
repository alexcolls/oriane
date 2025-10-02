#!/usr/bin/env python3
"""
Simple Instagram Video Processor
================================

This script:
1. Fetches Instagram codes from insta_content table (newest to oldest by publish_date)
2. Processes them in batches of 1000 through the core pipeline
3. No tracking of is_extracted/is_embedded - just pure processing

Usage:
    python3 simple_processor.py --batch-size 1000 --max-workers 8
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

# Core pipeline Python interpreter
CORE_VENV_PY = "/home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline/.venv/bin/python"


class SimpleInstagramProcessor:
    """Simple processor for Instagram videos from database."""

    def __init__(self, batch_size: int = 1000, max_workers: int = 1):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.processed_count = 0

        # Database connection
        self.db_url = os.getenv("ORIANE_ADMIN_DB_URL")
        if not self.db_url:
            raise ValueError("ORIANE_ADMIN_DB_URL environment variable is required")

    def get_instagram_codes(self, offset: int = 0) -> List[str]:
        """
        Get Instagram codes from database, ordered by publish_date DESC (newest first).

        Args:
            offset: Number of records to skip

        Returns:
            List of Instagram codes
        """
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = """
                        SELECT code
                        FROM public.insta_content
                        WHERE code IS NOT NULL
                        ORDER BY publish_date DESC
                        LIMIT %s OFFSET %s
                    """
                    cur.execute(query, (self.batch_size, offset))
                    results = cur.fetchall()
                    return [row["code"] for row in results]
        except Exception as e:
            print(f"❌ Database error: {e}")
            return []

    def process_single_video(self, code: str) -> bool:
        """
        Process a single Instagram video through the core pipeline.

        Args:
            code: Instagram video code

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare job input for core pipeline
            job_input = json.dumps([{"platform": "instagram", "code": code}])

            # Set up environment with memory optimization
            env = os.environ.copy()
            env["JOB_INPUT"] = job_input
            env["VIRTUAL_ENV"] = str(Path(CORE_VENV_PY).parent.parent)
            # Force CPU usage to avoid CUDA OOM with 6GB GPU
            env["CUDA_VISIBLE_DEVICES"] = ""
            env["FORCE_CPU"] = "1"

            # Sanity check
            if not Path(CORE_VENV_PY).exists():
                raise FileNotFoundError(f"Core venv python not found at {CORE_VENV_PY}")

            # Create timestamped log file for this specific video processing
            timestamp = time.strftime('%Y%m%d-%H%M%S')
            log_file = f"/home/quantium/labs/oriane/ExtractionPipeline/qdrant/extraction-legacy/logs/{timestamp}_{code}.log"
            
            # Ensure logs directory exists
            os.makedirs("/home/quantium/labs/oriane/ExtractionPipeline/qdrant/extraction-legacy/logs", exist_ok=True)
            
            print(f"  📄 Detailed logs: {log_file}")
            sys.stdout.flush()
            
            # Execute core pipeline with streaming output to both log file and console
            with open(log_file, "w") as f:
                f.write(f"=== Processing {code} at {timestamp} ===\n")
                f.write(f"Environment: {env.get('CUDA_VISIBLE_DEVICES', 'not set')} (CUDA), {env.get('FORCE_CPU', 'not set')} (CPU)\n")
                f.write(f"JOB_INPUT: {job_input}\n\n")
                
                result = subprocess.run(
                    [
                        CORE_VENV_PY,
                        "/home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline/entrypoint.py",
                    ],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=600,
                )
                
                # Write all output to log file
                if result.stdout:
                    f.write(result.stdout)
                
                # Also print key information to console for immediate feedback
                if result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if any(keyword in line for keyword in ['✅', '❌', '🔄', '⬇️', '📎', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']):
                            print(f"    {line}")
                            sys.stdout.flush()

            if result.returncode == 0:
                print(f"  ✅ {code} - SUCCESS")
                sys.stdout.flush()
                return True
            else:
                # Log full error message (stdout now contains both stdout and stderr)
                with open("/home/quantium/labs/oriane/ExtractionPipeline/qdrant/extraction-legacy/simple_processor_errors.log", "a") as err_log:
                    err_log.write(f"\n❌ {code} - FAILED\n{result.stdout or 'No output captured'}")
                    
                # Extract error details for console display
                error_lines = (result.stdout or '').split('\n')[-5:]  # Last 5 lines for context
                error_summary = ' | '.join([line.strip() for line in error_lines if line.strip()])
                print(f"  ❌ {code} - FAILED: {error_summary[:200]}...")  # Truncate for readability
                sys.stdout.flush()
                return False

        except subprocess.TimeoutExpired:
            print(f"  ⏰ {code} - TIMEOUT")
            return False
        except Exception as e:
            print(f"  💥 {code} - ERROR: {e}")
            return False

    def process_batch_parallel(self, codes: List[str]) -> int:
        """
        Process a batch of codes in parallel.

        Args:
            codes: List of Instagram codes to process

        Returns:
            Number of successful processes
        """
        if not codes:
            return 0

        print(f"\n🚀 Processing batch of {len(codes)} videos with {self.max_workers} workers...")
        sys.stdout.flush()
        successes = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_code = {
                executor.submit(self.process_single_video, code): code for code in codes
            }

            # Collect results with exception handling
            for future in as_completed(future_to_code):
                try:
                    result = future.result()
                    if result:
                        successes += 1
                except Exception as e:
                    code = future_to_code[future]
                    print(f"  💥 {code} - EXCEPTION: {type(e).__name__}: {e}")
                    sys.stdout.flush()
                    # Log the full traceback to a file for debugging
                    with open("/home/quantium/labs/oriane/ExtractionPipeline/qdrant/extraction-legacy/simple_processor_exceptions.log", "a") as ex_log:
                        import traceback
                        ex_log.write(f"\n\n{'='*50}\n")
                        ex_log.write(f"Exception for {code} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        ex_log.write(f"Exception type: {type(e).__name__}\n")
                        ex_log.write(f"Exception message: {e}\n")
                        ex_log.write("Full traceback:\n")
                        traceback.print_exc(file=ex_log)
                    # Continue processing other futures

        return successes

    def run(self):
        """Run the processing pipeline."""
        print("🎬 Starting Simple Instagram Video Processor")
        print(f"📊 Batch size: {self.batch_size}")
        print(f"⚡ Max workers: {self.max_workers}")
        print(f"🎯 Target: Instagram videos (newest to oldest)")
        sys.stdout.flush()  # Ensure immediate output

        offset = 0
        total_processed = 0
        total_successful = 0

        try:
            while True:
                # Get next batch
                print(f"\n📥 Fetching batch {offset // self.batch_size + 1} (offset: {offset})...")
                sys.stdout.flush()
                
                print("   🔄 Connecting to database...")
                sys.stdout.flush()
                codes = self.get_instagram_codes(offset)
                print(f"   ✅ Database query completed")
                sys.stdout.flush()

                if not codes:
                    print("🏁 No more videos to process!")
                    break

                print(f"📋 Found {len(codes)} codes: {codes[0]} ... {codes[-1]}")
                sys.stdout.flush()

                # Process batch
                start_time = time.time()
                successful = self.process_batch_parallel(codes)
                duration = time.time() - start_time

                # Update counters
                total_processed += len(codes)
                total_successful += successful
                offset += len(codes)

                # Progress report
                success_rate = (successful / len(codes)) * 100
                speed = len(codes) / duration if duration > 0 else 0

                print(f"\n📈 Batch Summary:")
                print(f"   ✅ Successful: {successful}/{len(codes)} ({success_rate:.1f}%)")
                print(f"   ⏱️  Duration: {duration:.1f}s ({speed:.1f} videos/sec)")
                print(f"   📊 Total: {total_successful}/{total_processed} videos processed")

                # Memory cleanup delay between batches
                time.sleep(3)  # Allow GPU memory to be released

        except KeyboardInterrupt:
            print("\n⛔ Interrupted by user")
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Ensure counters are always displayed, even on early exit
            print(f"\n🎯 Final Summary:")
            print(f"   📊 Total processed: {total_processed} videos")
            print(f"   ✅ Total successful: {total_successful} videos")
            if total_processed > 0:
                final_rate = (total_successful / total_processed) * 100
                print(f"   📈 Overall success rate: {final_rate:.1f}%")
            if total_successful < total_processed:
                print("   🚨 Some videos failed during processing")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Simple Instagram Video Processor")
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Number of videos per batch (default: 1000)"
    )
    parser.add_argument(
        "--max-workers", type=int, default=1, help="Number of parallel workers (default: 1)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.batch_size <= 0:
        print("❌ Batch size must be positive")
        sys.exit(1)
    if args.max_workers <= 0:
        print("❌ Max workers must be positive")
        sys.exit(1)

    # Check environment
    if not os.getenv("ORIANE_ADMIN_DB_URL"):
        print("❌ ORIANE_ADMIN_DB_URL environment variable is required")
        sys.exit(1)

    # Run processor
    processor = SimpleInstagramProcessor(batch_size=args.batch_size, max_workers=args.max_workers)
    processor.run()


if __name__ == "__main__":
    main()
