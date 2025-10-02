#!/usr/bin/env python3
"""
Main entrypoint for the extraction pipeline test suite.
"""
import asyncio
import argparse
import sys
import signal
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from config import Config
from s3_utils import S3Utils, list_instagram_codes
from qdrant_utils import QdrantUtils
from api_client import APIClient
from job_monitor import JobMonitor
from state import StateManager
from logging_config import LoggingConfig
from retry_utils import network_retry

# Global variables for graceful shutdown
shutdown_event = asyncio.Event()
active_jobs = {}
job_monitor = None
state_manager = None


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, initiating graceful shutdown...")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def dispatch_batch(batch_items: List[str], batch_number: int, api_client: APIClient, config: Config, active_jobs: Dict[str, str]) -> str:
    """Dispatch a batch of items for processing.
    
    Args:
        batch_items: List of video codes to process
        batch_number: Batch number for file naming
        api_client: API client instance
        config: Configuration instance
        active_jobs: Dictionary to track active jobs
        
    Returns:
        Job ID for the batch
    """
    logger = logging.getLogger(__name__)
    
    # Create batch request
    batch_request = {
        "batch_number": batch_number,
        "items": [{
            "video_code": code,
            "platform": "instagram",
            "timestamp": datetime.utcnow().isoformat()
        } for code in batch_items],
        "created_at": datetime.utcnow().isoformat(),
        "batch_size": len(batch_items)
    }
    
    # Create requests directory if it doesn't exist
    requests_dir = Path('./requests')
    requests_dir.mkdir(parents=True, exist_ok=True)
    
    # Save request JSON
    request_file = requests_dir / f"batch-{batch_number}.json"
    with open(request_file, 'w') as f:
        json.dump(batch_request, f, indent=2)
    
    logger.info(f"Saved batch request to {request_file}")
    
    # Submit batch to API
    job_id = await api_client.submit_batch(batch_request['items'])
    
    # Track the job
    active_jobs[f"batch-{batch_number}"] = job_id
    
    logger.info(f"Submitted batch {batch_number} with {len(batch_items)} items, job_id: {job_id}")
    
    return job_id


async def process_batches(config: Config, state_manager: StateManager, api_client: APIClient, qdrant_utils: QdrantUtils, job_monitor: JobMonitor) -> Dict[str, Any]:
    """Main batching logic implementation.
    
    Args:
        config: Configuration instance
        state_manager: State management instance
        api_client: API client instance
        qdrant_utils: Qdrant utilities instance
        job_monitor: Job monitor instance
        
    Returns:
        Dictionary with processing results
    """
    logger = logging.getLogger(__name__)
    
    # Step 1: Load state & list codes from S3
    logger.info("Loading state and listing video codes from S3...")
    await state_manager.load_state()
    
    # Get all Instagram codes from S3
    loop = asyncio.get_event_loop()
    all_codes = await loop.run_in_executor(None, list_instagram_codes)
    
    # Get processed codes from state
    processed_codes = await state_manager.get_processed_codes()
    
    logger.info(f"Found {len(all_codes)} total codes, {len(processed_codes)} already processed")
    
    # Step 2: For each code not in processed, check if extracted in Qdrant
    current_batch = []
    batch_number = 0
    batch_limit = config.batch_limit
    
    unprocessed_codes = [code for code in all_codes if code not in processed_codes]
    
    if config.limit:
        unprocessed_codes = unprocessed_codes[:config.limit]
    
    logger.info(f"Processing {len(unprocessed_codes)} unprocessed codes in batches of {batch_limit}")
    
    for code in unprocessed_codes:
        # Check for shutdown signal
        if shutdown_event.is_set():
            logger.info("Shutdown signal received, stopping processing")
            break
        
        # Check if video is already extracted in Qdrant
        try:
            is_extracted = await qdrant_utils.is_video_extracted(code)
            if not is_extracted:
                current_batch.append(code)
                logger.debug(f"Added {code} to current batch (size: {len(current_batch)})")
        except Exception as e:
            logger.warning(f"Error checking if video {code} is extracted: {e}, adding to batch anyway")
            current_batch.append(code)
        
        # Step 3: When batch is full, dispatch it
        if len(current_batch) >= batch_limit:
            try:
                await dispatch_batch(current_batch, batch_number, api_client, config, active_jobs)
                current_batch = []
                batch_number += 1
            except Exception as e:
                logger.error(f"Error dispatching batch {batch_number}: {e}")
                # Continue processing, but log the error
    
    # Step 4: Dispatch remainder if any
    if current_batch and not shutdown_event.is_set():
        try:
            await dispatch_batch(current_batch, batch_number, api_client, config, active_jobs)
            batch_number += 1  # Increment for final batch
        except Exception as e:
            logger.error(f"Error dispatching final batch {batch_number}: {e}")
    
    # Step 5: Await job_monitor.run_all(active_jobs)
    if active_jobs and not shutdown_event.is_set():
        logger.info(f"Monitoring {len(active_jobs)} active jobs...")
        monitoring_results = await job_monitor.run_all(active_jobs)
    else:
        monitoring_results = {'total_jobs': 0, 'successful': 0, 'failed': 0, 'results': {}}
    
    # Step 6: Update processed.json with successfully completed video codes
    successful_jobs = 0
    for job_name, result in monitoring_results.get('results', {}).items():
        if result.get('status') == 'completed':
            successful_jobs += 1
            # Extract the video codes from the batch and mark them as processed
            try:
                batch_num = int(job_name.split('-')[1])
                request_file = Path('./requests') / f"batch-{batch_num}.json"
                
                if request_file.exists():
                    with open(request_file, 'r') as f:
                        batch_data = json.load(f)
                    
                    for item in batch_data.get('items', []):
                        video_code = item.get('video_code')
                        if video_code:
                            await state_manager.mark_processed(
                                video_code, 
                                result.get('job_id'), 
                                result.get('result')
                            )
                            logger.debug(f"Marked {video_code} as processed")
                            
            except Exception as e:
                logger.error(f"Error processing successful job {job_name}: {e}")
    
    logger.info(f"Processing complete: {successful_jobs} successful batches out of {len(active_jobs)}")
    
    return {
        'total_codes': len(all_codes),
        'processed_codes': len(processed_codes),
        'unprocessed_codes': len(unprocessed_codes),
        'batches_created': batch_number,
        'monitoring_results': monitoring_results,
        'successful_batches': successful_jobs,
        'shutdown_requested': shutdown_event.is_set()
    }


