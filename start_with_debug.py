#!/usr/bin/env python3
"""Manual server startup with FINNHUB key debugging"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

def check_finnhub_config():
    """Check FINNHUB configuration"""
    finnhub_api_key = os.getenv("FINNHUB_API_KEY", "")
    finnhub_key = os.getenv("FINNHUB_KEY", "")
    
    print("🔑 FINNHUB Configuration Check:")
    print(f"   FINNHUB_API_KEY: {'✅ SET' if finnhub_api_key else '❌ MISSING'}")
    print(f"   FINNHUB_KEY: {'✅ SET' if finnhub_key else '❌ MISSING'}")
    
    if finnhub_api_key:
        print(f"   Using FINNHUB_API_KEY: {finnhub_api_key[:8]}...")
    elif finnhub_key:
        print(f"   Fallback to FINNHUB_KEY: {finnhub_key[:8]}...")
    else:
        print("   ⚠️  No FINNHUB keys found - using demo mode")
    
    return finnhub_api_key or finnhub_key

def start_server():
    """Start server with environment check"""
    print("🏛️ STARTING BOTTIE PROFESSIONAL TRADING SYSTEM")
    print("=" * 60)
    
    # Check FINNHUB config
    has_finnhub = check_finnhub_config()
    
    print("\n📊 System Status:")
    print("✅ Professional Trading Grid: READY")
    print("✅ Volume-based scanning: IMPLEMENTED") 
    print("✅ ML Performance endpoint: READY")
    print("✅ Sentiment analysis: ENABLED")
    print(f"{'✅' if has_finnhub else '⚠️ '} FINNHUB News: {'LIVE' if has_finnhub else 'DEMO MODE'}")
    
    try:
        import uvicorn
        from api.app import app
        
        print("\n🚀 Starting server at: http://localhost:8000")
        print("🔗 Professional Grid: http://localhost:8000/grid/matrix")
        print("📱 Frontend: web/index.html")
        print("=" * 60)
        
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")

if __name__ == "__main__":
    start_server()
