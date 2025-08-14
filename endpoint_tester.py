#!/usr/bin/env python3
"""
Comprehensive API endpoint tester for dashboard troubleshooting
"""

import requests
import json
import time
from datetime import datetime

def test_endpoint(endpoint, description):
    """Test a single endpoint and return results"""
    url = f"http://127.0.0.1:8000{endpoint}"
    print(f"\n🔍 Testing: {description}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS - Data received")
                return True, data
            except json.JSONDecodeError:
                print(f"   ❌ INVALID JSON")
                print(f"   Raw response: {response.text[:200]}...")
                return False, None
        else:
            print(f"   ❌ HTTP ERROR: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False, None
            
    except requests.exceptions.ConnectRefusedError:
        print(f"   ❌ CONNECTION REFUSED - Server not running")
        return False, None
    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT - Server took too long")
        return False, None
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False, None

def main():
    print("🧪 COMPREHENSIVE API ENDPOINT TEST")
    print("="*60)
    print(f"Time: {datetime.now()}")
    
    # Wait for server to be ready
    print("\n⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Define all endpoints your dashboard might use
    endpoints = [
        ("/status", "System Status & Equity"),
        ("/account/positions", "Account Positions"),
        ("/account/balance", "Account Balance"),
        ("/market-data", "Market Data"),
        ("/health", "Health Check"),
        ("/", "Root Endpoint"),
        ("/docs", "API Documentation"),
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        success, data = test_endpoint(endpoint, description)
        results[endpoint] = {"success": success, "data": data}
        
        # Show key data for dashboard-critical endpoints
        if success and data:
            if endpoint == "/status":
                equity = data.get('equity', 'MISSING')
                mode = data.get('mode', 'MISSING')
                print(f"     💰 Equity: ${equity}")
                print(f"     🔄 Mode: {mode}")
                
            elif endpoint == "/account/positions":
                active_trades = data.get('active_trades', 'MISSING')
                total_pnl = data.get('total_pnl', 'MISSING')
                print(f"     📊 Active Trades: {active_trades}")
                print(f"     💹 Total PnL: ${total_pnl}")
                
            elif endpoint == "/account/balance":
                if isinstance(data, dict):
                    total_usdt = data.get('total_usdt', 'MISSING')
                    print(f"     💵 Total USDT: ${total_usdt}")
                    
            elif endpoint == "/market-data":
                if isinstance(data, list):
                    print(f"     📈 Market symbols: {len(data)} found")
                elif isinstance(data, dict):
                    print(f"     📈 Market data keys: {list(data.keys())[:3]}...")
    
    # Summary
    print(f"\n📋 ENDPOINT TEST SUMMARY")
    print("="*60)
    
    working_endpoints = []
    failing_endpoints = []
    
    for endpoint, result in results.items():
        if result["success"]:
            working_endpoints.append(endpoint)
            print(f"✅ {endpoint}")
        else:
            failing_endpoints.append(endpoint)
            print(f"❌ {endpoint}")
    
    print(f"\n📊 Results: {len(working_endpoints)}/{len(endpoints)} endpoints working")
    
    if failing_endpoints:
        print(f"\n🚨 DASHBOARD ISSUES - These endpoints are failing:")
        for endpoint in failing_endpoints:
            print(f"   • {endpoint}")
        print(f"\n💡 This explains why your dashboard is missing data!")
    else:
        print(f"\n🎉 All endpoints working! Dashboard should have all data.")
    
    # Test critical data flow
    print(f"\n🔍 CRITICAL DATA FLOW CHECK:")
    if "/status" in working_endpoints:
        status_data = results["/status"]["data"]
        equity = status_data.get('equity')
        if equity and equity > 7000:
            print(f"✅ Real equity available: ${equity:.2f}")
        else:
            print(f"❌ Equity missing or wrong: {equity}")
    
    if "/account/positions" in working_endpoints:
        pos_data = results["/account/positions"]["data"]
        trades = pos_data.get('active_trades', 0)
        if trades > 0:
            print(f"✅ Real positions available: {trades} trades")
        else:
            print(f"⚠️  No active trades shown")

if __name__ == "__main__":
    main()
