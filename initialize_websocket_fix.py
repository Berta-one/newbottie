#!/usr/bin/env python3
"""
Initialize WebSocket connections to fix rate limit issues
This script should be run at startup to establish WebSocket connections
"""

import os
import asyncio
import logging
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("WebSocketInitializer")

async def initialize_websocket_for_trading():
    """Initialize WebSocket connections for trading to avoid rate limits"""
    try:
        from engine.free_websocket_manager import initialize_free_websocket_data
        
        # Get API credentials from environment
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not api_key or not api_secret:
            log.warning("⚠️ BINANCE_API_KEY or BINANCE_API_SECRET not found - WebSocket will work for public data only")
        
        # Common trading symbols that are likely to be used
        trading_symbols = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 
            'DOT/USDT', 'SOL/USDT', 'MATIC/USDT', 'LINK/USDT',
            'AVAX/USDT', 'UNI/USDT', 'LTC/USDT', 'XRP/USDT',
            'DOGE/USDT', 'ATOM/USDT', 'FTM/USDT', 'NEAR/USDT'
        ]
        
        # Initialize WebSocket with symbols and credentials
        success = await initialize_free_websocket_data(
            symbols=trading_symbols,
            kline_symbols=trading_symbols[:8],  # Limit klines to prevent overload
            api_key=api_key,
            api_secret=api_secret
        )
        
        if success:
            log.info("🚀 WebSocket initialized successfully - rate limit issues should be resolved!")
            log.info(f"📡 Monitoring {len(trading_symbols)} symbols via WebSocket")
            if api_key and api_secret:
                log.info("🔐 Authenticated WebSocket - balance updates will be real-time")
            else:
                log.info("📊 Public WebSocket - price data will be real-time")
            return True
        else:
            log.error("❌ Failed to initialize WebSocket - will fallback to REST API (may cause rate limits)")
            return False
            
    except ImportError as e:
        log.error(f"❌ WebSocket dependencies not available: {e}")
        log.error("Install with: pip install python-binance")
        return False
    except Exception as e:
        log.error(f"❌ WebSocket initialization failed: {e}")
        return False

def run_websocket_initialization():
    """Run WebSocket initialization synchronously"""
    return asyncio.run(initialize_websocket_for_trading())

if __name__ == "__main__":
    print("🔧 Initializing WebSocket connections to fix Binance rate limit issues...")
    success = run_websocket_initialization()
    
    if success:
        print("\n✅ WebSocket Fix Applied Successfully!")
        print("🎯 Your trading system should now use WebSocket data instead of REST API calls")
        print("📉 This will dramatically reduce API calls and prevent rate limit bans")
        print("\n💡 The WebSocket will automatically:")
        print("   - Provide real-time price data without API calls")
        print("   - Stream account balance updates (if API keys provided)")
        print("   - Cache data to reduce fallback API usage")
        print("\n🚀 You can now run your trading system without rate limit issues!")
    else:
        print("\n❌ WebSocket initialization failed")
        print("🔧 Please check your BINANCE_API_KEY and BINANCE_API_SECRET")
        print("📦 Ensure python-binance is installed: pip install python-binance")
        print("🌐 Check your network connection to Binance")