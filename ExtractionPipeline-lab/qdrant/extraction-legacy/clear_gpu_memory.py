#!/usr/bin/env python3
"""
GPU Memory Cleanup Utility
==========================

Clears CUDA memory cache and kills processes that might be holding GPU memory.
Run this before starting the extraction pipeline to ensure clean GPU state.
"""

import subprocess
import sys
import time

def run_command(cmd, description):
    """Run a command and handle errors gracefully."""
    try:
        print(f"🔧 {description}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"⚠️  {description} failed (this may be normal)")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
    except Exception as e:
        print(f"❌ {description} error: {e}")

def main():
    print("🚀 Starting GPU Memory Cleanup...")
    print("=" * 50)
    
    # Check if CUDA is available
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ NVIDIA driver not found or CUDA not available")
            sys.exit(1)
        print("✅ NVIDIA GPU detected")
    except FileNotFoundError:
        print("❌ nvidia-smi not found - CUDA not available")
        sys.exit(1)
    
    # Clear Python GPU memory if torch is available
    run_command("""python3 -c "
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    print('GPU memory cache cleared')
else:
    print('CUDA not available in PyTorch')
" """, "Clearing PyTorch CUDA cache")
    
    # Kill any lingering Python processes that might be using GPU
    run_command("pkill -f 'python.*pipeline'", "Killing lingering pipeline processes")
    run_command("pkill -f 'python.*extract'", "Killing lingering extraction processes")
    
    # Give processes time to clean up
    print("⏳ Waiting for processes to clean up...")
    time.sleep(2)
    
    # Show current GPU memory usage
    print("\n📊 Current GPU Memory Status:")
    run_command("nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits", "GPU memory usage")
    
    print("\n✅ GPU cleanup completed!")
    print("🚀 You can now run your extraction pipeline")

if __name__ == "__main__":
    main()
