#!/usr/bin/env python3
"""
Live Bot Status Checker - Check what the bot is actually doing right now
This script will help us see the real-time status and logs
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

def check_render_app_status():
    """Check if we can determine the Render app URL and status"""
    print("🌐 CHECKING LIVE RENDER DEPLOYMENT")
    print("=" * 50)
    
    # Common Render URL patterns - we'll need the actual URL
    possible_urls = [
        "https://bottie-trading-bot.onrender.com",
        "https://bottie-api.onrender.com", 
        "https://sntax-trading-api.onrender.com",
        "https://bottie.onrender.com"
    ]
    
    print("🔍 Attempting to find your live bot...")
    
    for url in possible_urls:
        try:
            print(f"Trying: {url}")
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                print(f"✅ FOUND LIVE BOT: {url}")
                return url
        except Exception as e:
            print(f"❌ Not found: {str(e)[:50]}...")
    
    print("\n💡 Please provide your Render app URL to check live status")
    print("   Format: https://your-app-name.onrender.com")
    return None

def get_live_bot_status(base_url):
    """Get comprehensive status from live bot"""
    print(f"\n📊 LIVE BOT STATUS CHECK: {base_url}")
    print("=" * 50)
    
    endpoints = [
        ("/health", "System Health"),
        ("/status", "Bot Status"), 
        ("/positions", "Current Positions"),
        ("/signals", "Trading Signals"),
        ("/ml/status", "ML System"),
        ("/trading/status", "Trading Engine"),
        ("/logs", "Recent Logs"),
        ("/pnl/slate", "P&L Summary")
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        try:
            print(f"🔍 Checking {description}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {
                    "status": "✅ SUCCESS",
                    "data": data
                }
                print(f"   ✅ {description}: OK")
            else:
                results[endpoint] = {
                    "status": f"❌ ERROR {response.status_code}",
                    "data": None
                }
                print(f"   ❌ {description}: Error {response.status_code}")
                
        except Exception as e:
            results[endpoint] = {
                "status": f"❌ FAILED: {str(e)[:50]}",
                "data": None
            }
            print(f"   ❌ {description}: {str(e)[:50]}")
    
    return results

def analyze_live_data(results):
    """Analyze the live data and provide insights"""
    print(f"\n🔍 LIVE BOT ANALYSIS")
    print("=" * 50)
    
    # Health Check Analysis
    if "/health" in results and results["/health"]["data"]:
        health = results["/health"]["data"]
        print(f"🏥 SYSTEM HEALTH:")
        print(f"   Status: {'✅ HEALTHY' if health.get('ok') else '❌ UNHEALTHY'}")
        print(f"   Mode: {health.get('mode', 'Unknown')}")
        print(f"   Exchange: {health.get('exchange', 'Unknown')}")
        print(f"   Equity: ${health.get('equity', 0):,.2f}")
        
        features = health.get('features', {})
        for feature, info in features.items():
            status = "✅" if info.get('enabled') else "❌"
            print(f"   {feature}: {status}")
    
    # Trading Status Analysis  
    if "/trading/status" in results and results["/trading/status"]["data"]:
        trading = results["/trading/status"]["data"]
        print(f"\n⚡ TRADING ENGINE:")
        print(f"   Trading Enabled: {'✅' if trading.get('trade_enabled') else '❌'}")
        print(f"   Execution Enabled: {'✅' if trading.get('execution_enabled') else '❌'}")
        print(f"   Recent Signals: {trading.get('recent_signals', 0)}")
        print(f"   Recent Trades: {trading.get('recent_trades', 0)}")
    
    # Positions Analysis
    if "/positions" in results and results["/positions"]["data"]:
        positions_data = results["/positions"]["data"]
        positions = positions_data.get('positions', {})
        print(f"\n💼 CURRENT POSITIONS:")
        if positions:
            for symbol, pos in positions.items():
                pnl = pos.get('pnl', 0)
                pnl_pct = pos.get('pnl_percentage', 0)
                value = pos.get('market_value', 0)
                print(f"   {symbol}: ${value:,.2f} | P&L: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
        else:
            print("   No active positions")
    
    # Signals Analysis
    if "/signals" in results and results["/signals"]["data"]:
        signals_data = results["/signals"]["data"]
        signals = signals_data.get('signals', [])
        print(f"\n🎯 TRADING SIGNALS:")
        if signals:
            for signal in signals[:5]:  # Show first 5
                symbol = signal.get('symbol', 'Unknown')
                signal_type = signal.get('signal', 'HOLD')
                conf = signal.get('conf', 0)
                timestamp = signal.get('t', 0)
                age = int(time.time() - timestamp) if timestamp else 0
                print(f"   {symbol}: {signal_type} (conf: {conf:.1%}, {age}s ago)")
        else:
            print("   No active signals")
    
    # P&L Analysis
    if "/pnl/slate" in results and results["/pnl/slate"]["data"]:
        pnl_data = results["/pnl/slate"]["data"].get('pnl_data', {})
        print(f"\n💰 P&L SUMMARY:")
        print(f"   Total P&L: ${pnl_data.get('total_pnl', 0):+,.2f}")
        print(f"   Realized P&L: ${pnl_data.get('realized_pnl', 0):+,.2f}")
        print(f"   Unrealized P&L: ${pnl_data.get('unrealized_pnl', 0):+,.2f}")
        print(f"   Total Fees: ${pnl_data.get('total_fees_paid', 0):,.2f}")
        print(f"   Win Rate: {pnl_data.get('win_rate', 0):.1f}%")
        print(f"   Total Trades: {pnl_data.get('total_trades', 0)}")
    
    # Logs Analysis
    if "/logs" in results and results["/logs"]["data"]:
        logs_data = results["/logs"]["data"]
        logs = logs_data.get('logs', [])
        print(f"\n📋 RECENT LOGS:")
        if logs:
            for log in logs[-10:]:  # Show last 10 logs
                print(f"   {log}")
        else:
            print("   No recent logs available")

def generate_live_report(results):
    """Generate a comprehensive live report"""
    print(f"\n📊 LIVE BOT REPORT")
    print("=" * 50)
    
    # Count working endpoints
    working = sum(1 for r in results.values() if "✅" in r["status"])
    total = len(results)
    
    print(f"📡 API Endpoints: {working}/{total} working")
    
    # Determine overall status
    if working >= total * 0.8:  # 80% or more working
        overall_status = "✅ OPERATIONAL"
    elif working >= total * 0.5:  # 50% or more working  
        overall_status = "⚠️ PARTIAL"
    else:
        overall_status = "❌ ISSUES"
    
    print(f"🤖 Overall Status: {overall_status}")
    
    # Check for specific issues
    issues = []
    if "/health" in results and "❌" in results["/health"]["status"]:
        issues.append("Health endpoint not responding")
    if "/trading/status" in results and "❌" in results["/trading/status"]["status"]:
        issues.append("Trading engine not accessible")
    if "/positions" in results and "❌" in results["/positions"]["status"]:
        issues.append("Position data not available")
    
    if issues:
        print(f"\n⚠️ DETECTED ISSUES:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print(f"\n✅ NO ISSUES DETECTED")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if overall_status == "✅ OPERATIONAL":
        print("   • Bot is working well - monitor performance")
        print("   • Check P&L regularly for profitability")
        print("   • Review trading signals for accuracy")
    elif overall_status == "⚠️ PARTIAL":
        print("   • Some endpoints have issues - check Render logs")
        print("   • Verify environment variables are set correctly")
        print("   • Check for any deployment errors")
    else:
        print("   • Bot has significant issues - immediate attention needed")
        print("   • Check Render service status and logs")
        print("   • Verify API keys and network connectivity")

def main():
    """Main function to check live bot status"""
    print("🤖 LIVE BOTTIE BOT STATUS CHECKER")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Try to find the live bot
    base_url = check_render_app_status()
    
    if not base_url:
        print("\n❓ MANUAL URL CHECK NEEDED")
        print("Please run this command with your Render URL:")
        print("python3 check_live_bot.py https://your-app.onrender.com")
        return
    
    # Get live status
    results = get_live_bot_status(base_url)
    
    # Analyze the data
    analyze_live_data(results)
    
    # Generate report
    generate_live_report(results)
    
    print(f"\n🔗 Bot Dashboard: {base_url}")
    print(f"📊 Direct Health Check: {base_url}/health")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # URL provided as argument
        url = sys.argv[1].rstrip('/')
        results = get_live_bot_status(url)
        analyze_live_data(results)
        generate_live_report(results)
    else:
        main()