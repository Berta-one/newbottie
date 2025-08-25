#!/usr/bin/env python3
"""
Startup script for Sntax P&L WebSocket Server
Handles dependencies and server initialization
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_dependencies():
    """Check and install required dependencies"""
    required_packages = [
        'websockets',
        'ccxt',
        'sqlite3'  # Built-in, but check availability
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"📦 Installing missing packages: {', '.join(missing_packages)}")
        for package in missing_packages:
            if package != 'sqlite3':  # sqlite3 is built-in
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--break-system-packages'])
        print("✅ Dependencies installed")
    else:
        print("✅ All dependencies satisfied")

def main():
    print("🚀 Starting Sntax P&L WebSocket Server")
    print("=" * 50)
    
    # Check dependencies
    check_dependencies()
    
    # Import and run server
    try:
        from websocket_pnl_server import PnLWebSocketServer
        
        # Create server instance
        server = PnLWebSocketServer()
        
        print("\n📊 P&L Server Configuration:")
        print(f"  - WebSocket Host: localhost")
        print(f"  - WebSocket Port: 8765")
        print(f"  - Database: trades_pnl.db")
        print(f"  - Features: Real-time P&L tracking, Trade storage, WebSocket updates")
        print("\n🌐 Dashboard URL: http://localhost:9000/pnl_dashboard.html")
        print("\n💡 Commands available:")
        print("  - Ctrl+C to stop server")
        print("  - Use dashboard to simulate trades")
        print("  - Export reports in JSON format")
        
        # Add sample data for demonstration
        print("\n🧪 Adding sample trades for demonstration...")
        import time
        from datetime import datetime
        
        sample_trades = [
            {"symbol": "BTCUSDT", "side": "buy", "amount": 0.001, "price": 45000, "pnl": 450.50},
            {"symbol": "ETHUSDT", "side": "sell", "amount": 0.1, "price": 2800, "pnl": -28.75},
            {"symbol": "ADAUSDT", "side": "buy", "amount": 100, "price": 0.45, "pnl": 2.25},
            {"symbol": "BTCUSDT", "side": "sell", "amount": 0.0005, "price": 46000, "pnl": -11.50},
            {"symbol": "ETHUSDT", "side": "buy", "amount": 0.05, "price": 2750, "pnl": 13.75},
            {"symbol": "BNBUSDT", "side": "buy", "amount": 0.5, "price": 320, "pnl": 8.00},
            {"symbol": "ADAUSDT", "side": "sell", "amount": 200, "price": 0.48, "pnl": 6.00},
            {"symbol": "BTCUSDT", "side": "buy", "amount": 0.002, "price": 44500, "pnl": 89.00},
        ]
        
        for i, trade in enumerate(sample_trades):
            trade_data = {
                "id": f"demo_{i}_{int(time.time())}",
                "symbol": trade["symbol"],
                "side": trade["side"],
                "amount": trade["amount"],
                "price": trade["price"],
                "cost": trade["amount"] * trade["price"],
                "fee": {"cost": trade["amount"] * trade["price"] * 0.001},
                "timestamp": int((time.time() - (i * 7200)) * 1000),  # Spread over hours
                "datetime": datetime.fromtimestamp(time.time() - (i * 7200)).isoformat(),
                "status": "closed",
                "pnl": trade["pnl"]
            }
            server.db.store_trade(trade_data)
        
        print("✅ Sample trades added")
        print("\n🎯 Server starting...")
        
        # Start server
        asyncio.run(server.start_server("localhost", 8765))
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Make sure port 8765 is not in use")
        print("  2. Check that Python 3.7+ is installed")
        print("  3. Verify websockets package is installed")
        sys.exit(1)

if __name__ == "__main__":
    main()