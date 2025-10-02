"""
This program is used to extract the OrianeAdmin DB insta_content table, where is_extracted = False,
and proceed with the video extraction pipeline. With the first step the cropping and scene framing, and then
on success update is_extracted = True. And second step is the video frames embedding extraction and after
successfull storage in the Qdrant DB watched_frames collection then update is_embedded = True from the insta_content table.
The table can contain millions of rows, so we need to process them in batches of 1000 rows.
It must use the core/py/pipeline/*.py scripts to process the video extraction pipeline with the same parameters as the
core/py/pipeline/.env and it uses the virtual environment from the core/py/pipeline/.venv.
The program is able to handle errors and continue from the last processed row.
"""

import json
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from checkpoint_manager import CheckpointManager
from db import mark_embedded, mark_extracted, next_batch
from models import InstaContent

CORE_VENV_PY = "/home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline/.venv/bin/python"


class ExtractionPipeline:
    """
    Main extraction pipeline with checkpoint/resume capability.
    """

    def __init__(
        self, batch_size: int = 1000, use_json_checkpoint: bool = True, max_workers: int = 4
    ):
        """
        Initialize the extraction pipeline.

        Args:
            batch_size: Number of records to process per batch
            use_json_checkpoint: Whether to use JSON file for checkpoints (default: True)
            max_workers: Number of parallel workers for video processing (default: 4)
        """
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.checkpoint_manager = CheckpointManager(use_json=use_json_checkpoint)
        self.should_stop = False

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals (Ctrl+C, etc.).
        """
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.should_stop = True

    def run(self):
        """
        Run the extraction pipeline with checkpoint/resume capability.
        """
        print("Starting extraction pipeline...")

        # Get the last processed ID from checkpoint
        last_processed_id = self.checkpoint_manager.get_checkpoint()
        if last_processed_id:
            print(f"Resuming from checkpoint: last processed ID = {last_processed_id}")
        else:
            print("Starting from the beginning (no checkpoint found)")

        total_processed = 0

        try:
            while not self.should_stop:
                # Get next batch of records to process
                batch = next_batch(size=self.batch_size, last_id=last_processed_id)

                if not batch:
                    print("No more records to process. Extraction complete.")
                    break

                print(
                    f"Processing batch of {len(batch)} records (IDs: {batch[0]['id']} - {batch[-1]['id']})"
                )

                # Process the batch in parallel
                successful_extractions = []
                successful_embeddings = []

                # Separate records that need extraction vs embedding
                extraction_records = [r for r in batch if not r["is_extracted"]]
                embedding_records = [r for r in batch if r["is_extracted"] and not r["is_embedded"]]

                # Process video extractions in parallel
                if extraction_records:
                    print(
                        f"  Processing {len(extraction_records)} video extractions in parallel..."
                    )
                    extraction_results = self._process_batch_parallel(
                        extraction_records, self._process_video_extraction, "video extraction"
                    )
                    successful_extractions.extend(extraction_results)

                # Process embeddings in parallel
                if embedding_records:
                    print(f"  Processing {len(embedding_records)} frame embeddings in parallel...")
                    embedding_results = self._process_batch_parallel(
                        embedding_records, self._process_frame_embedding, "frame embedding"
                    )
                    successful_embeddings.extend(embedding_results)

                # Update database with successful extractions
                if successful_extractions:
                    mark_extracted(successful_extractions)
                    print(f"Marked {len(successful_extractions)} records as extracted")

                if successful_embeddings:
                    mark_embedded(successful_embeddings)
                    print(f"Marked {len(successful_embeddings)} records as embedded")

                # Update checkpoint with the last processed ID in this batch
                if batch:
                    last_processed_id = batch[-1]["id"]
                    self.checkpoint_manager.update_checkpoint(last_processed_id)
                    total_processed += len(batch)
                    print(f"Updated checkpoint: last processed ID = {last_processed_id}")
                    print(f"Total records processed so far: {total_processed}")

                # Small delay to prevent overwhelming the system
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nReceived keyboard interrupt. Shutting down gracefully...")
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
        finally:
            print(f"Pipeline stopped. Total records processed: {total_processed}")
            if last_processed_id:
                print(f"Last processed ID: {last_processed_id}")
            print("Run the program again to resume from where it left off.")

    def _process_batch_parallel(
        self, records: List[dict], processor_func, process_type: str
    ) -> List[str]:
        """
        Process a batch of records in parallel.

        Args:
            records: List of records to process
            processor_func: Function to process each record
            process_type: Description of the process for logging

        Returns:
            List of successful record IDs
        """
        successful_ids = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_record = {
                executor.submit(processor_func, record): record for record in records
            }

            # Collect results as they complete
            for future in as_completed(future_to_record):
                record = future_to_record[future]
                try:
                    if future.result():  # If processing was successful
                        successful_ids.append(record["id"])
                except Exception as e:
                    print(f"  Error in {process_type} for record {record['id']}: {e}")

                # Check for shutdown signal
                if self.should_stop:
                    print("Stopping parallel processing due to shutdown signal...")
                    # Cancel remaining futures
                    for f in future_to_record:
                        f.cancel()
                    break

        return successful_ids

    def _process_video_extraction(self, record: dict) -> bool:
        """
        Process video extraction for a single record.

        Args:
            record: Dictionary containing InstaContent record data

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"  Processing video extraction for record {record['id']}")

            # Prepare job input for the core pipeline
            job_input = json.dumps(
                [
                    {
                        "platform": "instagram",  # All records are Instagram content
                        "code": record["code"],
                    }
                ]
            )

            # Set up environment for the subprocess
            env = os.environ.copy()
            env["JOB_INPUT"] = job_input
            env["VIRTUAL_ENV"] = str(Path(CORE_VENV_PY).parent.parent)

            # Sanity check for missing interpreter
            if not Path(CORE_VENV_PY).exists():
                raise FileNotFoundError(f"Core venv python not found at {CORE_VENV_PY}")

            # Execute the core pipeline in its virtual environment
            result = subprocess.run(
                [
                    CORE_VENV_PY,
                    "/home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline/entrypoint.py",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
            )

            if result.returncode == 0:
                print(f"  ✅ Video extraction successful for record {record['id']}")
                return True
            else:
                print(f"  ❌ Video extraction failed for record {record['id']}")
                print(f"  Error output: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"  ⏰ Video extraction timed out for record {record['id']}")
            return False
        except Exception as e:
            print(f"  Error in video extraction for record {record['id']}: {e}")
            return False

    def _process_frame_embedding(self, record: dict) -> bool:
        """
        Process frame embedding extraction for a single record.

        Args:
            record: Dictionary containing InstaContent record data

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"  Processing frame embedding for record {record['id']}")

            # Set up environment for the subprocess
            env = os.environ.copy()
            env["VIRTUAL_ENV"] = str(Path(CORE_VENV_PY).parent.parent)

            # Sanity check for missing interpreter
            if not Path(CORE_VENV_PY).exists():
                raise FileNotFoundError(f"Core venv python not found at {CORE_VENV_PY}")

            # Execute the embedding pipeline in its virtual environment
            result = subprocess.run(
                [
                    CORE_VENV_PY,
                    "/home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline/embed_entrypoint.py",
                    record["code"],  # Pass the video code as argument
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=1200,  # 20 minutes timeout (embedding can take longer)
            )

            if result.returncode == 0:
                print(f"  ✅ Frame embedding successful for record {record['id']}")
                return True
            else:
                print(f"  ❌ Frame embedding failed for record {record['id']}")
                print(f"  Error output: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"  ⏰ Frame embedding timed out for record {record['id']}")
            return False
        except Exception as e:
            print(f"  Error in frame embedding for record {record['id']}: {e}")
            return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Oriane Video Extraction Pipeline")
    parser.add_argument("--batch-size", type=int, default=1000, help="Number of records per batch")
    parser.add_argument("--max-workers", type=int, default=8, help="Number of parallel workers")
    parser.add_argument(
        "--json-checkpoint", action="store_true", default=True, help="Use JSON checkpoints"
    )
    args = parser.parse_args()

    # Initialize and run the extraction pipeline with optimized settings
    pipeline = ExtractionPipeline(
        batch_size=args.batch_size,
        use_json_checkpoint=args.json_checkpoint,
        max_workers=args.max_workers,
    )
    pipeline.run()
