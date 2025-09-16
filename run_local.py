#!/usr/bin/env python3
"""
Local launcher for the Research Platform
Simplified version for local hosting without cloud dependencies
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for local application"""
    print("🚀 Starting Research Platform (Local Mode)")
    print("=" * 50)
    
    # Set environment variables for local development
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = 'True'
    
    try:
        # Import and run the FastAPI app
        from app import app
        import uvicorn
        
        print("✅ Application initialized successfully")
        print("🌐 Running on: http://localhost:8000")
        print("📝 API endpoints available at: http://localhost:8000/api")
        print("🌐 Web interface: http://localhost:8000")
        print("\n💡 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Run the FastAPI server using uvicorn
        uvicorn.run(
            "app:app",
            host='0.0.0.0',
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Error importing application: {e}")
        print("🔧 Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
