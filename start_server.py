#!/usr/bin/env python3
"""Start the Bottie API server with the new professional trading grid"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    import uvicorn
    from api.app import app
    
    print("🏛️ BOTTIE PROFESSIONAL TRADING SYSTEM")
    print("=" * 50)
    print("✅ All dashboard issues resolved")
    print("🔥 NEW: Professional Trading Grid implemented!")
    print("📊 Features:")
    print("  • Portfolio holdings (Y) × Top 50 volume cryptos (X)")
    print("  • Up to 300 cross-pair combinations")
    print("  • Live Binance volume data")
    print("  • WebSocket-optimized performance")
    print("  • ALL crypto-to-crypto atomic swaps (not just USDT)")
    print("")
    print("🌐 Starting server at: http://localhost:8000")
    print("🔗 Key endpoints:")
    print("  • /grid/matrix - Professional trading grid")
    print("  • /ml/performance - ML performance data")
    print("  • /signals - Trading signals")
    print("  • /health - System health")
    print("")
    print("🎯 Frontend: Open web/index.html in your browser")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("💡 Install with: pip install uvicorn fastapi")
except Exception as e:
    print(f"❌ Server error: {e}")
