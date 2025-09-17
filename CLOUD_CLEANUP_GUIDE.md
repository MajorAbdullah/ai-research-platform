# Cloud Deployment Cleanup Guide

This document provides a comprehensive guide for cleaning up your research platform codebase before cloud deployment.

## 🎯 Overview

When deploying to cloud platforms (like Heroku, Railway, Render, or AWS), you want to minimize the deployment package size and remove unnecessary files that are only needed for local development.

## 📊 Current Project Analysis

### Files Safe to Remove

#### 1. Development & Testing Files
- `test_integration.py` - Integration test script (6.2KB)
- `tests/demo_parallel.py` - Demo testing file
- `tests/test_parallel_processing.py` - Development test file

#### 2. Local Configuration & Scripts
- `dev.sh` - Local development script
- `deploy_local.sh` - Local deployment script  
- `setup.sh` - Local setup script
- `run_local.py` - Local runner (use `run.py` instead)

#### 3. Documentation Files (Optional)
- `README_LOCAL_HOSTING.md` - Local hosting documentation
- `CONTRIBUTING.md` - Contribution guidelines
- `IMPROVEMENTS_SUMMARY.md` - Development notes
- `image/` - Screenshots and demo images directory

#### 4. Log & Temporary Files
- `server.log` - Runtime log file (6KB)
- `*.pyc` - Python compiled files
- `__pycache__/` - Python cache directories

#### 5. Empty Directories
- `research_documents/archives/` - Empty directory
- `research_documents/market_research/` - Empty directory

#### 6. Development Configuration
- `config/requirements.txt` - Duplicate requirements file
- `.vscode/` - VS Code settings (if present)
- `.idea/` - PyCharm settings (if present)

#### 7. OS-Specific Files
- `.DS_Store` - macOS file system metadata
- `Thumbs.db` - Windows thumbnail cache

### Files to Keep

#### Essential Application Files
- `app.py` - Main FastAPI application ✅
- `run.py` - Production runner ✅
- `requirements.txt` - Python dependencies ✅

#### Core Application Code
- `models/` - Database models ✅
- `services/` - Business logic ✅
- `templates/` - HTML templates ✅

#### Configuration
- `config/__init__.py` - Config module ✅
- `.env` - Environment variables ✅
- `.gitignore` - Git ignore rules ✅

#### Data & Content
- `research_documents/` - Generated research files ✅
  - Keep: `comprehensive_research/`, `custom_research/`, `financial_analysis/`, `idea_validation/`, `metadata/`
  - Remove: `archives/` (empty), `market_research/` (empty)

#### Essential Documentation
- `README.md` - Main documentation ✅
- `LICENSE` - License file ✅

## 🧹 Automated Cleanup

Use the provided cleanup script:

```bash
# Preview what will be removed (dry run)
python cleanup_for_cloud.py

# Actually perform the cleanup
python cleanup_for_cloud.py --execute
```

## 📦 Size Reduction Estimate

| Category | Estimated Size Saved |
|----------|---------------------|
| Virtual environment (`.venv/`) | ~200-500MB |
| Git history (`.git/`) | ~5-20MB |
| Python cache files | ~1-5MB |
| Development files | ~50KB |
| Log files | ~6KB |
| Documentation/images | ~1-10MB |

**Total estimated savings: 200-500MB+**

## 🚀 Optimized Requirements for Cloud

The cleanup script creates `requirements_cloud.txt` with only essential dependencies:

```txt
# Core FastAPI and web framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0

# OpenAI and AI dependencies  
openai>=1.35.0

# HTTP and networking
requests>=2.31.0
aiohttp>=3.8.0

# Environment and configuration
python-dotenv>=1.0.0

# Database
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
```

## 🔧 Manual Cleanup Steps

If you prefer manual cleanup:

1. **Remove development files:**
   ```bash
   rm test_integration.py
   rm -rf tests/demo_parallel.py
   rm -rf tests/test_parallel_processing.py
   ```

2. **Remove local scripts:**
   ```bash
   rm dev.sh deploy_local.sh setup.sh run_local.py
   ```

3. **Clean Python cache:**
   ```bash
   find . -type d -name "__pycache__" -exec rm -rf {} +
   find . -name "*.pyc" -delete
   ```

4. **Remove empty directories:**
   ```bash
   rmdir research_documents/archives
   rmdir research_documents/market_research
   ```

5. **Remove logs and temporary files:**
   ```bash
   rm server.log
   rm -rf .DS_Store
   ```

## ⚠️ Important Notes

### Before Cleanup
- **Backup your project** - Create a backup before running cleanup
- **Test locally** - Ensure your application works after cleanup
- **Check environment variables** - Make sure `.env` file has required variables

### After Cleanup  
- **Test the application:** `python run.py`
- **Verify all endpoints work**
- **Check that research functionality is intact**

### Environment Variables Required
Ensure your `.env` file contains:
```env
OPENAI_API_KEY=your_openai_api_key
ENVIRONMENT=production
DEBUG=false
```

## 🌐 Cloud Deployment Checklist

- [ ] Run cleanup script
- [ ] Test application locally after cleanup  
- [ ] Use `requirements_cloud.txt` for deployment
- [ ] Set environment variables in cloud platform
- [ ] Configure port binding for cloud (usually via `PORT` env var)
- [ ] Test deployed application

## 📈 Expected Results

After cleanup, your deployment package should be:
- ✅ Significantly smaller (200-500MB+ saved)
- ✅ Contains only production-necessary files
- ✅ Faster deployment times
- ✅ Reduced cloud storage costs
- ✅ Cleaner, more maintainable codebase

## 🔍 Verification

After cleanup, your project structure should look like:

```
research-agent/
├── app.py                          # Main application
├── run.py                          # Production runner  
├── requirements.txt                # Dependencies
├── requirements_cloud.txt          # Optimized dependencies
├── .env                           # Environment variables
├── .gitignore                     # Git ignore
├── README.md                      # Documentation
├── LICENSE                        # License
├── models/                        # Database models
│   ├── __init__.py
│   └── database.py
├── services/                      # Business logic
│   ├── __init__.py
│   ├── document_manager.py
│   ├── research_client.py
│   └── storage_service.py
├── templates/                     # HTML templates
│   └── index.html
├── research_documents/            # Research data
│   ├── comprehensive_research/
│   ├── custom_research/
│   ├── financial_analysis/
│   ├── idea_validation/
│   └── metadata/
└── tests/                         # Essential tests only
    ├── conftest.py
    └── test_api.py
```

This streamlined structure is optimal for cloud deployment while maintaining all essential functionality.
