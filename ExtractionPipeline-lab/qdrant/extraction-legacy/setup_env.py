#!/usr/bin/env python3
"""
Migration script to set up a proper virtual environment for the extraction pipeline.
This script creates a new virtual environment and installs dependencies from both
./requirements.txt and ../../core/py/pipeline/requirements.txt
"""

import os
import subprocess
import sys
import venv
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(
        cmd, shell=isinstance(cmd, str), cwd=cwd, capture_output=True, text=True, check=check
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def main():
    # Get current directory
    current_dir = Path.cwd()
    print(f"Working in: {current_dir}")

    # Define paths
    venv_dir = current_dir / ".venv"
    local_requirements = current_dir / "requirements.txt"
    core_requirements = (
        current_dir / ".." / ".." / "core" / "py" / "pipeline" / "requirements.txt"
    )

    # Check if requirements files exist
    if not local_requirements.exists():
        print(f"Error: {local_requirements} not found!")
        sys.exit(1)
    if not core_requirements.exists():
        print(f"Error: {core_requirements} not found!")
        sys.exit(1)

    print(f"Local requirements: {local_requirements}")
    print(f"Core requirements: {core_requirements}")

    # Remove existing .venv if it exists
    if venv_dir.exists():
        print(f"Removing existing virtual environment at {venv_dir}")
        import shutil

        shutil.rmtree(venv_dir)

    # Create new virtual environment
    print(f"Creating virtual environment at {venv_dir}")
    venv.create(venv_dir, with_pip=True)

    # Determine the python executable in the virtual environment
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"

    # Upgrade pip
    print("Upgrading pip...")
    run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])

    # Install core requirements first (includes PyTorch and heavy dependencies)
    print("Installing core pipeline requirements...")
    run_command([str(pip_exe), "install", "-r", str(core_requirements)])

    # Install local requirements (may override some versions)
    print("Installing local requirements...")
    run_command([str(pip_exe), "install", "-r", str(local_requirements)])

    # Verify installation
    print("Verifying installation...")
    result = run_command(
        [
            str(python_exe),
            "-c",
            "import cv2, torch, psycopg2; print('All key modules imported successfully')",
        ],
        check=False,
    )

    if result.returncode == 0:
        print("✅ Virtual environment setup completed successfully!")
        print(f"To activate the environment, run:")
        if sys.platform == "win32":
            print(f"    {venv_dir / 'Scripts' / 'activate.bat'}")
        else:
            print(f"    source {venv_dir / 'bin' / 'activate'}")
    else:
        print("❌ There were issues with the installation. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
