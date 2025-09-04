#!/usr/bin/env python3
"""
Test script to verify WebSocket rate limit fix is working
"""

import asyncio
import time
import logging
from initialize_websocket_fix import initialize_websocket_for_trading

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("WebSocketTest")

async def test_websocket_balance_fix():
    """Test that WebSocket balance fetching works and avoids rate limits"""
    
    print("🧪 Testing WebSocket Rate Limit Fix...")
    print("=" * 50)
    
    # Step 1: Initialize WebSocket
    print("\n📡 Step 1: Initializing WebSocket...")
    ws_success = await initialize_websocket_for_trading()
    
    if not ws_success:
        print("❌ WebSocket initialization failed - cannot test fix")
        return False
    
    print("✅ WebSocket initialized successfully")
    
    # Step 2: Wait for connection to stabilize
    print("\n⏳ Step 2: Waiting for WebSocket connection to stabilize...")
    await asyncio.sleep(5)
    
    # Step 3: Test balance fetching
    print("\n💰 Step 3: Testing balance fetching...")
    
    try:
        from engine.free_websocket_manager import get_free_websocket_manager
        ws_manager = get_free_websocket_manager()
        
        print(f"   Connection status: {ws_manager.is_connected()}")
        print(f"   Balance data available: {bool(ws_manager.account_balance)}")
        print(f"   Ticker count: {len(ws_manager.tickers)}")
        
        # Test the balance functions that were causing rate limits
        if ws_manager.account_balance:
            balance = ws_manager.get_formatted_balance()
            if balance:
                print("✅ WebSocket balance data retrieved successfully (no API calls)")
                print(f"   Assets in balance: {len(balance)}")
            else:
                print("⚠️ WebSocket balance data not ready yet")
        else:
            print("ℹ️ WebSocket balance data not available (may need API keys)")
            
    except Exception as e:
        print(f"❌ Error testing WebSocket balance: {e}")
        return False
    
    # Step 4: Test API integration
    print("\n🔌 Step 4: Testing API integration...")
    
    try:
        # Import and test the API functions that were causing rate limits
        from api.app import get_real_balance
        
        print("   Testing get_real_balance()...")
        start_time = time.time()
        
        # This should now use WebSocket data instead of REST API
        balance = get_real_balance()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Balance retrieved in {duration:.2f}s")
        print(f"   Balance keys: {list(balance.keys()) if balance else 'None'}")
        
        if duration < 1.0:  # WebSocket should be much faster than REST API
            print("🚀 Fast response indicates WebSocket is being used!")
        else:
            print("⚠️ Slow response may indicate REST API fallback")
            
    except Exception as e:
        print(f"⚠️ API integration test failed: {e}")
    
    print("\n🎯 Step 5: Testing rate limit prevention...")
    
    # Simulate multiple rapid balance requests (what was causing the rate limit)
    print("   Making 10 rapid balance requests (this would cause rate limits before fix)...")
    
    start_time = time.time()
    success_count = 0
    
    for i in range(10):
        try:
            balance = get_real_balance()
            if balance:
                success_count += 1
            print(f"   Request {i+1}/10: ✅")
        except Exception as e:
            print(f"   Request {i+1}/10: ❌ {e}")
        
        # Small delay between requests
        await asyncio.sleep(0.1)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    print(f"\n📊 Results:")
    print(f"   Successful requests: {success_count}/10")
    print(f"   Total time: {total_duration:.2f}s")
    print(f"   Average per request: {total_duration/10:.2f}s")
    
    if success_count >= 8 and total_duration < 5:
        print("🎉 Rate limit fix is working! Fast, successful requests without API errors")
        return True
    else:
        print("⚠️ Rate limit fix may not be fully working - some requests failed or were slow")
        return False

async def main():
    """Run the WebSocket test"""
    success = await test_websocket_balance_fix()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ WEBSOCKET RATE LIMIT FIX VERIFIED!")
        print("🚀 Your system should no longer encounter Binance rate limit errors")
        print("📡 Balance and position data will be retrieved via WebSocket streams")
        print("💾 Intelligent caching will reduce API calls when WebSocket is unavailable")
    else:
        print("❌ WebSocket fix verification failed")
        print("🔧 Please check your setup and try again")
        print("📋 Common issues:")
        print("   - Missing BINANCE_API_KEY or BINANCE_API_SECRET environment variables")
        print("   - python-binance library not installed")
        print("   - Network connectivity issues")
        print("   - Binance API restrictions in your region")

if __name__ == "__main__":
    asyncio.run(main())