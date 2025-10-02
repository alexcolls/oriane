#!/usr/bin/env python3
"""
Test script to verify model preloading functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.core.models.model_preloader import preload_models, get_preloader


async def test_model_preload():
    """Test the model preloading functionality"""
    print("Testing model preloading...")
    
    # Check initial state
    preloader = get_preloader()
    print(f"Initial model loaded status: {preloader.is_model_loaded()}")
    
    # Test model preloading
    await preload_models()
    
    # Check final state
    print(f"Final model loaded status: {preloader.is_model_loaded()}")
    
    print("Model preloading test completed!")


if __name__ == "__main__":
    asyncio.run(test_model_preload())
