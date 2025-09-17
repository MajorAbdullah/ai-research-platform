#!/usr/bin/env python3
"""
Cloud Deployment Cleanup Script
===============================

This script removes unnecessary files and directories that are not needed for cloud deployment.
It helps reduce the deployment package size and removes development-specific files.

Files and directories to remove:
1. Empty directories
2. Development and testing files
3. Local configuration files
4. Cache and temporary files
5. Documentation and demo files (keeping essential ones)
6. OS-specific files
"""

import os
import shutil
import sys
from pathlib import Path

def get_files_to_remove():
    """Define files and directories to remove for cloud deployment"""
    
    # Files to remove (exact paths relative to project root)
    files_to_remove = [
        # Development and testing files
        "test_integration.py",
        "tests/demo_parallel.py", 
        "tests/test_parallel_processing.py",
        
        # Local configuration files
        "dev.sh",
        "deploy_local.sh",
        "setup.sh",
        "run_local.py",
        
        # Log files and temporary files
        "server.log",
        
        # Documentation (keeping main README.md)
        "README_LOCAL_HOSTING.md",
        "CONTRIBUTING.md",
        "IMPROVEMENTS_SUMMARY.md",
        
        # Development configuration
        "config/requirements.txt",  # Use main requirements.txt instead
        
        # OS-specific files that might exist
        ".DS_Store",
        "Thumbs.db",
        
        # IDE files that might exist
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        "*~",
        
        # Image folder (demo images)
        "image/",
    ]
    
    # Directories to remove (empty or unnecessary)
    directories_to_remove = [
        # Empty research directories
        "research_documents/archives",
        "research_documents/market_research",
        
        # Development directories
        "image",
        
        # Cache directories
        "__pycache__",
        "models/__pycache__",
        "services/__pycache__",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        
        # Virtual environment (if accidentally included)
        ".venv",
        "venv",
        "env",
        
        # Git directory (usually not needed in cloud deployment)
        ".git",
    ]
    
    return files_to_remove, directories_to_remove

def safe_remove_file(file_path, dry_run=True):
    """Safely remove a file"""
    if os.path.exists(file_path):
        if os.path.isfile(file_path):
            if dry_run:
                print(f"[DRY RUN] Would remove file: {file_path}")
                return True
            else:
                try:
                    os.remove(file_path)
                    print(f"✅ Removed file: {file_path}")
                    return True
                except Exception as e:
                    print(f"❌ Error removing file {file_path}: {e}")
                    return False
        else:
            print(f"⚠️ Not a file: {file_path}")
    else:
        print(f"⚠️ File not found: {file_path}")
    return False

def safe_remove_directory(dir_path, dry_run=True):
    """Safely remove a directory and all its contents"""
    if os.path.exists(dir_path):
        if os.path.isdir(dir_path):
            if dry_run:
                print(f"[DRY RUN] Would remove directory: {dir_path}")
                return True
            else:
                try:
                    shutil.rmtree(dir_path)
                    print(f"✅ Removed directory: {dir_path}")
                    return True
                except Exception as e:
                    print(f"❌ Error removing directory {dir_path}: {e}")
                    return False
        else:
            print(f"⚠️ Not a directory: {dir_path}")
    else:
        print(f"⚠️ Directory not found: {dir_path}")
    return False

def get_directory_size(path):
    """Calculate total size of directory"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except (OSError, IOError):
        pass
    return total_size

def format_size(size_bytes):
    """Format bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def analyze_project_size(project_root):
    """Analyze current project size"""
    print("📊 Project Size Analysis")
    print("=" * 50)
    
    total_size = get_directory_size(project_root)
    print(f"Total project size: {format_size(total_size)}")
    
    # Analyze major directories
    major_dirs = ["research_documents", "services", "models", "tests", ".venv", ".git"]
    
    for dir_name in major_dirs:
        dir_path = os.path.join(project_root, dir_name)
        if os.path.exists(dir_path):
            dir_size = get_directory_size(dir_path)
            percentage = (dir_size / total_size * 100) if total_size > 0 else 0
            print(f"  {dir_name}: {format_size(dir_size)} ({percentage:.1f}%)")
    
    print()

