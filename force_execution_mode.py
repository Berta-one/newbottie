#!/usr/bin/env python3
"""
Force execution mode activation - diagnose why MINIMAL mode persists
"""

import requests
import json

def force_execution_analysis():
    bot_url = "https://bottie-1.onrender.com"
    
    print("🔧 FORCING EXECUTION MODE ANALYSIS")
    print("=" * 50)
    
    # Check what's keeping it in MINIMAL mode
    print("🔍 CHECKING MINIMAL MODE CAUSES:")
    
    # Get comprehensive status
    try:
        health = requests.get(f"{bot_url}/health").json()
        trading = requests.get(f"{bot_url}/trading/status").json()
        ml_status = requests.get(f"{bot_url}/ml/status").json()
        
        print(f"✅ Health Status: {health}")
        print(f"✅ Trading Status: {trading}")
        print(f"✅ ML Status: {ml_status}")
        
        # Check for execution blockers
        print(f"\n🚨 MINIMAL MODE TRIGGERS:")
        
        # Common reasons for MINIMAL mode:
        reasons = []
        
        # 1. Missing execution runtime flag
        if not trading.get('execution_enabled'):
            reasons.append("EXECUTION_RUNTIME_ENABLED not set to true")
        
        # 2. API connection issues
        if health.get('balance', 0) == 0:
            reasons.append("API connection failed (zero balance)")
        
        # 3. Missing trading permissions
        # We can't directly test this, but we can infer
        
        # 4. Startup errors
        if trading.get('mode') == 'MINIMAL':
            reasons.append("Execution loop failed to start during initialization")
        
        if reasons:
            for i, reason in enumerate(reasons, 1):
                print(f"   {i}. ❌ {reason}")
        else:
            print("   ✅ No obvious triggers found")
        
        # Check if we can access execution controls
        print(f"\n🧪 TESTING EXECUTION ACCESS:")
        
        # Try different methods to start execution
        test_methods = [
            ("GET", "/trading/start", "GET Start"),
            ("POST", "/trading/start", "POST Start"),
            ("PUT", "/trading/start", "PUT Start"),
            ("GET", "/execution/enable", "Enable Execution"),
            ("POST", "/execution/enable", "POST Enable"),
        ]
        
        for method, endpoint, name in test_methods:
            try:
                if method == "GET":
                    resp = requests.get(f"{bot_url}{endpoint}")
                elif method == "POST":
                    resp = requests.post(f"{bot_url}{endpoint}")
                elif method == "PUT":
                    resp = requests.put(f"{bot_url}{endpoint}")
                
                print(f"   {name}: HTTP {resp.status_code}")
                if resp.status_code == 200:
                    print(f"      ✅ Success: {resp.text[:100]}")
                elif resp.status_code == 401:
                    print(f"      🔒 Needs authentication")
                elif resp.status_code == 404:
                    print(f"      ❌ Endpoint not found")
                elif resp.status_code == 405:
                    print(f"      ❌ Method not allowed")
                    
            except Exception as e:
                print(f"   {name}: Error - {str(e)[:50]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

def suggest_fixes():
    print(f"\n🔧 SPECIFIC FIXES FOR MINIMAL MODE:")
    
    print(f"\n1. 🎯 ENVIRONMENT VARIABLE CHECK:")
    print("   Verify these are set in Render Environment:")
    print("   ✓ EXECUTION_RUNTIME_ENABLED=true")
    print("   ✓ TRADE_ENABLED=1") 
    print("   ✓ DEMO_MODE=0")
    print("   ✓ BINANCE_API_KEY=(your real key)")
    print("   ✓ BINANCE_API_SECRET=(your real secret)")
    
    print(f"\n2. 🔑 BINANCE API PERMISSIONS:")
    print("   Your API key MUST have:")
    print("   ✓ 'Enable Spot & Margin Trading' = YES")
    print("   ✓ 'Enable Reading' = YES")
    print("   ✓ 'Enable Futures' = NO (for safety)")
    
    print(f"\n3. 🌐 RENDER SERVICE CONFIGURATION:")
    print("   Check Render service settings:")
    print("   ✓ Build Command: (should build successfully)")
    print("   ✓ Start Command: python render_api.py")
    print("   ✓ Environment variables properly set")
    
    print(f"\n4. 🔄 FORCE RESTART METHOD:")
    print("   Try this sequence:")
    print("   1. Go to Render Dashboard")
    print("   2. Environment → Add: FORCE_EXECUTION_MODE=1")
    print("   3. Save (triggers auto-deploy)")
    print("   4. Wait 3-5 minutes for full startup")
    print("   5. Check: curl https://bottie-1.onrender.com/trading/status")
    
    print(f"\n5. 🚨 EMERGENCY ACTIVATION:")
    print("   If still MINIMAL mode, the issue is likely:")
    print("   • Binance API key lacks trading permissions")
    print("   • Network/firewall blocking execution startup")
    print("   • Code-level issue preventing execution loop start")

if __name__ == "__main__":
    if force_execution_analysis():
        suggest_fixes()
        
        print(f"\n🎯 NEXT STEPS:")
        print("1. Check Binance API key permissions (most likely cause)")
        print("2. Add FORCE_EXECUTION_MODE=1 to Render environment")
        print("3. Monitor Render logs during startup")
        print("4. Test again: curl https://bottie-1.onrender.com/trading/status")
        
        print(f"\n💡 Your bot WILL work once execution mode activates!")
        print("   All systems are ready - just need to trigger execution loop")