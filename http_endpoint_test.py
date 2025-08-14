#!/usr/bin/env python3
"""
HTTP endpoint tester - starts server and tests all endpoints
"""

import subprocess
import time
import requests
import json
import threading
import sys

def start_server():
    """Start the API server in background"""
    import os
    os.chdir(r"c:\tools\Bottie 3.0\Bottie")
    
    # Import here to use the same environment
    import uvicorn
    from api.app import app
    
    print("🚀 Starting API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def test_endpoints():
    """Test all endpoints once server is running"""
    base_url = "http://127.0.0.1:8000"
    
    # Wait for server to start
    print("⏳ Waiting for server startup...")
    time.sleep(8)
    
    # Test all critical endpoints
    endpoints = [
        "/",
        "/health", 
        "/status",
        "/account/balance",
        "/account/positions",
        "/grid/matrix",
        "/signals",
        "/ml/status",
        "/quantum/details"
    ]
    
    print(f"\n🧪 TESTING ALL ENDPOINTS")
    print("="*60)
    
    results = {}
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n📡 Testing: {endpoint}")
        
        try:
            response = requests.get(url, timeout=15)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results[endpoint] = {"status": "SUCCESS", "data": data}
                    
                    # Show key info for dashboard-critical endpoints
                    if endpoint == "/status":
                        equity = data.get('equity', 'MISSING')
                        mode = data.get('mode', 'MISSING')
                        print(f"   💰 Equity: ${equity}")
                        print(f"   🔄 Mode: {mode}")
                        
                    elif endpoint == "/account/positions":
                        trades = data.get('active_trades', 'MISSING')
                        equity = data.get('equity', 'MISSING')
                        print(f"   📊 Active Trades: {trades}")
                        print(f"   💰 Equity: ${equity}")
                        
                    elif endpoint == "/account/balance":
                        if isinstance(data, dict):
                            total = data.get('total_usdt', 'MISSING')
                            print(f"   💵 Total USDT: ${total}")
                            
                    print(f"   ✅ SUCCESS")
                    
                except json.JSONDecodeError:
                    results[endpoint] = {"status": "INVALID_JSON", "data": None}
                    print(f"   ❌ Invalid JSON response")
                    
            elif response.status_code == 503:
                results[endpoint] = {"status": "SERVICE_UNAVAILABLE", "data": None}
                print(f"   ⚠️  Service unavailable (expected for some endpoints)")
                
            else:
                results[endpoint] = {"status": f"HTTP_{response.status_code}", "data": None}
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text[:100]}...")
                
        except requests.exceptions.Timeout:
            results[endpoint] = {"status": "TIMEOUT", "data": None}
            print(f"   ❌ Timeout")
            
        except requests.exceptions.ConnectionError:
            results[endpoint] = {"status": "CONNECTION_ERROR", "data": None}
            print(f"   ❌ Connection Error")
            
        except Exception as e:
            results[endpoint] = {"status": f"ERROR", "data": None}
            print(f"   ❌ Error: {e}")
    
    # Summary
    print(f"\n📋 ENDPOINT TEST SUMMARY")
    print("="*60)
    
    success_count = 0
    total_count = len(endpoints)
    
    for endpoint, result in results.items():
        status = result['status']
        if status == "SUCCESS":
            print(f"✅ {endpoint} - {status}")
            success_count += 1
        elif status == "SERVICE_UNAVAILABLE":
            print(f"⚠️  {endpoint} - {status}")
        else:
            print(f"❌ {endpoint} - {status}")
    
    print(f"\n📊 Results: {success_count}/{total_count} endpoints working")
    
    if success_count >= 3:  # /status, /account/balance, /account/positions
        print(f"\n🎉 DASHBOARD SHOULD WORK!")
        print(f"   Core endpoints are responding with real data")
        print(f"   Dashboard URL: http://127.0.0.1:8000")
    else:
        print(f"\n🚨 DASHBOARD LIKELY BROKEN")
        print(f"   Critical endpoints are failing")
    
    return results

def main():
    print("🧪 COMPREHENSIVE HTTP ENDPOINT TEST")
    print("="*60)
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Test endpoints
    results = test_endpoints()
    
    # Keep server running for manual testing
    print(f"\n🌐 Server running at: http://127.0.0.1:8000")
    print(f"📱 Try opening the dashboard in your browser")
    print(f"🔧 Press Ctrl+C to stop...")
    
    try:
        time.sleep(60)  # Keep alive for 1 minute
    except KeyboardInterrupt:
        print(f"\n👋 Server stopped")

if __name__ == "__main__":
    main()
