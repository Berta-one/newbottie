#!/usr/bin/env python3
"""
Check if execution loop is actually running in the background
"""

import requests
import time
import json

def check_execution_loop():
    bot_url = "https://bottie-1.onrender.com"
    
    print("🔍 CHECKING EXECUTION LOOP STATUS")
    print("=" * 50)
    
    # Check multiple times to see if signals are being processed
    print("📊 Monitoring signal processing over time...")
    
    previous_signals = None
    
    for i in range(3):
        try:
            response = requests.get(f"{bot_url}/signals")
            current_signals = response.json()
            
            signals = current_signals.get("signals", [])
            executable = [s for s in signals if s.get("executable", False)]
            
            print(f"\n⏰ Check {i+1}:")
            print(f"   📡 Total Signals: {len(signals)}")
            print(f"   ⚡ Executable: {len(executable)}")
            print(f"   🕐 Timestamp: {current_signals.get('timestamp', 0)}")
            
            if previous_signals:
                prev_timestamp = previous_signals.get('timestamp', 0)
                curr_timestamp = current_signals.get('timestamp', 0)
                
                if curr_timestamp > prev_timestamp:
                    print(f"   ✅ Signals are being updated")
                else:
                    print(f"   ❌ Signals not updating (stale)")
            
            previous_signals = current_signals
            
            if i < 2:  # Don't sleep on last iteration
                time.sleep(10)  # Wait 10 seconds between checks
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Check if there are any execution-related endpoints
    print(f"\n🔍 CHECKING EXECUTION ENDPOINTS:")
    
    execution_endpoints = [
        "/trading/logs",
        "/execution/status", 
        "/runtime/status",
        "/background/status",
        "/worker/status"
    ]
    
    for endpoint in execution_endpoints:
        try:
            response = requests.get(f"{bot_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {endpoint}: Available")
                data = response.json()
                print(f"      Data: {json.dumps(data, indent=6)[:100]}...")
            elif response.status_code == 404:
                print(f"   ❌ {endpoint}: Not found")
            else:
                print(f"   ⚠️ {endpoint}: HTTP {response.status_code}")
        except:
            print(f"   ❌ {endpoint}: Connection failed")
    
    # Check recent trades to see if anything executed
    print(f"\n💱 CHECKING RECENT TRADE ACTIVITY:")
    
    try:
        trades_response = requests.get(f"{bot_url}/trades")
        trades_data = trades_response.json()
        
        recent_trades = trades_data.get("trades", [])
        print(f"   📊 Total Trades: {len(recent_trades)}")
        
        if recent_trades:
            print("   Recent trades:")
            for trade in recent_trades[-5:]:
                print(f"      {trade}")
        else:
            print("   ❌ No trades found")
            
    except Exception as e:
        print(f"   ❌ Error checking trades: {e}")
    
    # Final diagnosis
    print(f"\n🎯 EXECUTION LOOP DIAGNOSIS:")
    
    issues = []
    
    # Check if signals are stale
    if previous_signals:
        timestamp = previous_signals.get('timestamp', 0)
        current_time = time.time()
        age_minutes = (current_time - timestamp) / 60
        
        if age_minutes > 5:
            issues.append(f"Signals are {age_minutes:.1f} minutes old (should update every 1-2 min)")
    
    # Check execution loop indicators
    if len(executable) > 0:
        issues.append("Executable signals present but no trades executing")
    
    if not issues:
        issues.append("No obvious execution issues detected")
    
    for issue in issues:
        print(f"   • {issue}")
    
    print(f"\n💡 LIKELY CAUSES:")
    print("   1. 🔄 Background execution loop not started")
    print("   2. 🚫 Execution loop crashed or stopped")
    print("   3. 🔒 API permissions insufficient for trading")
    print("   4. ⚙️ Environment variables not properly loaded")
    print("   5. 🌐 Render service configuration issue")
    
    print(f"\n🔧 IMMEDIATE ACTIONS:")
    print("   1. Check Render service logs for execution loop startup")
    print("   2. Restart the Render service to reinitialize loops")
    print("   3. Verify Binance API key has trading permissions")
    print("   4. Check if minimum balance requirements are met")

if __name__ == "__main__":
    check_execution_loop()