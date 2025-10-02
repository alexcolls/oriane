#!/usr/bin/env python3
"""
Validation script to check the new project structure.
"""

import os
import sys
from pathlib import Path

def check_directory_structure():
    """Check if the expected directories exist."""
    print("🔍 Checking directory structure...")
    
    expected_dirs = [
        "src",
        "src/api",
        "src/core",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration", 
        "tests/e2e",
        "config",
        "deploy",
        "deploy/docker",
        "deploy/kubernetes",
        "scripts",
        "docs",
        "docs/api",
        "docs/deployment",
        "docs/development",
        "examples",
        ".github",
        ".github/workflows",
    ]
    
    missing_dirs = []
    for dir_path in expected_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ Missing directories: {', '.join(missing_dirs)}")
        return False
    else:
        print("✅ All expected directories present")
        return True

def check_key_files():
    """Check if key files exist in expected locations."""
    print("\\n🔍 Checking key files...")
    
    expected_files = [
        "main.py",
        "requirements.txt",
        "README.md",
        "MANIFEST.md",
        "src/__init__.py",
        "src/api/__init__.py",
        "src/api/app.py",
        "src/core/__init__.py",
        "src/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/e2e/__init__.py",
        "config/requirements.txt",
        "config/requirements-dev.txt",
        "config/.env.sample",
        "config/pytest.ini",
        "config/setup.cfg",
        "deploy/docker/Dockerfile",
        ".github/workflows/ci.yml",
        ".github/workflows/validate.yml",
    ]
    
    missing_files = []
    for file_path in expected_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All expected key files present")
        return True

def check_imports():
    """Check if imports are working with the new structure."""
    print("\\n🔍 Checking imports...")
    
    try:
        # Add current directory to Python path
        import sys
        sys.path.insert(0, os.getcwd())
        
        # Test basic imports
        import src
        import src.api
        import src.core
        import src.utils
        print("✅ Basic package imports working")
        
        # Test if main.py can run (this will test the app import)
        import subprocess
        result = subprocess.run(
            [sys.executable, "-c", "import main; print('Main module import successful')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Main module import working")
            return True
        else:
            print(f"❌ Main module import failed: {result.stderr}")
            return False
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def check_scripts():
    """Check if scripts are executable."""
    print("\\n🔍 Checking scripts...")
    
    script_files = [
        "scripts/run-dev.sh",
        "scripts/run-tests.sh",
        "scripts/setup-project.sh",
        "scripts/deploy.sh",
        "scripts/deploy-to-eks.sh",
        "scripts/migrate_structure.py",
        "scripts/validate_structure.py",
        "tests/integration/test_locally.sh",
    ]
    
    non_executable = []
    for script in script_files:
        if Path(script).exists():
            if not os.access(script, os.X_OK):
                non_executable.append(script)
    
    if non_executable:
        print(f"❌ Non-executable scripts: {', '.join(non_executable)}")
        print("Run: chmod +x " + " ".join(non_executable))
        return False
    else:
        print("✅ All scripts are executable")
        return True

def check_configuration():
    """Check configuration files."""
    print("\\n🔍 Checking configuration...")
    
    config_files = [
        ("config/requirements.txt", "fastapi"),
        ("config/requirements-dev.txt", "pytest"),
        ("config/.env.sample", "API_NAME"),
        ("config/pytest.ini", "[tool:pytest]"),
        ("config/setup.cfg", "[flake8]"),
    ]
    
    issues = []
    for file_path, expected_content in config_files:
        if Path(file_path).exists():
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                if expected_content not in content:
                    issues.append(f"{file_path} missing '{expected_content}'")
            except Exception as e:
                issues.append(f"Error reading {file_path}: {e}")
        else:
            issues.append(f"Missing {file_path}")
    
    if issues:
        print(f"❌ Configuration issues: {', '.join(issues)}")
        return False
    else:
        print("✅ Configuration files look good")
        return True

def main():
    """Main validation function."""
    print("🚀 Validating project structure reorganization...")
    print("=" * 60)
    
    checks = [
        check_directory_structure,
        check_key_files,
        check_imports,
        check_scripts,
        check_configuration,
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print("\\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    if all(results):
        print("🎉 All validations passed! Project structure is ready.")
        print("\\nNext steps:")
        print("1. Test the application: python main.py")
        print("2. Run tests: pytest tests/")
        print("3. Build Docker image: docker build -f deploy/docker/Dockerfile -t pipeline-api .")
        print("4. Commit changes to version control")
        return 0
    else:
        print("❌ Some validations failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
