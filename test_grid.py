#!/usr/bin/env python3
"""Test the new professional trading grid endpoint"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from api.app import app
import uvicorn

if __name__ == "__main__":
    print("🏛️ Starting Professional Trading Grid Test Server...")
    print("📊 Features:")
    print("  • Portfolio holdings (Y-axis) vs Top 50 volume cryptos (X-axis)")
    print("  • Up to 300 trading pairs")
    print("  • WebSocket-powered real-time data")
    print("  • Volume-based crypto ranking")
    print("")
    print("🌐 Server will be available at: http://localhost:8000")
    print("🔗 Grid endpoint: http://localhost:8000/grid/matrix")
    print("🎯 Dashboard: Open web/index.html in your browser")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
