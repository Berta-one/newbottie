#!/usr/bin/env python3
"""
Clear demo data and verify live trading setup
"""
import requests
import json
import time

def check_trading_status():
    """Check if system is really in live trading mode"""
    try:
        # Check health endpoint
        health = requests.get("https://bottie-1.onrender.com/health").json()
        print("🔍 Health Check:")
        print(f"  Mode: {health.get('mode', 'Unknown')}")
        print(f"  Exchange: {health.get('exchange', 'Unknown')}")
        print(f"  Real Trading: {health.get('features', {}).get('real_trading', {}).get('enabled', False)}")
        
        # Check status endpoint for more details
        status = requests.get("https://bottie-1.onrender.com/status").json()
        print(f"\n📊 Status Check:")
        print(f"  Mode: {status.get('mode', 'Unknown')}")
        print(f"  Active Trades: {status.get('active_trades', 0)}")
        print(f"  Total P&L: ${status.get('total_pnl', 0):.2f}")
        
        # Check if we can get recent trades
        trades = requests.get("https://bottie-1.onrender.com/trades?limit=3").json()
        if trades.get('trades'):
            latest_trade = trades['trades'][0]
            trade_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest_trade['timestamp']))
            print(f"\n📈 Latest Trade:")
            print(f"  Time: {trade_time}")
            print(f"  Symbol: {latest_trade['symbol']}")
            print(f"  Side: {latest_trade['side']}")
            print(f"  Quantity: {latest_trade['quantity']}")
            print(f"  Price: ${latest_trade['price']}")
            print(f"  P&L: ${latest_trade['pnl']}")
            print(f"  Trade ID: {latest_trade.get('trade_id', 'N/A')}")
            
        return health, status, trades
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None, None, None

def clear_cached_data():
    """Clear any cached demo data"""
    try:
        # Try to trigger a trades sync
        sync_response = requests.get("https://bottie-1.onrender.com/trades/sync")
        if sync_response.status_code == 200:
            print("✅ Triggered trades sync")
        else:
            print(f"⚠️ Trades sync returned: {sync_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

def verify_binance_connection():
    """Verify if we're actually connected to Binance"""
    try:
        # Check if we can get real account balance
        # This would only work with real API keys
        print("\n🔗 Testing Binance Connection...")
        
        # The trades endpoint should show real trade IDs if connected
        trades = requests.get("https://bottie-1.onrender.com/trades?limit=5").json()
        
        if trades.get('trades'):
            trade_ids = [t.get('trade_id', '') for t in trades['trades'][:3]]
            print(f"📋 Recent Trade IDs: {trade_ids}")
            
            # Real Binance trade IDs are usually numeric
            # Demo trade IDs often have patterns like "T1755608483BTC"
            demo_pattern = any('T1755' in str(tid) for tid in trade_ids)
            
            if demo_pattern:
                print("⚠️ DEMO DATA DETECTED: Trade IDs follow demo pattern")
                print("   Real Binance trade IDs are usually pure numbers")
                print("   This suggests system is generating demo data")
            else:
                print("✅ REAL DATA: Trade IDs look like real Binance trades")
                
        return trades
        
    except Exception as e:
        print(f"❌ Error verifying connection: {e}")
        return None

def main():
    print("🚀 Bottie Trading Diagnostic & Demo Data Cleaner")
    print("=" * 50)
    
    # Check current status
    health, status, trades = check_trading_status()
    
    # Verify connection
    verify_binance_connection()
    
    # Clear cached data
    print("\n🧹 Clearing cached demo data...")
    clear_cached_data()
    
    print("\n" + "=" * 50)
    print("🎯 RECOMMENDATIONS:")
    
    if health and health.get('mode') == 'LIVE':
        print("✅ System reports LIVE mode")
        if trades and trades.get('trades'):
            latest = trades['trades'][0]
            if 'T1755' in str(latest.get('trade_id', '')):
                print("❌ BUT: Trade IDs suggest demo data")
                print("🔧 ACTION: Check Binance API key permissions")
                print("   - Ensure 'Spot Trading' is enabled")
                print("   - Verify API key is for mainnet (not testnet)")
                print("   - Check IP whitelist if enabled")
            else:
                print("✅ Trade IDs look real - check Binance portfolio")
        else:
            print("⚠️ No trades found")
    else:
        print("❌ System not in LIVE mode")
        print("🔧 ACTION: Check LIVE_TRADING_ENABLED environment variable")
    
    print("\n💡 To verify real trading:")
    print("   1. Check your Binance Spot Wallet for recent trades")
    print("   2. Look for trades in the last few hours")
    print("   3. Compare trade times with system logs")

if __name__ == "__main__":
    main()