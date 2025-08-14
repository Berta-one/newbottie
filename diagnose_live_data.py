#!/usr/bin/env python3
"""
Diagnostic script to check why real-time data isn't appearing
"""

import requests
import json
from datetime import datetime

def check_render_status():
    """Check current Render deployment status"""
    print("🔍 CHECKING RENDER DEPLOYMENT STATUS")
    print("="*50)
    
    try:
        # Check root endpoint
        response = requests.get("https://bottie-1.onrender.com/")
        root_data = response.json()
        
        print("📊 ROOT ENDPOINT:")
        print(f"   Status: {root_data.get('status', 'unknown')}")
        print(f"   Service: {root_data.get('service', 'unknown')}")
        print(f"   Features: {root_data.get('features', {})}")
        
        # Check if live trading mode is indicated
        if 'mode' in root_data:
            print(f"   Mode: {root_data['mode']}")
        
        # Check status endpoint
        response = requests.get("https://bottie-1.onrender.com/status")
        status_data = response.json()
        
        print("\n💰 STATUS ENDPOINT:")
        print(f"   OK: {status_data.get('ok', False)}")
        print(f"   Equity: ${status_data.get('equity', 0):.2f}")
        print(f"   Positions: {len(status_data.get('positions', {}))}")
        
        if 'mode' in status_data:
            print(f"   Trading Mode: {status_data['mode']}")
        
        # Check grid matrix for data source
        response = requests.get("https://bottie-1.onrender.com/grid/matrix")
        grid_data = response.json()
        
        print("\n📈 MARKET DATA:")
        print(f"   Status: {grid_data.get('status', 'unknown')}")
        print(f"   Data Source: {grid_data.get('data_source', 'unknown')}")
        print(f"   Symbols: {len(grid_data.get('symbols', []))}")
        print(f"   Timestamp: {grid_data.get('timestamp', 0)}")
        
        # Check if we have real market data
        if 'grid' in grid_data and grid_data['grid']:
            first_symbol = grid_data['grid'][0]
            print(f"   Sample Price (BTC): ${first_symbol.get('price', 0)}")
            print(f"   Confidence: {first_symbol.get('confidence', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

def check_real_data_indicators():
    """Check indicators that show if real data is being used"""
    print("\n🔍 CHECKING REAL DATA INDICATORS")
    print("="*50)
    
    try:
        # Check health endpoint
        response = requests.get("https://bottie-1.onrender.com/health")
        health_data = response.json()
        
        print("🏥 HEALTH CHECK:")
        print(f"   Status: {health_data.get('status', 'unknown')}")
        print(f"   Service: {health_data.get('service', 'unknown')}")
        print(f"   Equity: ${health_data.get('equity', 0):.2f}")
        
        if 'mode' in health_data:
            mode = health_data['mode']
            if mode == 'LIVE':
                print("   🔴 MODE: LIVE TRADING")
            elif mode == 'TESTNET':
                print("   🟡 MODE: TESTNET")
            else:
                print(f"   🟢 MODE: {mode}")
        
        features = health_data.get('features', {})
        if features:
            print("   Features:")
            for feature, enabled in features.items():
                status = "✅" if enabled else "❌"
                print(f"     {status} {feature}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        return False

def diagnose_issue():
    """Diagnose why real-time data might not be appearing"""
    print("\n🔧 DIAGNOSIS")
    print("="*50)
    
    # Common issues and solutions
    issues = [
        {
            "issue": "LIVE_TRADING_ENABLED not set",
            "solution": "Add LIVE_TRADING_ENABLED=true to Render environment variables",
            "check": "Check if system shows TESTNET mode"
        },
        {
            "issue": "API keys not working",
            "solution": "Verify Binance API keys are correct and have proper permissions",
            "check": "Check if equity shows realistic values"
        },
        {
            "issue": "Exchange connection failed",
            "solution": "Check API key permissions and IP restrictions",
            "check": "Look for connection errors in logs"
        },
        {
            "issue": "Dashboard caching old data",
            "solution": "Hard refresh dashboard (Ctrl+F5) or clear browser cache",
            "check": "Check if timestamps are recent"
        }
    ]
    
    print("🎯 POSSIBLE ISSUES & SOLUTIONS:")
    for i, item in enumerate(issues, 1):
        print(f"\n{i}. {item['issue']}")
        print(f"   Solution: {item['solution']}")
        print(f"   Check: {item['check']}")

def main():
    """Main diagnostic function"""
    print("🚀 BOTTIE REAL-TIME DATA DIAGNOSTIC")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Check deployment status
    status_ok = check_render_status()
    
    if status_ok:
        # Check health and real data indicators
        health_ok = check_real_data_indicators()
        
        # Provide diagnosis
        diagnose_issue()
        
        print("\n🎯 QUICK FIX:")
        print("1. Go to https://dashboard.render.com")
        print("2. Find your Bottie service")
        print("3. Add environment variable:")
        print("   Name: LIVE_TRADING_ENABLED")
        print("   Value: true")
        print("4. Save and redeploy")
        print("5. Wait 2-3 minutes for deployment")
        print("6. Hard refresh your dashboard (Ctrl+F5)")
        
    else:
        print("\n❌ Cannot connect to Render deployment")
        print("Check if your service is running on Render")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
