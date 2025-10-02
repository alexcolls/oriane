#!/usr/bin/env python3
"""
Script to display the reorganized project structure
"""

import os
from pathlib import Path

def show_tree(path, prefix="", max_depth=3, current_depth=0):
    """Display directory tree structure."""
    if current_depth >= max_depth:
        return
    
    path = Path(path)
    if not path.exists():
        return
    
    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    
    for i, item in enumerate(items):
        if item.name.startswith('.') and item.name not in ['.github', '.env.sample']:
            continue
            
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        
        print(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir() and not item.name.startswith('__pycache__'):
            extension = "    " if is_last else "│   "
            show_tree(item, prefix + extension, max_depth, current_depth + 1)

def main():
    """Main function to display project structure."""
    print("🏗️  PIPELINE API - REORGANIZED PROJECT STRUCTURE")
    print("=" * 60)
    print()
    
    # Show main structure
    print("📁 Project Structure:")
    show_tree(".", max_depth=4)
    
    print("\n" + "=" * 60)
    print("📊 STRUCTURE SUMMARY")
    print("=" * 60)
    
    # Count files by type
    file_counts = {
        'Python files': 0,
        'Test files': 0,
        'Config files': 0,
        'Documentation': 0,
        'Scripts': 0,
        'Docker/K8s': 0,
        'Other': 0
    }
    
    for root, dirs, files in os.walk('.'):
        # Skip hidden and cache directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.startswith('.') and file != '.env.sample':
                continue
                
            if file.endswith('.py'):
                if 'test' in file.lower():
                    file_counts['Test files'] += 1
                else:
                    file_counts['Python files'] += 1
            elif file.endswith(('.yml', '.yaml', '.ini', '.cfg', '.txt', '.env')):
                file_counts['Config files'] += 1
            elif file.endswith(('.md', '.rst')):
                file_counts['Documentation'] += 1
            elif file.endswith('.sh') or 'script' in root:
                file_counts['Scripts'] += 1
            elif 'docker' in root.lower() or 'k8s' in root.lower() or file == 'Dockerfile':
                file_counts['Docker/K8s'] += 1
            else:
                file_counts['Other'] += 1
    
    for category, count in file_counts.items():
        print(f"• {category}: {count}")
    
    print("\n" + "=" * 60)
    print("🎯 KEY DIRECTORIES")
    print("=" * 60)
    
    key_dirs = {
        'src/': 'Source code (API, core business logic, utilities)',
        'tests/': 'Test suite (unit, integration, e2e)',
        'config/': 'Configuration files and settings',
        'deploy/': 'Docker and Kubernetes deployment files',
        'scripts/': 'Utility and development scripts',
        'docs/': 'Documentation (API, deployment, development)',
        'examples/': 'Example requests and sample data',
        '.github/workflows/': 'CI/CD pipeline configuration',
    }
    
    for dir_path, description in key_dirs.items():
        status = "✅" if Path(dir_path).exists() else "❌"
        print(f"{status} {dir_path:<20} {description}")
    
    print("\n" + "=" * 60)
    print("🚀 GETTING STARTED")
    print("=" * 60)
    
    print("""
1. Install dependencies:
   pip install -r requirements.txt

2. Copy and configure environment:
   cp config/.env.sample .env

3. Start the application:
   python main.py

4. Run tests:
   pytest tests/

5. Build Docker image:
   docker build -f deploy/docker/Dockerfile -t pipeline-api .

6. View API documentation:
   http://localhost:8000/api/docs (requires auth)
""")

if __name__ == "__main__":
    main()