async def graceful_shutdown():
    """Handle graceful shutdown: cancel monitors, persist state."""
    logger = logging.getLogger(__name__)
    
    logger.info("Starting graceful shutdown...")
    
    # Cancel any active job monitors
    if job_monitor and active_jobs:
        logger.info(f"Canceling {len(active_jobs)} active job monitors...")
        try:
            cancel_results = await job_monitor.cancel_all_jobs()
            logger.info(f"Canceled {sum(cancel_results.values())} jobs")
        except Exception as e:
            logger.error(f"Error canceling jobs during shutdown: {e}")
    
    # Persist final state
    if state_manager:
        logger.info("Persisting final state...")
        try:
            await state_manager.save_state()
            logger.info("State saved successfully")
        except Exception as e:
            logger.error(f"Error saving state during shutdown: {e}")
    
    logger.info("Graceful shutdown complete")


async def main():
    """Main async entrypoint."""
    global job_monitor, state_manager
    
    # Setup signal handlers
    setup_signal_handlers()
    
    parser = argparse.ArgumentParser(description='Extract all pipeline test runner')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--interval', type=int, help='Polling interval in seconds')
    parser.add_argument('--timeout', type=int, help='Timeout in seconds')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       help='Logging level')
    parser.add_argument('--env-file', help='Path to .env file')
    
    args = parser.parse_args()
    
    # Setup centralized logging
    log_level = args.log_level or 'INFO'
    logging_config = LoggingConfig(log_level=log_level, log_dir=config.logs_dir if 'config' in locals() else './logs')
    
    logger = logging.getLogger(__name__)
    logger.info("Starting extraction pipeline...")
    
    # Load configuration
    config = Config(
        env_file=args.env_file,
        limit=args.limit,
        interval=args.interval,
        timeout=args.timeout,
        log_level=args.log_level
    )
    
    # Update logging configuration with config paths
    logging_config = LoggingConfig(log_level=log_level, log_dir=config.logs_dir)
    
    # Initialize components
    s3_utils = S3Utils(config)
    qdrant_utils = QdrantUtils(config)
    api_client = APIClient(config.timeout)
    state_manager = StateManager(config)
    job_monitor = JobMonitor(config, api_client, state_manager)
    
    try:
        # Check prerequisites (optional)
        try:
            await qdrant_utils.check_connection()
            logger.info("Qdrant connection successful")
        except Exception as e:
            logger.warning(f"Qdrant connection check failed: {e}")
        
        # Reset state if not resuming
        if not args.resume:
            try:
                await state_manager.reset_state()
                logger.info("State reset completed")
            except Exception as e:
                logger.error(f"Error resetting state: {e}")
                raise
        
        # Run the main batching logic
        results = await process_batches(config, state_manager, api_client, qdrant_utils, job_monitor)
        
        # Print final results
        print("\n=== Processing Results ===")
        print(f"Total codes found: {results['total_codes']}")
        print(f"Already processed: {results['processed_codes']}")
        print(f"Unprocessed codes: {results['unprocessed_codes']}")
        print(f"Batches created: {results['batches_created']}")
        print(f"Successful batches: {results['successful_batches']}")
        
        if results['shutdown_requested']:
            print("\n⚠️  Processing interrupted by shutdown signal")
        else:
            print("\n✅ Processing completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\nInterrupted by user")
        shutdown_event.set()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        shutdown_event.set()
    finally:
        # Always attempt graceful shutdown and save state
        try:
            await graceful_shutdown()
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
        
        # Ensure state is saved in finally block
        if state_manager:
            try:
                await state_manager.save_state()
                logger.info("Final state save completed")
            except Exception as e:
                logger.error(f"Error saving final state: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())