def cleanup_for_cloud_deployment(dry_run=True):
    """Main cleanup function"""
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    print(f"Project root: {project_root}")
    print()
    
    # Analyze current size
    if not dry_run:
        analyze_project_size(project_root)
    
    mode = "DRY RUN" if dry_run else "ACTUAL CLEANUP"
    print(f"🧹 Cloud Deployment Cleanup - {mode}")
    print("=" * 60)
    print()
    
    files_to_remove, directories_to_remove = get_files_to_remove()
    
    removed_files = 0
    removed_dirs = 0
    
    # Remove files
    print("📄 Removing unnecessary files...")
    for file_path in files_to_remove:
        full_path = os.path.join(project_root, file_path)
        if safe_remove_file(full_path, dry_run):
            removed_files += 1
    
    print()
    
    # Remove directories
    print("📁 Removing unnecessary directories...")
    for dir_path in directories_to_remove:
        full_path = os.path.join(project_root, dir_path)
        if safe_remove_directory(full_path, dry_run):
            removed_dirs += 1
    
    print()
    
    # Remove files matching patterns
    print("🔍 Removing files matching patterns...")
    patterns_to_remove = ["*.pyc", "*.pyo", "*.pyd", "__pycache__"]
    
    for root, dirs, files in os.walk(project_root):
        # Remove __pycache__ directories
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            if safe_remove_directory(pycache_path, dry_run):
                removed_dirs += 1
            dirs.remove("__pycache__")  # Don't traverse into it
        
        # Remove .pyc files
        for file in files:
            if file.endswith(('.pyc', '.pyo', '.pyd')):
                file_path = os.path.join(root, file)
                if safe_remove_file(file_path, dry_run):
                    removed_files += 1
    
    print()
    print("📋 Cleanup Summary")
    print("=" * 30)
    print(f"Files processed: {removed_files}")
    print(f"Directories processed: {removed_dirs}")
    
    if dry_run:
        print()
        print("⚠️  This was a DRY RUN - no files were actually removed")
        print("🔧 To perform actual cleanup, run: python cleanup_for_cloud.py --execute")
    else:
        print()
        print("✅ Cleanup completed successfully!")
        
        # Show new size
        print()
        analyze_project_size(project_root)

def create_cloud_requirements():
    """Create optimized requirements.txt for cloud deployment"""
    
    cloud_requirements = """# Core FastAPI and web framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0

# OpenAI and AI dependencies
openai>=1.35.0

# HTTP and networking
requests>=2.31.0
aiohttp>=3.8.0

# Data processing
pydantic>=2.0.0
python-dateutil>=2.8.0

# Environment and configuration
python-dotenv>=1.0.0

# Database (SQLite for simplicity)
aiosqlite>=0.19.0

# Web scraping and content processing
beautifulsoup4>=4.12.0
html2text>=2020.1.16

# Search functionality
ddgs>=5.0.0

# Utilities
typing-extensions>=4.7.0
markdown>=3.5.0
PyYAML>=6.0

# Optional: For enhanced performance
# uvloop>=0.17.0  # Uncomment for Linux/macOS deployment
"""
    
    requirements_path = "requirements_cloud.txt"
    
    with open(requirements_path, 'w') as f:
        f.write(cloud_requirements)
    
    print(f"✅ Created optimized cloud requirements: {requirements_path}")

def main():
    """Main execution"""
    
    # Check command line arguments
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] in ['--execute', '-e', '--run']:
        dry_run = False
        
        # Confirm with user
        print("⚠️  You are about to permanently remove files and directories!")
        print("This action cannot be undone.")
        confirm = input("Are you sure you want to continue? (yes/no): ").lower().strip()
        
        if confirm not in ['yes', 'y']:
            print("❌ Cleanup cancelled by user")
            return
    
    # Run cleanup
    cleanup_for_cloud_deployment(dry_run)
    
    # Create cloud requirements
    if not dry_run:
        print()
        create_cloud_requirements()
    
    print()
    print("🚀 Ready for cloud deployment!")
    
    if dry_run:
        print()
        print("Next steps:")
        print("1. Review the files that would be removed above")
        print("2. Run 'python cleanup_for_cloud.py --execute' to perform cleanup")
        print("3. Test your application locally after cleanup")
        print("4. Use requirements_cloud.txt for deployment")

if __name__ == "__main__":
    main()
