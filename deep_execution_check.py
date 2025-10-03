#!/usr/bin/env python3
"""
Deep execution system check - find why execution isn't working
"""

import requests
import json

def deep_execution_check():
    bot_url = "https://bottie-1.onrender.com"
    
    print("🔍 DEEP EXECUTION SYSTEM CHECK")
    print("=" * 50)
    
    # Check all execution-related endpoints
    endpoints_to_check = [
        ("/health", "System Health"),
        ("/trading/status", "Trading Status"),
        ("/ml/status", "ML Status"),
        ("/signals", "Signals"),
        ("/positions", "Positions"),
        ("/trades", "Trades"),
        ("/logs", "System Logs")
    ]
    
    results = {}
    
    for endpoint, name in endpoints_to_check:
        try:
            response = requests.get(f"{bot_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                results[endpoint] = response.json()
                print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {str(e)[:50]}")
    
    # Analyze execution blockages
    print(f"\n🔍 EXECUTION ANALYSIS:")
    
    # Check signals vs execution
    signals_data = results.get("/signals", {})
    trades_data = results.get("/trades", {})
    trading_data = results.get("/trading/status", {})
    
    signals = signals_data.get("signals", [])
    executable_signals = [s for s in signals if s.get("executable", False)]
    total_trades = trades_data.get("summary", {}).get("total_trades", 0)
    
    print(f"   📡 Total Signals: {len(signals)}")
    print(f"   ⚡ Executable Signals: {len(executable_signals)}")
    print(f"   💱 Total Trades: {total_trades}")
    print(f"   🔄 Trading Enabled: {trading_data.get('trading_enabled', False)}")
    print(f"   🎛️ Mode: {trading_data.get('mode', 'Unknown')}")
    
    # Check for specific execution blockers
    print(f"\n🚨 EXECUTION BLOCKERS:")
    
    blockers = []
    
    # Check if execution loop is running
    if len(executable_signals) > 0 and total_trades == 0:
        blockers.append("Execution loop not processing signals")
    
    # Check authentication
    try:
        # Try to access protected endpoint
        auth_response = requests.post(f"{bot_url}/trading/start")
        if auth_response.status_code == 401:
            blockers.append("Authentication required for execution control")
        elif auth_response.status_code == 200:
            print("   ✅ Execution control accessible")
    except:
        blockers.append("Cannot access execution control endpoints")
    
    # Check for minimum order size issues
    if executable_signals:
        for signal in executable_signals[:3]:
            symbol = signal.get("symbol", "")
            price = signal.get("price", 0)
            if price > 0:
                min_order_value = 100  # Assuming 100 USDT per order
                min_quantity = min_order_value / price
                if min_quantity * price < 20:  # Binance minimum
                    blockers.append(f"Order size too small for {symbol}")
    
    # Check balance issues
    health_data = results.get("/health", {})
    balance = health_data.get("balance", 0)
    if balance < 100:  # Minimum for trading
        blockers.append("Insufficient balance for minimum order sizes")
    
    if blockers:
        for i, blocker in enumerate(blockers, 1):
            print(f"   {i}. ❌ {blocker}")
    else:
        print("   ✅ No obvious blockers found")
    
    # Check specific signal details
    print(f"\n🎯 EXECUTABLE SIGNALS ANALYSIS:")
    if executable_signals:
        for i, signal in enumerate(executable_signals[:5], 1):
            symbol = signal.get("symbol", "Unknown")
            signal_type = signal.get("signal", "UNKNOWN")
            conf = signal.get("conf", 0)
            price = signal.get("price", 0)
            executable = signal.get("executable", False)
            
            print(f"   {i}. {symbol}: {signal_type} ({conf:.1%}) - ${price:.2f}")
            print(f"      Executable: {executable}")
            
            # Calculate order value
            order_value = 100  # Default order size
            if price > 0:
                quantity = order_value / price
                print(f"      Est. Order: {quantity:.6f} units = ${order_value:.2f}")
    
    # Generate specific recommendations
    print(f"\n💡 SPECIFIC RECOMMENDATIONS:")
    
    if len(executable_signals) > 0 and total_trades == 0:
        print("   1. 🔧 Check Render service logs for execution errors")
        print("   2. 🔄 Try manual execution restart")
        print("   3. 🔑 Verify API key trading permissions on Binance")
        print("   4. 💰 Check account balance and available funds")
        print("   5. 📊 Verify WebSocket connections are stable")
    
    if trading_data.get("mode") == "MINIMAL":
        print("   6. 🎛️ Check why bot is in MINIMAL mode despite settings")
    
    print("   7. 🌐 Check Render deployment logs for startup errors")
    print("   8. 🔍 Monitor /logs endpoint for real-time execution status")
    
    return results

if __name__ == "__main__":
    deep_execution_check()