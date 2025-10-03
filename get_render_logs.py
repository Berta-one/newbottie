#!/usr/bin/env python3
"""
Render Log Analyzer - Get logs and status from your Render deployment
This script helps analyze what your bot is actually doing in production
"""

import sys
import requests
import json
from datetime import datetime

def check_bot_with_url(base_url):
    """Check bot status with provided URL"""
    print(f"🔍 CHECKING LIVE BOT: {base_url}")
    print("=" * 60)
    
    # Remove trailing slash
    base_url = base_url.rstrip('/')
    
    # Test basic connectivity first
    try:
        print("🌐 Testing basic connectivity...")
        response = requests.get(base_url, timeout=10)
        print(f"✅ Base URL responds: {response.status_code}")
    except Exception as e:
        print(f"❌ Base URL error: {e}")
        return False
    
    # Check critical endpoints
    critical_endpoints = [
        ("/health", "System Health"),
        ("/status", "Bot Status"),
        ("/trading/status", "Trading Status"),
        ("/logs", "System Logs")
    ]
    
    results = {}
    
    for endpoint, name in critical_endpoints:
        try:
            print(f"\n🔍 Checking {name} ({endpoint})...")
            response = requests.get(f"{base_url}{endpoint}", timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results[endpoint] = data
                    print(f"✅ {name}: SUCCESS")
                    
                    # Show key info immediately
                    if endpoint == "/health":
                        print(f"   Mode: {data.get('mode', 'Unknown')}")
                        print(f"   Exchange: {data.get('exchange', 'Unknown')}")
                        print(f"   Equity: ${data.get('equity', 0):,.2f}")
                        features = data.get('features', {})
                        for feature, info in features.items():
                            status = "✅" if info.get('enabled') else "❌"
                            print(f"   {feature}: {status}")
                    
                    elif endpoint == "/trading/status":
                        print(f"   Trade Enabled: {data.get('trade_enabled')}")
                        print(f"   Execution Enabled: {data.get('execution_enabled')}")
                        print(f"   Recent Signals: {data.get('recent_signals', 0)}")
                        print(f"   Recent Trades: {data.get('recent_trades', 0)}")
                    
                    elif endpoint == "/logs":
                        logs = data.get('logs', [])
                        print(f"   Available Logs: {len(logs)}")
                        if logs:
                            print("   Recent logs:")
                            for log in logs[-5:]:  # Show last 5 logs
                                print(f"     {log}")
                
                except json.JSONDecodeError:
                    print(f"⚠️ {name}: Response not JSON")
                    results[endpoint] = {"raw_response": response.text[:200]}
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                results[endpoint] = {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ {name}: {str(e)[:50]}...")
            results[endpoint] = {"error": str(e)}
    
    return results

def analyze_bot_status(results):
    """Analyze the bot status and provide insights"""
    print(f"\n📊 BOT ANALYSIS")
    print("=" * 60)
    
    # Health Analysis
    if "/health" in results and isinstance(results["/health"], dict):
        health = results["/health"]
        print(f"🏥 SYSTEM HEALTH:")
        
        if health.get('ok'):
            print("   ✅ System is healthy")
        else:
            print("   ❌ System has issues")
        
        mode = health.get('mode', 'Unknown')
        if mode == "LIVE":
            print("   ✅ Running in LIVE mode")
        elif mode == "TESTNET":
            print("   ⚠️ Running in TESTNET mode")
        else:
            print(f"   ❓ Mode: {mode}")
        
        equity = health.get('equity', 0)
        if equity > 0:
            print(f"   💰 Account Equity: ${equity:,.2f}")
        else:
            print("   ⚠️ No equity detected - check API connection")
    
    # Trading Analysis
    if "/trading/status" in results and isinstance(results["/trading/status"], dict):
        trading = results["/trading/status"]
        print(f"\n⚡ TRADING ENGINE:")
        
        if trading.get('trade_enabled'):
            print("   ✅ Trading is enabled")
        else:
            print("   ❌ Trading is disabled")
        
        if trading.get('execution_enabled'):
            print("   ✅ Execution is enabled")
        else:
            print("   ❌ Execution is disabled")
        
        signals = trading.get('recent_signals', 0)
        trades = trading.get('recent_trades', 0)
        
        print(f"   📡 Recent Signals: {signals}")
        print(f"   💱 Recent Trades: {trades}")
        
        if signals > 0 and trades == 0:
            print("   ⚠️ Signals generated but no trades executed")
        elif signals > 0 and trades > 0:
            print("   ✅ Bot is actively trading")
        elif signals == 0:
            print("   ⚠️ No signals being generated")
    
    # Log Analysis
    if "/logs" in results and isinstance(results["/logs"], dict):
        logs = results["/logs"].get('logs', [])
        print(f"\n📋 LOG ANALYSIS:")
        
        if logs:
            print(f"   📝 Total Logs: {len(logs)}")
            
            # Look for specific patterns
            error_logs = [log for log in logs if 'ERROR' in log or '❌' in log]
            warning_logs = [log for log in logs if 'WARNING' in log or '⚠️' in log]
            success_logs = [log for log in logs if 'SUCCESS' in log or '✅' in log]
            
            print(f"   ❌ Errors: {len(error_logs)}")
            print(f"   ⚠️ Warnings: {len(warning_logs)}")
            print(f"   ✅ Success: {len(success_logs)}")
            
            if error_logs:
                print("   Recent errors:")
                for error in error_logs[-3:]:
                    print(f"     {error}")
            
            if warning_logs:
                print("   Recent warnings:")
                for warning in warning_logs[-3:]:
                    print(f"     {warning}")
        else:
            print("   ⚠️ No logs available")

def generate_recommendations(results):
    """Generate specific recommendations based on status"""
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 60)
    
    health = results.get("/health", {})
    trading = results.get("/trading/status", {})
    
    recommendations = []
    
    # Check if bot is working
    if not health.get('ok'):
        recommendations.append("🚨 CRITICAL: System health check failing - check Render logs immediately")
    
    # Check API connection
    equity = health.get('equity', 0)
    if equity == 0:
        recommendations.append("🔑 API Connection: Check if Binance API keys are correctly set in Render environment")
    
    # Check trading status
    if not trading.get('trade_enabled'):
        recommendations.append("⚡ Trading: Set TRADE_ENABLED=1 in Render environment variables")
    
    if not trading.get('execution_enabled'):
        recommendations.append("🔧 Execution: Trading execution is disabled - check bot logs for reason")
    
    # Check activity
    signals = trading.get('recent_signals', 0)
    trades = trading.get('recent_trades', 0)
    
    if signals == 0:
        recommendations.append("📡 Signals: No signals being generated - check ML system and market data")
    
    if signals > 0 and trades == 0:
        recommendations.append("💱 Trades: Signals present but no trades executing - check minimum order sizes and balance")
    
    # Check mode
    mode = health.get('mode', '')
    if mode == "TESTNET":
        recommendations.append("🌐 Mode: Bot is in testnet mode - set DEMO_MODE=0 for live trading")
    
    if not recommendations:
        recommendations.append("✅ Bot appears to be working correctly - monitor performance")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

def main():
    """Main function"""
    print("🤖 RENDER BOT LOG ANALYZER")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    if len(sys.argv) < 2:
        print("\n❓ USAGE:")
        print("python3 get_render_logs.py https://your-app.onrender.com")
        print("\nTo find your Render URL:")
        print("1. Go to your Render dashboard")
        print("2. Click on your bot service")
        print("3. Copy the URL (e.g., https://your-app-name.onrender.com)")
        return
    
    bot_url = sys.argv[1]
    
    # Check the bot
    results = check_bot_with_url(bot_url)
    
    if results:
        # Analyze results
        analyze_bot_status(results)
        
        # Generate recommendations
        generate_recommendations(results)
        
        print(f"\n🔗 QUICK ACCESS LINKS:")
        print(f"Dashboard: {bot_url}")
        print(f"Health: {bot_url}/health")
        print(f"Status: {bot_url}/status")
        print(f"Signals: {bot_url}/signals")
        print(f"Logs: {bot_url}/logs")
        
    else:
        print("\n❌ Could not connect to bot - check URL and deployment status")

if __name__ == "__main__":
    main()