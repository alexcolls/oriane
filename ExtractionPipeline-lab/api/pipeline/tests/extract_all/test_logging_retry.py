#!/usr/bin/env python3
"""
Test script to validate the logging and retry implementation.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from logging_config import LoggingConfig
from retry_utils import api_retry, s3_operation_retry, qdrant_retry
from config import Config


@api_retry()
async def test_api_function():
    """Test API function with retry decorator."""
    logger = logging.getLogger(__name__)
    logger.info("Test API function called")
    return "API success"


@s3_operation_retry()
def test_s3_function():
    """Test S3 function with retry decorator."""
    logger = logging.getLogger(__name__)
    logger.info("Test S3 function called")
    return "S3 success"


@qdrant_retry()
async def test_qdrant_function():
    """Test Qdrant function with retry decorator."""
    logger = logging.getLogger(__name__)
    logger.info("Test Qdrant function called")
    return "Qdrant success"


async def main():
    """Main test function."""
    # Setup logging
    logging_config = LoggingConfig(log_level='INFO', log_dir='./test_logs')
    logger = logging.getLogger(__name__)
    
    logger.info("Starting logging and retry test")
    
    try:
        # Test API retry
        result = await test_api_function()
        logger.info(f"API function result: {result}")
        
        # Test S3 retry
        result = test_s3_function()
        logger.info(f"S3 function result: {result}")
        
        # Test Qdrant retry
        result = await test_qdrant_function()
        logger.info(f"Qdrant function result: {result}")
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    asyncio.run(main())
