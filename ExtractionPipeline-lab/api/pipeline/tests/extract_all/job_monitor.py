#!/usr/bin/env python3
"""
Job monitoring with async polling for job status.

Implements:
• Async task per job: poll /status every STATUS_INTERVAL until status in {COMPLETED, FAILED}.
• Write final JSON to responses/batch-<n>.json, update logs/batch-<n>.log.
• On failure, surface reason and optionally retry failed videos in next run.
"""
import asyncio
import logging
import json
import aiofiles
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class JobMonitor:
    """Async job monitoring with polling and timeout handling."""
    
    def __init__(self, config, api_client, state_manager):
        """Initialize job monitor with dependencies."""
        self.config = config
        self.api_client = api_client
        self.state_manager = state_manager
        self.logger = logging.getLogger(__name__)
        
        # Active jobs tracking
        self.active_jobs = {}
        
        # Batch index counter for file naming
        self.batch_counter = 0
        self.batch_lock = asyncio.Lock()
        
    async def monitor_job(self, job_id: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Monitor a job until completion or timeout.
        
        Args:
            job_id: Job ID to monitor
            timeout: Timeout in seconds (defaults to config timeout)
        
        Returns:
            Dictionary with final job status and result
        """
        if timeout is None:
            timeout = self.config.timeout
            
        self.logger.info(f"Starting monitoring for job: {job_id} (timeout: {timeout}s)")
        
        start_time = datetime.utcnow()
        timeout_time = start_time + timedelta(seconds=timeout)
        
        # Get unique batch index
        async with self.batch_lock:
            batch_index = self.batch_counter
            self.batch_counter += 1
            
        responses_dir = Path(self.config.responses_dir)
        logs_dir = Path(self.config.logs_dir)
        responses_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        response_path = responses_dir / f"batch-{batch_index}.json"
        log_path = logs_dir / f"batch-{batch_index}.log"

        # Track job in active jobs
        self.active_jobs[job_id] = {
            'start_time': start_time,
            'timeout_time': timeout_time,
            'status': JobStatus.PENDING,
            'last_check': start_time
        }
        
        try:
            while datetime.utcnow() < timeout_time:
                try:
                    # Check job status
                    status_response = await self.api_client.get_job_status(job_id)
                    current_status = self._parse_status(status_response.get('status', 'unknown'))
                    
                    # Update tracking
                    self.active_jobs[job_id]['status'] = current_status
                    self.active_jobs[job_id]['last_check'] = datetime.utcnow()
                    
                    self.logger.debug(f"Job {job_id} status: {current_status.value}")
                    
                    # Check if job is complete
                    if current_status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                        self.logger.info(f"Job {job_id} finished with status: {current_status.value}")
                        
                        # Get final result if completed successfully
                        result = status_response
                        if current_status == JobStatus.COMPLETED:
                            try:
                                result = await self.api_client.get_job_result(job_id)
                            except Exception as e:
                                self.logger.warning(f"Could not get result for job {job_id}: {e}")
                        
                        # Write results to files
                        await self._write_job_result(job_id, result, response_path, log_path, start_time)

                        # Clean up tracking
                        del self.active_jobs[job_id]
                        
                        return {
                            'job_id': job_id,
                            'status': current_status.value,
                            'result': result,
                            'duration': (datetime.utcnow() - start_time).total_seconds()
                        }
                    
                    # Wait before next check
                    await asyncio.sleep(self.config.interval)
                    
                except Exception as e:
                    self.logger.error(f"Error checking status for job {job_id}: {e}")
                    await asyncio.sleep(self.config.interval)
                    
            # Timeout reached
            self.logger.error(f"Job {job_id} timed out after {timeout} seconds")
            
            # Write timeout result
            timeout_result = {'job_id': job_id, 'status': 'timeout', 'error': f'Job timed out after {timeout} seconds'}
            await self._write_job_result(job_id, timeout_result, response_path, log_path, start_time, is_timeout=True)

            # Try to cancel the job
            try:
                await self.api_client.cancel_job(job_id)
            except Exception as e:
                self.logger.warning(f"Failed to cancel timed out job {job_id}: {e}")
            
            # Clean up tracking
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
                
            return {
                'job_id': job_id,
                'status': 'timeout',
                'error': f'Job timed out after {timeout} seconds',
                'duration': timeout
            }
            
        except Exception as e:
            self.logger.error(f"Unexpected error monitoring job {job_id}: {e}")
            
            # Write error result
            error_result = {'job_id': job_id, 'status': 'error', 'error': str(e)}
            await self._write_job_result(job_id, error_result, response_path, log_path, start_time, is_error=True)

            # Clean up tracking
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
                
            return {
                'job_id': job_id,
                'status': 'error',
                'error': str(e),
                'duration': (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def monitor_multiple_jobs(self, job_ids: list, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Monitor multiple jobs concurrently.
        
        Args:
            job_ids: List of job IDs to monitor
            timeout: Timeout in seconds for each job
        
        Returns:
            Dictionary mapping job IDs to their results
        """
        self.logger.info(f"Starting monitoring for {len(job_ids)} jobs")
        
        # Create monitoring tasks
        tasks = []
        for job_id in job_ids:
            task = asyncio.create_task(self.monitor_job(job_id, timeout))
            tasks.append(task)
        
        # Wait for all jobs to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        job_results = {}
        for i, result in enumerate(results):
            job_id = job_ids[i]
            if isinstance(result, Exception):
                job_results[job_id] = {
                    'job_id': job_id,
                    'status': 'error',
                    'error': str(result)
                }
            else:
                job_results[job_id] = result
        
        return job_results
    
    def _parse_status(self, status_str: str) -> JobStatus:
        """Parse status string to JobStatus enum."""
        status_mapping = {
            'pending': JobStatus.PENDING,
            'running': JobStatus.RUNNING,
            'processing': JobStatus.RUNNING,
            'completed': JobStatus.COMPLETED,
            'success': JobStatus.COMPLETED,
            'failed': JobStatus.FAILED,
            'error': JobStatus.FAILED,
            'cancelled': JobStatus.CANCELLED,
            'canceled': JobStatus.CANCELLED,
        }
        
        return status_mapping.get(status_str.lower(), JobStatus.UNKNOWN)
    
    async def get_active_jobs(self) -> Dict[str, Any]:
        """Get information about currently active jobs."""
        active_info = {}
        current_time = datetime.utcnow()
        
        for job_id, job_info in self.active_jobs.items():
            elapsed = (current_time - job_info['start_time']).total_seconds()
            remaining = (job_info['timeout_time'] - current_time).total_seconds()
            
            active_info[job_id] = {
                'status': job_info['status'].value,
                'elapsed_seconds': elapsed,
                'remaining_seconds': max(0, remaining),
                'last_check': job_info['last_check'].isoformat()
            }
        
        return active_info
    
    async def cancel_all_jobs(self) -> Dict[str, bool]:
        """Cancel all active jobs."""
        self.logger.info(f"Canceling {len(self.active_jobs)} active jobs")
        
        results = {}
        for job_id in list(self.active_jobs.keys()):
            try:
                success = await self.api_client.cancel_job(job_id)
                results[job_id] = success
                
                if success:
                    self.logger.info(f"Successfully canceled job: {job_id}")
                    # Remove from active jobs
                    if job_id in self.active_jobs:
                        del self.active_jobs[job_id]
                else:
                    self.logger.warning(f"Failed to cancel job: {job_id}")
                    
            except Exception as e:
                self.logger.error(f"Error canceling job {job_id}: {e}")
                results[job_id] = False
        
        return results
    
    async def wait_for_completion(self, max_wait_time: int = 300) -> bool:
        """
        Wait for all active jobs to complete.
        
        Args:
            max_wait_time: Maximum time to wait in seconds
        
        Returns:
            True if all jobs completed, False if timeout
        """
        start_time = datetime.utcnow()
        timeout_time = start_time + timedelta(seconds=max_wait_time)
        
        self.logger.info(f"Waiting for {len(self.active_jobs)} jobs to complete (max wait: {max_wait_time}s)")
        
        while self.active_jobs and datetime.utcnow() < timeout_time:
            await asyncio.sleep(1)
            
        if self.active_jobs:
            self.logger.warning(f"Timeout waiting for jobs to complete. {len(self.active_jobs)} jobs still active")
            return False
        else:
            self.logger.info("All jobs completed successfully")
            return True
    
    async def get_job_statistics(self) -> Dict[str, Any]:
        """Get statistics about job monitoring."""
        current_time = datetime.utcnow()
        
        stats = {
            'active_jobs_count': len(self.active_jobs),
            'active_jobs': [],
            'monitoring_config': {
                'polling_interval': self.config.interval,
                'default_timeout': self.config.timeout
            }
        }
        
        for job_id, job_info in self.active_jobs.items():
            elapsed = (current_time - job_info['start_time']).total_seconds()
            stats['active_jobs'].append({
                'job_id': job_id,
                'status': job_info['status'].value,
                'elapsed_seconds': elapsed,
                'start_time': job_info['start_time'].isoformat()
            })
        
        return stats
    
    async def _write_job_result(self, job_id: str, result: Dict[str, Any], response_path: Path, log_path: Path, start_time: datetime, is_timeout: bool = False, is_error: bool = False) -> None:
        """
        Write job result to response and log files.
        
        Args:
            job_id: Job ID
            result: Job result data
            response_path: Path to response file
            log_path: Path to log file
            start_time: Job start time
            is_timeout: Whether this is a timeout result
            is_error: Whether this is an error result
        """
        try:
            # Write response file
            async with aiofiles.open(response_path, 'w') as response_file:
                await response_file.write(json.dumps(result, indent=2))
            
            # Write log entry
            duration = (datetime.utcnow() - start_time).total_seconds()
            async with aiofiles.open(log_path, 'a') as log_file:
                if is_timeout:
                    await log_file.write(f"Job {job_id} timed out after {duration:.2f}s\n")
                elif is_error:
                    await log_file.write(f"Job {job_id} failed with error after {duration:.2f}s\n")
                else:
                    await log_file.write(f"Job {job_id} completed in {duration:.2f}s\n")
                await log_file.write(json.dumps(result, indent=2) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error writing job result for {job_id}: {e}")
    
    async def process_batch_with_retry(self, job_ids: List[str], max_retries: int = 3, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a batch of jobs with retry logic for failed jobs.
        
        Args:
            job_ids: List of job IDs to process
            max_retries: Maximum number of retry attempts for failed jobs
            timeout: Timeout in seconds for each job
            
        Returns:
            Dictionary with batch processing results including retry information
        """
        self.logger.info(f"Processing batch of {len(job_ids)} jobs with up to {max_retries} retries")
        
        all_results = {}
        failed_jobs = []
        retry_count = 0
        
        jobs_to_process = job_ids.copy()
        
        while jobs_to_process and retry_count <= max_retries:
            self.logger.info(f"Attempt {retry_count + 1}: Processing {len(jobs_to_process)} jobs")
            
            # Process current batch
            batch_results = await self.monitor_multiple_jobs(jobs_to_process, timeout)
            
            # Update results and identify failed jobs
            successful_jobs = []
            current_failed_jobs = []
            
            for job_id, result in batch_results.items():
                all_results[job_id] = result
                
                if result.get('status') in ['failed', 'error', 'timeout']:
                    current_failed_jobs.append(job_id)
                    
                    # Mark as failed in state manager
                    try:
                        await self.state_manager.mark_failed(
                            job_id, 
                            job_id, 
                            result.get('error', 'Unknown error'), 
                            retry_count
                        )
                    except Exception as e:
                        self.logger.warning(f"Could not mark job {job_id} as failed: {e}")
                else:
                    successful_jobs.append(job_id)
                    
                    # Mark as processed in state manager
                    try:
                        await self.state_manager.mark_processed(
                            job_id, 
                            job_id, 
                            result.get('result')
                        )
                    except Exception as e:
                        self.logger.warning(f"Could not mark job {job_id} as processed: {e}")
            
            self.logger.info(f"Attempt {retry_count + 1} completed: {len(successful_jobs)} successful, {len(current_failed_jobs)} failed")
            
            # Prepare for next retry if needed
            if current_failed_jobs and retry_count < max_retries:
                jobs_to_process = current_failed_jobs
                failed_jobs.extend(current_failed_jobs)
                retry_count += 1
                
                # Wait before retry
                await asyncio.sleep(min(2 ** retry_count, 30))  # Exponential backoff, max 30s
            else:
                break
        
        # Final summary
        total_successful = len([r for r in all_results.values() if r.get('status') not in ['failed', 'error', 'timeout']])
        total_failed = len(job_ids) - total_successful
        
        batch_summary = {
            'total_jobs': len(job_ids),
            'successful': total_successful,
            'failed': total_failed,
            'retry_attempts': retry_count,
            'results': all_results,
            'failed_jobs': list(set(failed_jobs)),
            'success_rate': (total_successful / len(job_ids)) * 100 if job_ids else 0
        }
        
        self.logger.info(f"Batch processing complete: {total_successful}/{len(job_ids)} successful ({batch_summary['success_rate']:.1f}%)")
        
        return batch_summary
    
    async def get_failed_jobs_for_retry(self) -> List[str]:
        """
        Get list of failed jobs that can be retried in the next run.
        
        Returns:
            List of job IDs that failed and can be retried
        """
        try:
            failed_files = await self.state_manager.get_failed_files()
            retry_candidates = []
            
            for file_key in failed_files:
                file_status = await self.state_manager.get_file_status(file_key)
                if file_status and file_status.get('retry_count', 0) < 3:  # Max 3 retries
                    retry_candidates.append(file_key)
            
            self.logger.info(f"Found {len(retry_candidates)} jobs eligible for retry")
            return retry_candidates
            
        except Exception as e:
            self.logger.error(f"Error getting failed jobs for retry: {e}")
            return []
    
    async def run_all(self, active_jobs: Dict[str, str]) -> Dict[str, Any]:
        """
        Monitor all active jobs concurrently until completion.
        
        Args:
            active_jobs: Dictionary mapping job names to job IDs
        
        Returns:
            Dictionary with results for all jobs
        """
        self.logger.info(f"Starting monitoring for {len(active_jobs)} active jobs")
        
        # Create monitoring tasks for all jobs
        tasks = []
        job_mapping = {}  # Map task to job name
        
        for job_name, job_id in active_jobs.items():
            task = asyncio.create_task(self.monitor_job(job_id))
            tasks.append(task)
            job_mapping[task] = job_name
        
        # Wait for all jobs to complete
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            job_results = {}
            for i, result in enumerate(results):
                task = tasks[i]
                job_name = job_mapping[task]
                
                if isinstance(result, Exception):
                    job_results[job_name] = {
                        'job_id': active_jobs[job_name],
                        'status': 'error',
                        'error': str(result)
                    }
                else:
                    job_results[job_name] = result
            
            # Calculate summary statistics
            total_jobs = len(active_jobs)
            successful_jobs = len([r for r in job_results.values() if r.get('status') == 'completed'])
            failed_jobs = total_jobs - successful_jobs
            
            self.logger.info(f"All jobs completed: {successful_jobs}/{total_jobs} successful, {failed_jobs} failed")
            
            return {
                'total_jobs': total_jobs,
                'successful': successful_jobs,
                'failed': failed_jobs,
                'results': job_results,
                'success_rate': (successful_jobs / total_jobs) * 100 if total_jobs > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error in run_all: {e}")
            return {
                'total_jobs': len(active_jobs),
                'successful': 0,
                'failed': len(active_jobs),
                'results': {},
                'error': str(e)
            }
