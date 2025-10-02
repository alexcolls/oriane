#!/usr/bin/env python3
"""
Single Video Test Script
=======================

Test processing a single video to debug issues with the pipeline.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Core pipeline Python interpreter
CORE_VENV_PY = "/home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline/.venv/bin/python"

def test_single_video(code: str):
    """Test processing a single video."""
    print(f"🧪 Testing single video: {code}")
    
    try:
        # Prepare job input for core pipeline
        job_input = json.dumps([{"platform": "instagram", "code": code}])
        
        # Set up environment
        env = os.environ.copy()
        env["JOB_INPUT"] = job_input
        env["VIRTUAL_ENV"] = str(Path(CORE_VENV_PY).parent.parent)
        # Force CPU usage to avoid CUDA OOM
        env["CUDA_VISIBLE_DEVICES"] = ""
        env["FORCE_CPU"] = "1"
        
        print("🔧 Environment set up")
        print(f"   JOB_INPUT length: {len(job_input)}")
        print(f"   FORCE_CPU: {env.get('FORCE_CPU')}")
        print(f"   CUDA_VISIBLE_DEVICES: '{env.get('CUDA_VISIBLE_DEVICES')}'")
        
        # Sanity check
        if not Path(CORE_VENV_PY).exists():
            raise FileNotFoundError(f"Core venv python not found at {CORE_VENV_PY}")
        
        print("✅ Core venv python found")
        
        # Execute core pipeline with real-time output
        print("🚀 Starting core pipeline...")
        result = subprocess.run(
            [
                CORE_VENV_PY,
                "/home/quantium/labs/oriane/ExtractionPipeline/core/py/pipeline/entrypoint.py",
            ],
            env=env,
            timeout=300,  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {code} - SUCCESS")
            return True
        else:
            print(f"❌ {code} - FAILED with exit code: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {code} - TIMEOUT after 5 minutes")
        return False
    except Exception as e:
        print(f"💥 {code} - ERROR: {e}")
        return False

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python3 test_single_video.py <instagram_code>")
        sys.exit(1)
    
    code = sys.argv[1]
    print(f"🎬 Testing Instagram Video Processing")
    print(f"📱 Code: {code}")
    print("=" * 50)
    
    success = test_single_video(code)
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
