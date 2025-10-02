#!/usr/bin/env python3
"""
Migration script to update imports and paths for the new project structure.
"""

import os
import re
import sys
from pathlib import Path

def update_imports_in_file(file_path: Path):
    """Update import statements in a Python file."""
    if not file_path.suffix == '.py':
        return
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Update import statements
        replacements = [
            (r'from controllers\.', 'from src.api.controllers.'),
            (r'from models\.', 'from src.core.models.'),
            (r'from background\.', 'from src.core.background.'),
            (r'import controllers\.', 'import src.api.controllers.'),
            (r'import models\.', 'import src.core.models.'),
            (r'import background\.', 'import src.core.background.'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Updated imports in: {file_path}")
    
    except Exception as e:
        print(f"Error updating {file_path}: {e}")

def update_dockerfile():
    """Update Dockerfile for new structure."""
    dockerfile_path = Path("deploy/docker/Dockerfile")
    
    if not dockerfile_path.exists():
        print("Dockerfile not found, skipping...")
        return
    
    try:
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Update COPY statements for new structure
        replacements = [
            (r'COPY app\.py', 'COPY src/api/app.py'),
            (r'COPY main\.py', 'COPY main.py'),
            (r'COPY requirements\.txt', 'COPY requirements.txt'),
            (r'COPY controllers/', 'COPY src/api/controllers/'),
            (r'COPY models/', 'COPY src/core/models/'),
            (r'COPY background/', 'COPY src/core/background/'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        # Update CMD/ENTRYPOINT for new structure
        content = re.sub(
            r'CMD.*uvicorn.*app:app',
            'CMD ["python", "main.py"]',
            content
        )
        
        if content != original_content:
            with open(dockerfile_path, 'w') as f:
                f.write(content)
            print(f"Updated Dockerfile: {dockerfile_path}")
    
    except Exception as e:
        print(f"Error updating Dockerfile: {e}")

def update_test_scripts():
    """Update test scripts for new structure."""
    test_script_paths = [
        Path("tests/integration/test_locally.sh"),
        Path("scripts/run-tests.sh"),
    ]
    
    for script_path in test_script_paths:
        if not script_path.exists():
            continue
        
        try:
            with open(script_path, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Update uvicorn command
            content = re.sub(
                r'uvicorn app:app',
                'uvicorn src.api.app:app',
                content
            )
            
            # Update pytest commands
            content = re.sub(
                r'pytest test/',
                'pytest tests/',
                content
            )
            
            if content != original_content:
                with open(script_path, 'w') as f:
                    f.write(content)
                print(f"Updated test script: {script_path}")
        
        except Exception as e:
            print(f"Error updating {script_path}: {e}")

def main():
    """Main migration function."""
    print("Starting project structure migration...")
    
    # Update Python files
    src_dirs = [
        Path("src"),
        Path("tests"),
    ]
    
    for src_dir in src_dirs:
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                update_imports_in_file(py_file)
    
    # Update Dockerfile
    update_dockerfile()
    
    # Update test scripts
    update_test_scripts()
    
    print("Migration completed!")
    print("\nNext steps:")
    print("1. Test the application: python main.py")
    print("2. Run tests: pytest tests/")
    print("3. Build Docker image: docker build -f deploy/docker/Dockerfile -t pipeline-api .")
    print("4. Update any remaining hardcoded paths manually")

if __name__ == "__main__":
    main()
