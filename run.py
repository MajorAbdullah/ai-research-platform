#!/usr/bin/env python3
"""
Simple launcher for the AI Research Platform
Local hosting version
"""

import uvicorn
import os
import sys

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting AI Research Platform (Local Version)")
    print("📍 Platform will be available at: http://localhost:8000")
    print("📊 Dashboard available at: http://localhost:8000/dashboard")
    print("🔍 Health check: http://localhost:8000/health")
    print("---")
    
    try:
        # Import the FastAPI app from api/main.py
        from api.main import app
        
        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,  # Enable auto-reload for development
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Research Platform")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
