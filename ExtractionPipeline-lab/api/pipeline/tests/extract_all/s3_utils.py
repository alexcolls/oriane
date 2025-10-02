#!/usr/bin/env python3
"""
S3 utilities for listing files and checking connectivity.
"""
import asyncio
import logging
import time
import random
import os
from typing import List, Optional, Set
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.client import Config
from botocore import UNSIGNED
from concurrent.futures import ThreadPoolExecutor
from config import settings
from retry_utils import s3_operation_retry


def _make_s3_client(aws_region="us-east-1"):
    """Create S3 client with environment credentials if available, otherwise use unsigned."""
    if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        return boto3.client(
            "s3",
            region_name=aws_region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        )
    return boto3.client("s3", region_name=aws_region, config=Config(signature_version=UNSIGNED))


class S3Utils:
    """S3 utilities for file listing and connectivity checks."""
    
    def __init__(self, config):
        """Initialize S3 client with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize boto3 client using helper
        self.s3_client = _make_s3_client(config.aws_region)
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def check_connection(self) -> bool:
        """Check S3 connectivity and bucket access."""
        try:
            self.logger.info(f"Checking S3 connection to bucket: {self.config.s3_bucket}")
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._check_bucket_access
            )
            
            self.logger.info("S3 connection successful")
            return True
            
        except NoCredentialsError:
            self.logger.error("AWS credentials not found")
            raise
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                self.logger.error(f"Bucket {self.config.s3_bucket} does not exist")
            elif error_code == 'AccessDenied':
                self.logger.error(f"Access denied to bucket {self.config.s3_bucket}")
            else:
                self.logger.error(f"S3 error: {error_code} - {e.response['Error']['Message']}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error checking S3 connection: {e}")
            raise
    
    def _check_bucket_access(self):
        """Synchronous bucket access check."""
        response = self.s3_client.head_bucket(Bucket=self.config.s3_bucket)
        return response
    
    async def list_files(self, file_types: Optional[List[str]] = None) -> List[str]:
        """
        List files in the S3 bucket with optional filtering by file types.
        
        Args:
            file_types: List of file extensions to filter by (e.g., ['.pdf', '.txt'])
        
        Returns:
            List of S3 object keys
        """
        if file_types is None:
            file_types = ['.pdf', '.txt', '.doc', '.docx']
        
        try:
            self.logger.info(f"Listing files from s3://{self.config.s3_bucket}/{self.config.s3_prefix}")
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            files = await loop.run_in_executor(
                self.executor,
                self._list_files_sync,
                file_types
            )
            
            self.logger.info(f"Found {len(files)} files")
            return files
            
        except Exception as e:
            self.logger.error(f"Error listing files: {e}")
            raise
    
    def _list_files_sync(self, file_types: List[str]) -> List[str]:
        """Synchronous file listing."""
        files = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        
        page_iterator = paginator.paginate(
            Bucket=self.config.s3_bucket,
            Prefix=self.config.s3_prefix
        )
        
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Filter by file type if specified
                    if file_types:
                        if any(key.lower().endswith(ext.lower()) for ext in file_types):
                            files.append(key)
                    else:
                        files.append(key)
        
        return files
    
    async def get_file_info(self, key: str) -> dict:
        """
        Get metadata for a specific S3 object.
        
        Args:
            key: S3 object key
        
        Returns:
            Dictionary with file metadata
        """
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._get_file_info_sync,
                key
            )
            
            return {
                'key': key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'],
                'content_type': response.get('ContentType', 'application/octet-stream')
            }
            
        except Exception as e:
            self.logger.error(f"Error getting file info for {key}: {e}")
            raise
    
    def _get_file_info_sync(self, key: str):
        """Synchronous file info retrieval."""
        return self.s3_client.head_object(Bucket=self.config.s3_bucket, Key=key)
    
    async def download_file(self, key: str, local_path: str) -> bool:
        """
        Download a file from S3 to local path.
        
        Args:
            key: S3 object key
            local_path: Local file path to save to
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Downloading {key} to {local_path}")
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._download_file_sync,
                key,
                local_path
            )
            
            self.logger.info(f"Successfully downloaded {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading {key}: {e}")
            return False
    
    def _download_file_sync(self, key: str, local_path: str):
        """Synchronous file download."""
        self.s3_client.download_file(
            self.config.s3_bucket,
            key,
            local_path
        )
    
    async def close(self):
        """Clean up resources."""
        self.executor.shutdown(wait=True)


