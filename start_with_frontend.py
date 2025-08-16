#!/usr/bin/env python3
"""
Start both API server and frontend server
"""

import os
import sys
import time
import subprocess
import threading
import http.server
import socketserver
from pathlib import Path

def start_api_server():
    """Start the API server on port 8000"""
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import uvicorn
        from api.app import app
        
        print("🚀 Starting API server on port 8000...")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except Exception as e:
        print(f"❌ API server error: {e}")

def start_frontend_server():
    """Start the frontend server on port 3000"""
    try:
        web_dir = Path(__file__).parent / "web"
        if not web_dir.exists():
            print(f"❌ Web directory not found: {web_dir}")
            return
            
        os.chdir(web_dir)
        
        class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                super().end_headers()
        
        with socketserver.TCPServer(("", 3000), MyHTTPRequestHandler) as httpd:
            print("🌐 Frontend server running at http://localhost:3000")
            print("📱 Open http://localhost:3000 in your browser")
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ Frontend server error: {e}")

if __name__ == "__main__":
    print("🏛️ BOTTIE COMPLETE SYSTEM")
    print("=" * 50)
    print("Starting both API and Frontend servers...")
    print("")
    print("🔗 URLs:")
    print("  • Frontend: http://localhost:3000")
    print("  • API: http://localhost:8000")
    print("")
    
    # Start frontend server in a separate thread
    frontend_thread = threading.Thread(target=start_frontend_server, daemon=True)
    frontend_thread.start()
    
    # Give frontend server time to start
    time.sleep(2)
    
    # Start API server in main thread
    start_api_server()