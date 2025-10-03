#!/usr/bin/env python3
"""
Debug why bot stays in MINIMAL mode despite FORCE_EXECUTION_MODE=1
"""

import requests
import json

def debug_minimal_mode():
    bot_url = "https://bottie-1.onrender.com"
    
    print("🔍 DEBUGGING MINIMAL MODE PERSISTENCE")
    print("=" * 50)
    
    try:
        # Get all status endpoints
        health = requests.get(f"{bot_url}/health", timeout=10).json()
        trading = requests.get(f"{bot_url}/trading/status", timeout=10).json()
        
        print("📊 CURRENT STATUS:")
        print(f"   Health: {health}")
        print(f"   Trading: {trading}")
        
        # Check if the environment variables are actually loaded
        print(f"\n🔍 ENVIRONMENT VARIABLE CHECK:")
        
        # The bot should show different behavior if FORCE_EXECUTION_MODE is set
        if trading.get('mode') == 'MINIMAL':
            print("   ❌ Still in MINIMAL mode")
            print("   💡 This means one of these issues:")
            print("      1. Environment variables not loaded by Render")
            print("      2. Code not checking FORCE_EXECUTION_MODE properly")
            print("      3. Execution loop crashing during startup")
            print("      4. API validation still failing")
        
        # Check if we can see any execution-related info
        try:
            # Try to get more detailed status
            response = requests.get(f"{bot_url}/debug/env", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Environment debug available: {response.json()}")
            else:
                print(f"   ❌ No environment debug endpoint")
        except:
            pass
        
        # Check if there are any startup logs we can access
        try:
            logs = requests.get(f"{bot_url}/logs", timeout=5).json()
            print(f"\n📋 SYSTEM LOGS:")
            for log in logs.get('logs', []):
                print(f"   {log}")
        except Exception as e:
            print(f"   ❌ Cannot access logs: {e}")
        
        # Specific checks for execution mode
        print(f"\n🚨 MINIMAL MODE ROOT CAUSES:")
        
        causes = []
        
        # Check 1: API connection
        balance = health.get('balance', 0)
        if balance == 0:
            causes.append("API connection failed (zero balance)")
        else:
            print(f"   ✅ API connection OK (balance: ${balance:,.2f})")
        
        # Check 2: Trading enabled
        if not trading.get('trading_enabled'):
            causes.append("TRADE_ENABLED not set to 1")
        else:
            print(f"   ✅ Trading enabled: {trading.get('trading_enabled')}")
        
        # Check 3: Mode override
        if trading.get('mode') == 'MINIMAL':
            causes.append("FORCE_EXECUTION_MODE not taking effect")
        
        if causes:
            print(f"\n   🎯 IDENTIFIED ISSUES:")
            for i, cause in enumerate(causes, 1):
                print(f"      {i}. {cause}")
        
        # Generate specific next steps
        print(f"\n🔧 NEXT DEBUGGING STEPS:")
        
        if balance > 0 and trading.get('trading_enabled'):
            print("   1. 🔍 Check Render deployment logs for startup errors")
            print("   2. 🔄 Try manual service restart in Render dashboard")
            print("   3. 🧪 Add DEBUG_MODE=1 to environment variables")
            print("   4. 📊 Check if execution loop is mentioned in startup logs")
        else:
            print("   1. 🔑 Verify API keys are correctly set in Render")
            print("   2. 🌐 Check Render service is using latest environment variables")
            print("   3. 🔄 Force a complete redeploy")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False

if __name__ == "__main__":
    debug_minimal_mode()