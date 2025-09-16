#!/bin/bash

# AI Research Platform - Local Hosting Deployment Script
# This script sets up and runs the AI Research Platform for local hosting

set -e

echo "🚀 AI Research Platform - Local Hosting Setup"
echo "=============================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.13"

echo "📋 Checking Python version..."
if [[ $(echo "$python_version >= $required_version" | bc -l) -eq 1 ]]; then
    echo "✅ Python $python_version is compatible"
else
    echo "❌ Python $required_version+ required, found $python_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install/upgrade dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Check if database exists
if [ ! -f "research_platform.db" ]; then
    echo "🗄️ Database will be created automatically on first run"
else
    echo "✅ Database file exists"
fi

# Create research_documents directory if it doesn't exist
mkdir -p research_documents/{custom_research,idea_validation,market_research,financial_analysis,comprehensive_research,archives,metadata}
echo "✅ Research documents directory structure ready"

# Run health check
echo "🏥 Running application health check..."
python -c "
import sys
sys.path.append('.')
try:
    from app import app
    from services.research_client import OpenAIResearchClient
    print('✅ Application modules loaded successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'⚠️ Warning: {e}')
    print('✅ Basic imports work, some services may need configuration')
"

echo "✅ All checks passed!"
echo ""
echo "🌟 Setup Complete! 🌟"
echo "===================="
echo "To start the application:"
echo "  python run_local.py"
echo ""
echo "The application will be available at:"
echo "  🌐 Web Interface: http://localhost:8000"
echo "  📖 API Docs: http://localhost:8000/docs"
echo "  ❤️ Health Check: http://localhost:8000/health"
echo ""
echo "💡 Press Ctrl+C to stop the server when running"
echo "=============================================="
