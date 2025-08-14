#!/usr/bin/env python3
"""
Direct function testing to identify dashboard data issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.app import *

def test_critical_functions():
    print("🧪 TESTING CRITICAL DASHBOARD FUNCTIONS")
    print("="*60)
    
    # Initialize first
    print("1. Initializing exchange connection...")
    if not initialize_real_exchange():
        print("❌ Exchange initialization failed")
        return
    print("✅ Exchange connected")
    
    # Test balance function
    print("\n2. Testing get_real_balance()...")
    try:
        balance = get_real_balance()
        print(f"✅ Balance function works")
        print(f"   Total USDT: ${balance.get('total_usdt', 'MISSING')}")
        print(f"   Keys count: {len(balance)} currencies")
        if balance.get('total_usdt', 0) > 7000:
            print("   💰 Real equity detected")
        else:
            print("   ⚠️  Equity seems wrong")
    except Exception as e:
        print(f"❌ Balance error: {e}")
    
    # Test positions function  
    print("\n3. Testing get_real_positions()...")
    try:
        positions = get_real_positions()
        print(f"✅ Positions function works")
        print(f"   Total symbols: {len(positions)}")
        
        active_positions = {k: v for k, v in positions.items() if v.get('quantity', 0) > 0}
        print(f"   Active positions: {len(active_positions)}")
        
        if len(active_positions) >= 8:
            print("   📊 Real positions detected")
        else:
            print("   ⚠️  Too few positions")
            
    except Exception as e:
        print(f"❌ Positions error: {e}")
    
    # Test market data function
    print("\n4. Testing get_real_market_data()...")
    try:
        market_data = get_real_market_data()
        print(f"✅ Market data function works")
        print(f"   Data type: {type(market_data)}")
        if isinstance(market_data, list):
            print(f"   Market symbols: {len(market_data)}")
        else:
            print(f"   Data keys: {list(market_data.keys())[:3] if isinstance(market_data, dict) else 'N/A'}")
    except Exception as e:
        print(f"❌ Market data error: {e}")

def simulate_endpoint_responses():
    print("\n🔍 SIMULATING DASHBOARD ENDPOINT RESPONSES")
    print("="*60)
    
    # Simulate /status endpoint
    print("\n📊 /status endpoint response:")
    try:
        balance = get_real_balance()
        response = {
            "status": "UP",
            "ok": True,
            "service": "bottie-real-trading",
            "exchange": "binance",
            "mode": "LIVE" if (exchange_client and not exchange_client.sandbox) else "TESTNET",
            "equity": balance['total_usdt'],
            "features": {
                "real_trading": {"enabled": exchange_client is not None},
                "live_data": {"enabled": True},
                "real_positions": {"enabled": True}
            }
        }
        print(f"   ✅ Status: {response['status']}")
        print(f"   💰 Equity: ${response['equity']:.2f}")
        print(f"   🔄 Mode: {response['mode']}")
        print(f"   🔗 Exchange: {response['exchange']}")
    except Exception as e:
        print(f"   ❌ Status endpoint would fail: {e}")
    
    # Simulate /account/positions endpoint
    print("\n📊 /account/positions endpoint response:")
    try:
        balance = get_real_balance()
        positions = get_real_positions()
        
        total_pnl = 0
        position_details = {}
        
        for symbol, pos in positions.items():
            pnl = 0  # Would need entry prices for real PnL
            position_details[symbol] = {
                "symbol": symbol,
                "quantity": pos.get('quantity', 0),
                "market_value": pos.get('market_value', 0),
                "pnl": pnl,
                "side": pos.get('side', 'LONG')
            }
        
        response = {
            "ok": True,
            "equity": balance['total_usdt'],
            "balance": balance,
            "positions": position_details,
            "total_pnl": total_pnl,
            "active_trades": len([p for p in positions.values() if p.get('quantity', 0) > 0]),
            "mode": "LIVE" if (exchange_client and not exchange_client.sandbox) else "TESTNET"
        }
        
        print(f"   ✅ Active trades: {response['active_trades']}")
        print(f"   💰 Equity: ${response['equity']:.2f}")
        print(f"   📊 Total positions: {len(response['positions'])}")
        print(f"   💹 Total PnL: ${response['total_pnl']}")
        
    except Exception as e:
        print(f"   ❌ Positions endpoint would fail: {e}")
    
    # Simulate /account/balance endpoint
    print("\n📊 /account/balance endpoint response:")
    try:
        balance = get_real_balance()
        print(f"   ✅ Balance keys: {len(balance)} currencies")
        print(f"   💵 Total USDT: ${balance.get('total_usdt', 'MISSING')}")
        
        # Show major holdings
        major_holdings = {k: v for k, v in balance.items() 
                         if k in ['BTC', 'ETH', 'XRP', 'ADA', 'SOL', 'USDT'] and v > 0}
        print(f"   🏆 Major holdings: {list(major_holdings.keys())}")
        
    except Exception as e:
        print(f"   ❌ Balance endpoint would fail: {e}")

def main():
    test_critical_functions()
    simulate_endpoint_responses()
    
    print("\n🎯 DASHBOARD TROUBLESHOOTING SUMMARY")
    print("="*60)
    print("If functions work here but dashboard fails, check:")
    print("1. ❓ Is dashboard pointing to correct API URL (http://127.0.0.1:8000)?")
    print("2. ❓ Are CORS headers properly configured?")
    print("3. ❓ Is dashboard making requests to the right endpoints?")
    print("4. ❓ Are there JavaScript errors in browser console?")
    print("5. ❓ Is the API server staying alive during requests?")

if __name__ == "__main__":
    main()
