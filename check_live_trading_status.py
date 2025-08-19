#!/usr/bin/env python3
"""
Check if live trading is actually enabled after API key changes
"""
import requests
import json
import time

def check_trading_mode():
    """Check current trading mode"""
    try:
        print("🔍 Checking trading mode...")
        
        # Check health endpoint
        health = requests.get("https://bottie-1.onrender.com/health", timeout=10).json()
        print(f"Health endpoint mode: {health.get('mode', 'Unknown')}")
        
        # Check status endpoint  
        status = requests.get("https://bottie-1.onrender.com/status", timeout=10).json()
        print(f"Status endpoint mode: {status.get('mode', 'Unknown')}")
        
        # Check recent trades for demo patterns
        trades = requests.get("https://bottie-1.onrender.com/trades?limit=5", timeout=10).json()
        if trades.get('trades'):
            trade_ids = [t.get('trade_id', '') for t in trades['trades'][:3]]
            print(f"Recent trade IDs: {trade_ids}")
            
            demo_pattern = any('T1755' in str(tid) for tid in trade_ids)
            if demo_pattern:
                print("❌ DEMO MODE DETECTED: Trade IDs follow demo pattern")
                print("   Real Binance trade IDs are usually pure numbers")
                return False
            else:
                print("✅ LIVE MODE: Trade IDs look real")
                return True
        else:
            print("⚠️ No trades found")
            return None
            
    except Exception as e:
        print(f"❌ Error checking mode: {e}")
        return None

def check_api_endpoints():
    """Check which API endpoints are working"""
    endpoints = [
        '/health',
        '/status', 
        '/trades',
        '/ml/status',
        '/signals'
    ]
    
    print("\n🔗 Testing API endpoints:")
    working = 0
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"https://bottie-1.onrender.com{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {endpoint}: OK")
                working += 1
            else:
                print(f"   ❌ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   💥 {endpoint}: {e}")
    
    print(f"\n📊 {working}/{len(endpoints)} endpoints working")
    return working

def suggest_actions():
    """Suggest actions to enable live trading"""
    print("\n🛠️ TO ENABLE LIVE TRADING:")
    print("1. Go to Render Dashboard → bottie-1 service")
    print("2. Check Environment variables:")
    print("   ✅ LIVE_TRADING_ENABLED=true")
    print("   ✅ BINANCE_API_KEY=your_key")
    print("   ✅ BINANCE_SECRET=your_secret")
    print("3. Restart the service (Manual Deploy)")
    print("4. Check deployment logs for:")
    print("   ✅ 'LIVE TRADING initialization: LIVE TRADING'")
    print("   ❌ 'API connection failed' or similar errors")
    
    print("\n🔑 BINANCE API KEY CHECKLIST:")
    print("1. Go to Binance → API Management")
    print("2. Ensure permissions:")
    print("   ✅ Read Info")
    print("   ✅ Spot & Margin Trading") 
    print("   ✅ Enable Trading")
    print("3. IP Restrictions:")
    print("   ✅ Either disable IP restrictions")
    print("   ✅ Or whitelist Render's IP addresses")
    
    print("\n🎯 VERIFICATION:")
    print("After restart, trade IDs should change from:")
    print("   ❌ T1755618752ETH (demo pattern)")
    print("   ✅ 123456789 (real Binance trade ID)")

def main():
    print("🚀 Live Trading Status Checker")
    print("=" * 50)
    
    # Check current mode
    is_live = check_trading_mode()
    
    # Check API endpoints
    working_endpoints = check_api_endpoints()
    
    # Provide recommendations
    suggest_actions()
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    
    if is_live:
        print("✅ System appears to be in LIVE mode")
        print("   → Check your Binance Spot Wallet for trades")
    elif is_live is False:
        print("❌ System is in DEMO mode")
        print("   → Need to restart Render service with correct API keys")
    else:
        print("⚠️ Cannot determine trading mode")
        print("   → Check API connectivity")
    
    if working_endpoints >= 3:
        print("✅ API endpoints are healthy")
    else:
        print("❌ API endpoints having issues")

if __name__ == "__main__":
    main()