#!/usr/bin/env python3
"""
Test runner script for the extraction pipeline smoke tests.
"""

import os
import subprocess
import sys


def install_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    try:
        subprocess.run(
            ["python3", "-m", "pip", "install", "pytest>=7.0.0", "pytest-mock>=3.6.0"], check=True
        )
    except subprocess.CalledProcessError:
        print("Warning: Could not install dependencies. Please install manually:")
        print("pip install pytest>=7.0.0 pytest-mock>=3.6.0")
        print("Or use apt: sudo apt install python3-pytest")


def run_tests():
    """Run the smoke tests."""
    print("Running smoke tests...")
    test_dir = os.path.dirname(os.path.abspath(__file__))

    # Run pytest with verbose output
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            os.path.join(test_dir, "test_smoke.py"),
            "-v",
            "--tb=short",
        ],
        capture_output=True,
        text=True,
    )

    print("Test output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)

    return result.returncode == 0


if __name__ == "__main__":
    try:
        install_dependencies()
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)