def _exponential_backoff_retry(func, max_retries=5, base_delay=1.0, max_delay=60.0, jitter=True):
    """
    Retry function with exponential backoff for handling rate limits.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter to prevent thundering herd
    
    Returns:
        Result of function call
    
    Raises:
        Last exception if all retries fail
    """
    logger = logging.getLogger(__name__)
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            # Check if it's a rate limit error
            if error_code in ['Throttling', 'ThrottlingException', 'TooManyRequests', 'SlowDown']:
                if attempt < max_retries:
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Rate limit hit (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Rate limit exceeded after {max_retries + 1} attempts")
                    raise
            else:
                # Not a rate limit error, re-raise immediately
                raise
        except Exception as e:
            # For non-ClientError exceptions, only retry on the last few attempts
            if attempt < max_retries - 2:
                delay = min(base_delay * (2 ** attempt), max_delay)
                if jitter:
                    delay = delay * (0.5 + random.random() * 0.5)
                
                logger.warning(
                    f"Error occurred (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                time.sleep(delay)
                continue
            else:
                raise
    
    # This should never be reached, but just in case
    raise Exception("Max retries exceeded")


@s3_operation_retry()
def list_instagram_codes() -> Set[str]:
    """
    List Instagram codes from S3 bucket 'oriane-contents' with prefix 'instagram/'.
    
    Paginates through list_objects_v2 with delimiter '/' to get folder-like structure,
    then extracts the code parts from the CommonPrefixes.
    
    Returns:
        Set of Instagram codes extracted from S3 prefixes
    
    Raises:
        ClientError: If S3 operation fails
        NoCredentialsError: If AWS credentials are not available
    """
    logger = logging.getLogger(__name__)
    
    # Create S3 client using helper function
    s3_client = _make_s3_client(settings.get_aws_region())
    
    codes = set()
    
    def _list_objects_page(continuation_token=None):
        """List objects for a single page with optional continuation token."""
        kwargs = {
            'Bucket': 'oriane-contents',
            'Prefix': 'instagram/',
            'Delimiter': '/'
        }
        
        if continuation_token:
            kwargs['ContinuationToken'] = continuation_token
        
        return s3_client.list_objects_v2(**kwargs)
    
    try:
        logger.info("Listing Instagram codes from s3://oriane-contents/instagram/")
        
        # Paginate through all results
        continuation_token = None
        total_codes = 0
        
        while True:
            # Use exponential backoff retry for each page
            if continuation_token:
                response = _exponential_backoff_retry(
                    lambda: _list_objects_page(continuation_token)
                )
            else:
                response = _exponential_backoff_retry(
                    lambda: _list_objects_page()
                )
            
            # Extract codes from CommonPrefixes
            if 'CommonPrefixes' in response:
                for prefix_info in response['CommonPrefixes']:
                    prefix = prefix_info['Prefix']
                    
                    # Extract code from prefix like 'instagram/CODE/'
                    if prefix.startswith('instagram/') and prefix.endswith('/'):
                        code = prefix[len('instagram/'):-1]  # Remove 'instagram/' and trailing '/'
                        if code:  # Only add non-empty codes
                            codes.add(code)
                            total_codes += 1
            
            # Check if there are more pages
            if response.get('IsTruncated', False):
                continuation_token = response.get('NextContinuationToken')
                if not continuation_token:
                    break
            else:
                break
        
        logger.info(f"Found {total_codes} Instagram codes")
        return codes
        
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        raise
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            logger.error("Bucket 'oriane-contents' does not exist")
        elif error_code == 'AccessDenied':
            logger.error("Access denied to bucket 'oriane-contents'")
        else:
            logger.error(f"S3 error: {error_code} - {e.response['Error']['Message']}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing Instagram codes: {e}")
        raise
