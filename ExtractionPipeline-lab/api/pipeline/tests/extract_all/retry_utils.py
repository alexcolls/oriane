#!/usr/bin/env python3
"""
Retry decorators and utilities for network functions using tenacity.
"""
import logging
import functools
from typing import Callable, Any, Optional, Union
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
    before_sleep_log,
    after_log
)
import httpx
import aiohttp
import boto3
from botocore.exceptions import ClientError


def network_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: tuple = None,
    logger_name: str = None
):
    """
    Decorator for retrying network operations with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to wait times
        retry_on_exceptions: Tuple of exception types to retry on
        logger_name: Name of the logger to use
    
    Returns:
        Decorated function with retry logic
    """
    if retry_on_exceptions is None:
        retry_on_exceptions = (
            # HTTP exceptions
            httpx.TimeoutException,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
            httpx.NetworkError,
            httpx.RemoteProtocolError,
            # aiohttp exceptions
            aiohttp.ClientError,
            aiohttp.ClientTimeout,
            aiohttp.ClientConnectionError,
            aiohttp.ServerTimeoutError,
            # AWS exceptions
            ClientError,
            # Generic network exceptions
            ConnectionError,
            TimeoutError,
        )
    
    # Set up logger
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger(__name__)
    
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=min_wait,
                min=min_wait,
                max=max_wait,
                exp_base=exponential_base
            ),
            retry=retry_if_exception_type(retry_on_exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.DEBUG)
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def async_network_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on_exceptions: tuple = None,
    logger_name: str = None
):
    """
    Decorator for retrying async network operations with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to wait times
        retry_on_exceptions: Tuple of exception types to retry on
        logger_name: Name of the logger to use
    
    Returns:
        Decorated async function with retry logic
    """
    if retry_on_exceptions is None:
        retry_on_exceptions = (
            # HTTP exceptions
            httpx.TimeoutException,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.WriteTimeout,
            httpx.PoolTimeout,
            httpx.NetworkError,
            httpx.RemoteProtocolError,
            # aiohttp exceptions
            aiohttp.ClientError,
            aiohttp.ClientTimeout,
            aiohttp.ClientConnectionError,
            aiohttp.ServerTimeoutError,
            # Generic network exceptions
            ConnectionError,
            TimeoutError,
        )
    
    # Set up logger
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger(__name__)
    
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=min_wait,
                min=min_wait,
                max=max_wait,
                exp_base=exponential_base
            ),
            retry=retry_if_exception_type(retry_on_exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.DEBUG)
        )
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def s3_retry(
    max_attempts: int = 5,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    logger_name: str = None
):
    """
    Decorator specifically for S3 operations with retry logic for throttling.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        logger_name: Name of the logger to use
    
    Returns:
        Decorated function with S3-specific retry logic
    """
    # Set up logger
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger(__name__)
    
    def should_retry_s3_exception(exception):
        """Check if we should retry based on S3 exception type."""
        if isinstance(exception, ClientError):
            error_code = exception.response.get('Error', {}).get('Code', '')
            # Retry on throttling and temporary errors
            return error_code in [
                'Throttling',
                'ThrottlingException',
                'TooManyRequests',
                'SlowDown',
                'ServiceUnavailable',
                'InternalError',
                'RequestTimeout'
            ]
        return False
    
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=min_wait,
                min=min_wait,
                max=max_wait,
                exp_base=2.0
            ),
            retry=retry_if_exception_type((ClientError, ConnectionError, TimeoutError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.DEBUG)
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def http_status_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    retry_on_status: tuple = (500, 502, 503, 504, 429),
    logger_name: str = None
):
    """
    Decorator for retrying HTTP requests based on status codes.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        retry_on_status: Tuple of HTTP status codes to retry on
        logger_name: Name of the logger to use
    
    Returns:
        Decorated function with HTTP status-based retry logic
    """
    # Set up logger
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger(__name__)
    
    def should_retry_http_status(exception):
        """Check if we should retry based on HTTP status code."""
        if isinstance(exception, httpx.HTTPStatusError):
            return exception.response.status_code in retry_on_status
        return False
    
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=min_wait,
                min=min_wait,
                max=max_wait,
                exp_base=2.0
            ),
            retry=(
                retry_if_exception_type((
                    httpx.TimeoutException,
                    httpx.ConnectTimeout,
                    httpx.ReadTimeout,
                    httpx.NetworkError,
                    ConnectionError,
                    TimeoutError
                )) |
                retry_if_exception_type(httpx.HTTPStatusError) & 
                retry_if_result(should_retry_http_status)
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.DEBUG)
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def async_http_status_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    retry_on_status: tuple = (500, 502, 503, 504, 429),
    logger_name: str = None
):
    """
    Decorator for retrying async HTTP requests based on status codes.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        retry_on_status: Tuple of HTTP status codes to retry on
        logger_name: Name of the logger to use
    
    Returns:
        Decorated async function with HTTP status-based retry logic
    """
    # Set up logger
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger(__name__)
    
    def should_retry_http_status(exception):
        """Check if we should retry based on HTTP status code."""
        if isinstance(exception, httpx.HTTPStatusError):
            return exception.response.status_code in retry_on_status
        return False
    
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=min_wait,
                min=min_wait,
                max=max_wait,
                exp_base=2.0
            ),
            retry=(
                retry_if_exception_type((
                    httpx.TimeoutException,
                    httpx.ConnectTimeout,
                    httpx.ReadTimeout,
                    httpx.NetworkError,
                    aiohttp.ClientError,
                    aiohttp.ClientTimeout,
                    aiohttp.ClientConnectionError,
                    ConnectionError,
                    TimeoutError
                )) |
                retry_if_exception_type(httpx.HTTPStatusError) & 
                retry_if_result(should_retry_http_status)
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.DEBUG)
        )
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Convenience decorators with common configurations
api_retry = functools.partial(
    async_network_retry,
    max_attempts=3,
    min_wait=1.0,
    max_wait=30.0,
    logger_name='api_client'
)

s3_operation_retry = functools.partial(
    s3_retry,
    max_attempts=5,
    min_wait=1.0,
    max_wait=60.0,
    logger_name='s3_utils'
)

qdrant_retry = functools.partial(
    async_network_retry,
    max_attempts=3,
    min_wait=1.0,
    max_wait=30.0,
    logger_name='qdrant_utils'
)
