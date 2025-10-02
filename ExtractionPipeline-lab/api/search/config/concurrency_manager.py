"""
Concurrency Manager

This module provides concurrency control for the extraction pipeline including:
- Bounded ThreadPoolExecutor with configurable parallelism
- GPU memory protection via semaphore
- Job queue management for handling overflow
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable, Any, Awaitable
from contextlib import asynccontextmanager

from config.env_config import settings

# Configure logging
logger = logging.getLogger(__name__)


class ConcurrencyManager:
    """
    Manages concurrency for the extraction pipeline with bounded parallelism
    and GPU memory protection.
    """
    
    def __init__(self, max_parallel_jobs: Optional[int] = None):
        """
        Initialize the concurrency manager.
        
        Args:
            max_parallel_jobs: Maximum number of parallel jobs (default: from settings)
        """
        self.max_parallel_jobs = max_parallel_jobs or settings.pipeline_max_parallel_jobs
        self.executor = ThreadPoolExecutor(max_workers=self.max_parallel_jobs)
        
        # GPU memory protection semaphore
        # This limits the number of concurrent GPU operations
        self.gpu_semaphore = asyncio.Semaphore(self.max_parallel_jobs)
        
        # Job queue for managing overflow
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self._workers_running = False
        self._worker_tasks: list[asyncio.Task] = []
        
        logger.info(f"Initialized ConcurrencyManager with max_parallel_jobs={self.max_parallel_jobs}")
    
    async def start_workers(self):
        """Start worker tasks to process the job queue."""
        if self._workers_running:
            return
        
        self._workers_running = True
        
        # Start worker tasks equal to max_parallel_jobs
        for i in range(self.max_parallel_jobs):
            task = asyncio.create_task(self._worker_loop(worker_id=i))
            self._worker_tasks.append(task)
            
        logger.info(f"Started {self.max_parallel_jobs} worker tasks")
    
    async def stop_workers(self):
        """Stop all worker tasks."""
        if not self._workers_running:
            return
            
        self._workers_running = False
        
        # Cancel all worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete cancellation
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        self._worker_tasks.clear()
        logger.info("Stopped all worker tasks")
    
    async def _worker_loop(self, worker_id: int):
        """
        Worker loop that processes jobs from the queue.
        
        Args:
            worker_id: Unique identifier for this worker
        """
        logger.info(f"Worker {worker_id} started")
        
        try:
            while self._workers_running:
                try:
                    # Get job from queue with timeout
                    job_func, args, kwargs, result_future = await asyncio.wait_for(
                        self.job_queue.get(), timeout=1.0
                    )
                    
                    logger.info(f"Worker {worker_id} processing job")
                    
                    try:
                        # Execute the job with GPU semaphore protection
                        async with self.gpu_semaphore:
                            # Run the job function in the thread pool
                            loop = asyncio.get_running_loop()
                            result = await loop.run_in_executor(
                                self.executor, job_func, *args, **kwargs
                            )
                            result_future.set_result(result)
                    except Exception as e:
                        logger.error(f"Worker {worker_id} job failed: {e}")
                        result_future.set_exception(e)
                    finally:
                        self.job_queue.task_done()
                        
                except asyncio.TimeoutError:
                    # No job available, continue waiting
                    continue
                    
        except asyncio.CancelledError:
            logger.info(f"Worker {worker_id} cancelled")
        except Exception as e:
            logger.error(f"Worker {worker_id} encountered error: {e}")
        finally:
            logger.info(f"Worker {worker_id} stopped")
    
    async def submit_job(self, job_func: Callable, *args, **kwargs) -> Any:
        """
        Submit a job for processing.
        
        Args:
            job_func: Function to execute
            *args: Positional arguments for job_func
            **kwargs: Keyword arguments for job_func
            
        Returns:
            Result of job_func execution
        """
        # Create a future to track the job result
        result_future = asyncio.Future()
        
        # Add job to queue
        await self.job_queue.put((job_func, args, kwargs, result_future))
        
        logger.info(f"Job submitted to queue (queue size: {self.job_queue.qsize()})")
        
        # Wait for job completion
        return await result_future
    
    @asynccontextmanager
    async def gpu_memory_protection(self):
        """
        Context manager for GPU memory protection.
        
        Use this when performing GPU-intensive operations to ensure
        memory limits are respected.
        """
        async with self.gpu_semaphore:
            yield
    
    def get_queue_size(self) -> int:
        """Get the current size of the job queue."""
        return self.job_queue.qsize()
    
    def get_active_workers(self) -> int:
        """Get the number of active worker tasks."""
        return len([task for task in self._worker_tasks if not task.done()])
    
    def get_stats(self) -> dict:
        """Get concurrency manager statistics."""
        return {
            "max_parallel_jobs": self.max_parallel_jobs,
            "queue_size": self.get_queue_size(),
            "active_workers": self.get_active_workers(),
            "workers_running": self._workers_running,
            "gpu_semaphore_available": self.gpu_semaphore._value,
        }
    
    def __del__(self):
        """Cleanup resources when the manager is destroyed."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# Global concurrency manager instance
_concurrency_manager: Optional[ConcurrencyManager] = None


def get_concurrency_manager() -> ConcurrencyManager:
    """
    Get the global concurrency manager instance.
    
    Returns:
        ConcurrencyManager instance
    """
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = ConcurrencyManager()
    return _concurrency_manager


async def initialize_concurrency_manager():
    """Initialize and start the global concurrency manager."""
    manager = get_concurrency_manager()
    await manager.start_workers()
    logger.info("Concurrency manager initialized and workers started")


async def shutdown_concurrency_manager():
    """Shutdown the global concurrency manager."""
    global _concurrency_manager
    if _concurrency_manager is not None:
        await _concurrency_manager.stop_workers()
        _concurrency_manager = None
        logger.info("Concurrency manager shut down")
