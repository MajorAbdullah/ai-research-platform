#!/usr/bin/env python3
"""
AI Research Platform Launcher
Unified launcher for local development and production hosting
"""

import uvicorn
import os
import sys
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def main():
    """Main entry point for the AI Research Platform"""
    parser = argparse.ArgumentParser(description="AI Research Platform Launcher")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--production", action="store_true", help="Run in production mode")
    
    args = parser.parse_args()
    
    # Print startup banner
    print("🚀 Starting AI Research Platform")
    print("=" * 60)
    print(f"🌐 Platform URL: http://localhost:{args.port}")
    print(f"📊 Dashboard: http://localhost:{args.port}/dashboard")
    print(f"📚 API Docs: http://localhost:{args.port}/api/docs")
    print(f"🔍 Health Check: http://localhost:{args.port}/health")
    print("=" * 60)
    
    # Configure reload based on mode
    reload_enabled = args.reload or not args.production
    
    try:
        # Import the FastAPI app
        from app import app
        
        print("✅ Application initialized successfully")
        print(f"🔧 Mode: {'Production' if args.production else 'Development'}")
        print(f"🔄 Auto-reload: {'Enabled' if reload_enabled else 'Disabled'}")
        print("\n💡 Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Run the FastAPI server
        uvicorn.run(
            "app:app",
            host=args.host,
            port=args.port,
            reload=reload_enabled,
            log_level="info" if not args.production else "warning"
        )
        
    except ImportError as e:
        print(f"❌ Error importing application: {e}")
        print("\n🔧 Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Research Platform")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
