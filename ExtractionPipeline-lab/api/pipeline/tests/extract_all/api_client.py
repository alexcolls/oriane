#!/usr/bin/env python3
"""
API client for pipeline API using httpx.AsyncClient.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
import httpx
from config import settings
from retry_utils import api_retry


class APIClient:
    """API client for pipeline API with httpx.AsyncClient."""
    
    def __init__(self, config_or_timeout: Union[object, int] = None, max_retries: int = 3):
        """Initialize API client with configuration.
        
        Args:
            config_or_timeout: Either a Config object (for backward compatibility) or timeout int
            max_retries: Maximum number of retry attempts
        """
        self.logger = logging.getLogger(__name__)
        self.max_retries = max_retries
        
        # Handle backward compatibility with config object
        if config_or_timeout is None:
            self.timeout = 30
            self.config = None
        elif isinstance(config_or_timeout, int):
            self.timeout = config_or_timeout
            self.config = None
        else:
            # Assume it's a config object
            self.config = config_or_timeout
            self.timeout = getattr(config_or_timeout, 'timeout', 30)
        
        # Prepare headers for API requests
        self.headers = {'Content-Type': 'application/json'}
        if settings.get_api_key():
            self.headers['x-api-key'] = settings.get_api_key()
        
        # Initialize httpx client with base URL
        self.base_url = settings.get_pipeline_api_url()
        if not self.base_url:
            raise ValueError("PIPELINE_API_URL must be set in environment")
    
    @api_retry()
    async def submit_batch(self, items: List[Dict]) -> str:
        """
        Submit a batch of items for processing.
        
        Args:
            items: List of dictionaries containing items to process
        
        Returns:
            Job ID string
        """
        payload = {"items": items}
        
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await self._make_request_with_retry(
                    client.post, "/batch", 
                    json=payload, 
                    headers=self.headers
                )
                
                response_data = response.json()
                job_id = response_data.get('job_id')
                
                if not job_id:
                    raise Exception("No job_id returned from batch submission")
                
                self.logger.info(f"Batch submitted successfully: {job_id}")
                return job_id
        except Exception as e:
            self.logger.error(f"Error submitting batch: {e}")
            raise
    
    @api_retry()
    async def get_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a job.
        
        Args:
            job_id: Job ID to check status for
        
        Returns:
            Dictionary with parsed JobStatusResponse
        """
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await self._make_request_with_retry(
                    client.get, f"/status/{job_id}", 
                    headers=self.headers
                )
                
                response_data = response.json()
                self.logger.debug(f"Status for job {job_id}: {response_data.get('status')}")
                
                return response_data
        except Exception as e:
            self.logger.error(f"Error getting status for job {job_id}: {e}")
            raise
    
    async def _make_request_with_retry(self, request_func, *args, **kwargs):
        """
        Make HTTP request with retry logic for 5xx errors and timeouts.
        
        Args:
            request_func: The httpx request function to call
            *args: Positional arguments for the request
            **kwargs: Keyword arguments for the request
        
        Returns:
            httpx.Response object
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await request_func(*args, **kwargs)
                
                # Check if we got a 5xx error
                if response.status_code >= 500:
                    if attempt < self.max_retries:
                        self.logger.warning(
                            f"Server error {response.status_code} on attempt {attempt + 1}, retrying..."
                        )
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        response.raise_for_status()
                
                # Check for successful response
                response.raise_for_status()
                return response
                
            except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                last_exception = e
                if attempt < self.max_retries:
                    self.logger.warning(
                        f"Timeout on attempt {attempt + 1}, retrying..."
                    )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise
            
            except httpx.HTTPStatusError as e:
                # Don't retry on 4xx errors
                if 400 <= e.response.status_code < 500:
                    raise
                last_exception = e
                if attempt < self.max_retries:
                    self.logger.warning(
                        f"HTTP error {e.response.status_code} on attempt {attempt + 1}, retrying..."
                    )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise
            
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    self.logger.warning(
                        f"Error on attempt {attempt + 1}: {e}, retrying..."
                    )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise
        
        # If we get here, all retries failed
        raise last_exception or Exception("All retry attempts failed")
    
    # Backward compatibility methods
    async def submit_job(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a single file for processing (backward compatibility).
        
        Args:
            file_path: File path to process
            metadata: Optional metadata
        
        Returns:
            Job ID string
        """
        item = {"file_path": file_path}
        if metadata:
            item["metadata"] = metadata
        
        return await self.submit_batch([item])
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status (backward compatibility alias).
        
        Args:
            job_id: Job ID to check
        
        Returns:
            Job status dictionary
        """
        return await self.get_status(job_id)
    
    async def get_job_result(self, job_id: str) -> Dict[str, Any]:
        """
        Get job result (backward compatibility).
        
        Args:
            job_id: Job ID to get result for
        
        Returns:
            Job result dictionary
        """
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await self._make_request_with_retry(
                client.get, f"/result/{job_id}", 
                headers=self.headers
            )
            
            response_data = response.json()
            self.logger.debug(f"Result for job {job_id}: {response_data}")
            
            return response_data
    @api_retry()
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job (backward compatibility).
        
        Args:
            job_id: Job ID to cancel
        
        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await self._make_request_with_retry(
                    client.post, f"/cancel/{job_id}", 
                    headers=self.headers
                )
                
                self.logger.info(f"Job {job_id} canceled successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error canceling job {job_id}: {e}")
            return False
