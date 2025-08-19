#!/usr/bin/env python3
"""
Enable real trading and clear demo data
"""
import os
import time
import json

def clear_demo_trades():
    """Clear cached demo trades"""
    print("🧹 Clearing demo trades...")
    
    # Check if there's a trades cache file
    cache_files = [
        'trades_history.json',
        'cached_trades.json', 
        'demo_trades.json',
        'trades_cache.json'
    ]
    
    for cache_file in cache_files:
        if os.path.exists(cache_file):
            print(f"📁 Found cache file: {cache_file}")
            try:
                # Backup before clearing
                backup_name = f"{cache_file}.backup.{int(time.time())}"
                os.rename(cache_file, backup_name)
                print(f"✅ Moved {cache_file} to {backup_name}")
            except Exception as e:
                print(f"❌ Error backing up {cache_file}: {e}")
        else:
            print(f"📁 No cache file: {cache_file}")

def check_api_keys():
    """Check if API keys are properly configured"""
    print("\n🔑 Checking API Key Configuration...")
    
    api_key = os.getenv('BINANCE_API_KEY', '')
    secret = os.getenv('BINANCE_SECRET', '')
    live_enabled = os.getenv('LIVE_TRADING_ENABLED', 'false')
    cross_enabled = os.getenv('CROSS_PAIR_ENABLED', 'false')
    
    print(f"LIVE_TRADING_ENABLED: {live_enabled}")
    print(f"CROSS_PAIR_ENABLED: {cross_enabled}")
    print(f"BINANCE_API_KEY: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"BINANCE_SECRET: {'✅ Set' if secret else '❌ Missing'}")
    
    if api_key and len(api_key) > 10:
        print(f"API Key Preview: {api_key[:8]}...{api_key[-4:]}")
    
    return bool(api_key and secret and live_enabled.lower() == 'true')

def restart_trading_system():
    """Instructions to restart the trading system"""
    print("\n🔄 TO RESTART TRADING SYSTEM:")
    print("1. Go to Render Dashboard → bottie-1 service")
    print("2. Click 'Manual Deploy' or restart the service")
    print("3. Check logs for 'LIVE TRADING' initialization")
    print("4. Verify API key connection in startup logs")

def verify_binance_permissions():
    """Instructions to verify Binance API permissions"""
    print("\n🔑 VERIFY BINANCE API PERMISSIONS:")
    print("1. Go to Binance → API Management")
    print("2. Find your API key for this bot")
    print("3. Ensure these permissions are ENABLED:")
    print("   ✅ Read Info")
    print("   ✅ Spot & Margin Trading")
    print("   ✅ Enable Trading (if available)")
    print("4. Check IP Restrictions:")
    print("   - Either disable IP restrictions")
    print("   - Or add Render's IP addresses")
    print("5. Test API key with a simple balance check")

def main():
    print("🚀 Enable Real Trading & Clear Demo Data")
    print("=" * 50)
    
    # Clear demo data
    clear_demo_trades()
    
    # Check API configuration
    api_configured = check_api_keys()
    
    if api_configured:
        print("\n✅ API keys appear to be configured")
        print("🔍 If still seeing demo data, check:")
        print("   1. API key permissions in Binance")
        print("   2. IP whitelist settings")
        print("   3. Render service logs for connection errors")
    else:
        print("\n❌ API keys not properly configured")
        print("🔧 Add these to Render environment:")
        print("   BINANCE_API_KEY=your_key")
        print("   BINANCE_SECRET=your_secret")
        print("   LIVE_TRADING_ENABLED=true")
    
    # Provide instructions
    verify_binance_permissions()
    restart_trading_system()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Verify API permissions in Binance")
    print("2. Restart Render service")
    print("3. Check Render logs for 'LIVE TRADING' confirmation")
    print("4. Monitor your Binance Spot Wallet for new trades")
    print("5. Trade IDs should change from 'T1755...' to pure numbers")

if __name__ == "__main__":
    main()