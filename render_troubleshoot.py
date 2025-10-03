#!/usr/bin/env python3
"""
Render Troubleshooting Guide
Common issues and solutions for Bottie bot on Render
"""

def print_troubleshooting_guide():
    """Print comprehensive troubleshooting guide"""
    print("🔧 RENDER BOT TROUBLESHOOTING GUIDE")
    print("=" * 50)
    
    print("\n🎯 COMMON ISSUES & SOLUTIONS:")
    
    print("\n1. 🔑 API KEY ISSUES:")
    print("   Problem: Geographic restriction errors")
    print("   Cause: API keys not properly set in Render")
    print("   Solution:")
    print("   • Go to Render Dashboard → Your Service → Environment")
    print("   • Verify these variables exist and have real values:")
    print("     - BINANCE_API_KEY (not 'your_binance_api_key_here')")
    print("     - BINANCE_API_SECRET (not 'your_binance_secret_here')")
    print("     - FINNHUB_API_KEY (optional but recommended)")
    print("   • Redeploy after adding/updating keys")
    
    print("\n2. 🌐 DEPLOYMENT ISSUES:")
    print("   Problem: Bot not starting or crashing")
    print("   Solutions:")
    print("   • Check Render logs for startup errors")
    print("   • Verify all dependencies in requirements.txt")
    print("   • Ensure PORT environment variable is set to 8000")
    print("   • Check if build completed successfully")
    
    print("\n3. ⚡ TRADING NOT EXECUTING:")
    print("   Problem: Signals generated but no trades")
    print("   Solutions:")
    print("   • Set TRADE_ENABLED=1 in environment")
    print("   • Check minimum order size (20 USDT minimum)")
    print("   • Verify account has sufficient balance")
    print("   • Check API key has trading permissions")
    
    print("\n4. 📊 NO DATA/POSITIONS:")
    print("   Problem: Zero equity or no positions showing")
    print("   Solutions:")
    print("   • Verify API keys have 'Reading' permission")
    print("   • Check if API keys are for correct Binance account")
    print("   • Ensure not using testnet keys for live trading")
    print("   • Check IP whitelist if enabled on Binance")
    
    print("\n5. 🚨 SERVICE UNAVAILABLE:")
    print("   Problem: 'Service unavailable from restricted location'")
    print("   Cause: Usually indicates demo/placeholder API keys")
    print("   Solution:")
    print("   • Replace ALL placeholder values with real API keys")
    print("   • Ensure no 'demo_', 'your_', or 'placeholder' values")
    print("   • Redeploy after updating")
    
    print("\n🔍 DIAGNOSTIC STEPS:")
    print("1. Check your Render app URL: https://your-app.onrender.com/health")
    print("2. Look for these in the health response:")
    print("   • 'ok': true")
    print("   • 'mode': 'LIVE' (not 'TESTNET')")
    print("   • 'equity': > 0")
    print("   • 'real_trading': {'enabled': true}")
    
    print("\n📋 RENDER ENVIRONMENT CHECKLIST:")
    env_vars = [
        ("BINANCE_API_KEY", "Your actual Binance API key"),
        ("BINANCE_API_SECRET", "Your actual Binance secret"),
        ("TRADE_ENABLED", "1"),
        ("DEMO_MODE", "0"),
        ("PORT", "8000"),
        ("HOST", "0.0.0.0")
    ]
    
    for var, desc in env_vars:
        print(f"   ☐ {var} = {desc}")
    
    print("\n🎯 QUICK FIXES:")
    print("• If it worked before: Check if environment variables were reset")
    print("• If API errors: Regenerate Binance API keys")
    print("• If no trades: Check TRADE_ENABLED=1 and sufficient balance")
    print("• If crashing: Check Render logs for Python errors")
    
    print("\n📞 GET IMMEDIATE HELP:")
    print("Run this with your Render URL to get specific diagnostics:")
    print("python3 get_render_logs.py https://your-app.onrender.com")

def check_common_render_issues():
    """Check for common Render deployment issues"""
    print("\n🔍 CHECKING COMMON RENDER ISSUES")
    print("=" * 50)
    
    # Check if this looks like a fresh deployment
    import os
    
    issues_found = []
    
    # Check environment variables
    api_key = os.getenv('BINANCE_API_KEY', '')
    if not api_key or 'your_' in api_key or 'demo' in api_key:
        issues_found.append("❌ Binance API key not properly set")
    else:
        print("✅ Binance API key appears to be set")
    
    api_secret = os.getenv('BINANCE_API_SECRET', '')
    if not api_secret or 'your_' in api_secret or 'demo' in api_secret:
        issues_found.append("❌ Binance API secret not properly set")
    else:
        print("✅ Binance API secret appears to be set")
    
    # Check trading configuration
    trade_enabled = os.getenv('TRADE_ENABLED', '0')
    if trade_enabled != '1':
        issues_found.append("⚠️ Trading is disabled (TRADE_ENABLED != 1)")
    else:
        print("✅ Trading is enabled")
    
    demo_mode = os.getenv('DEMO_MODE', '1')
    if demo_mode == '1':
        issues_found.append("⚠️ Demo mode is enabled (set DEMO_MODE=0 for live trading)")
    else:
        print("✅ Demo mode is disabled (live trading)")
    
    if issues_found:
        print(f"\n🚨 ISSUES FOUND:")
        for issue in issues_found:
            print(f"   {issue}")
        print(f"\n💡 These issues likely explain why your bot isn't working properly.")
    else:
        print(f"\n✅ No obvious configuration issues found.")
        print(f"   If bot still not working, check Render logs for runtime errors.")

def main():
    """Main troubleshooting function"""
    print_troubleshooting_guide()
    check_common_render_issues()
    
    print(f"\n🎉 NEXT STEPS:")
    print("1. Check your Render environment variables")
    print("2. Run: python3 get_render_logs.py https://your-app.onrender.com")
    print("3. Review the specific diagnostics and recommendations")
    print("4. Apply the suggested fixes")
    print("5. Redeploy if environment variables were changed")

if __name__ == "__main__":
    main()