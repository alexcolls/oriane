#!/usr/bin/env python3
"""
Simple test script to verify main.py implementation.
"""
import asyncio
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from s3_utils import list_instagram_codes
from qdrant_utils import QdrantUtils
from api_client import APIClient
from job_monitor import JobMonitor
from state import StateManager

async def test_components():
    """Test if all components can be initialized and basic functionality works."""
    try:
        # Test configuration
        config = Config(limit=10)
        print(f"✓ Config loaded: batch_limit={config.batch_limit}")
        
        # Test S3 Instagram codes listing
        print("Testing S3 Instagram codes listing...")
        try:
            loop = asyncio.get_event_loop()
            codes = await loop.run_in_executor(None, list_instagram_codes)
            print(f"✓ Found {len(codes)} Instagram codes")
        except Exception as e:
            print(f"⚠ S3 listing failed: {e}")
        
        # Test Qdrant utils
        qdrant_utils = QdrantUtils(config)
        print("✓ QdrantUtils initialized")
        
        # Test API client
        api_client = APIClient(config.timeout)
        print("✓ APIClient initialized")
        
        # Test state manager
        state_manager = StateManager(config)
        await state_manager.load_state()
        print("✓ StateManager initialized and state loaded")
        
        # Test job monitor
        job_monitor = JobMonitor(config, api_client, state_manager)
        print("✓ JobMonitor initialized")
        
        # Test is_video_extracted method
        test_code = "test123"
        try:
            is_extracted = await qdrant_utils.is_video_extracted(test_code)
            print(f"✓ is_video_extracted test: {test_code} -> {is_extracted}")
        except Exception as e:
            print(f"⚠ is_video_extracted test failed: {e}")
        
        print("\n✅ All components initialized successfully!")
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_components())
