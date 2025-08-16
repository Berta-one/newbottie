#!/usr/bin/env python3
"""
Start complete Bottie system with both API and Frontend
"""

import os
import sys
import subprocess
import time

def main():
    print("🏛️ BOTTIE COMPLETE SYSTEM STARTUP")
    print("=" * 50)
    
    # Start frontend server (web directory)
    print("🌐 Starting frontend server on port 3000...")
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "http.server", "3000", "--directory", "web"
    ], cwd=os.getcwd())
    
    # Wait a moment for frontend to start
    time.sleep(2)
    
    print("🚀 Starting API server on port 8000...")
    print("")
    print("🔗 Access URLs:")
    print("  • Frontend: http://localhost:3000")
    print("  • API: http://localhost:8000")
    print("")
    print("💡 To connect frontend to local API, use:")
    print("  http://localhost:3000?api=http://localhost:8000")
    print("")
    
    # Start API server
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import uvicorn
        from api.app import app
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        frontend_process.terminate()
        frontend_process.wait()
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        print("💡 Make sure to install dependencies: pip install uvicorn fastapi")
        frontend_process.terminate()
        frontend_process.wait()

if __name__ == "__main__":
    main()