#!/usr/bin/env python3
"""
Enable Live Trading on Render - Step by Step Guide
"""

import requests
import json
import time
from datetime import datetime

def check_current_status():
    """Check current Render deployment status"""
    print("🔍 CHECKING CURRENT STATUS")
    print("="*50)
    
    try:
        response = requests.get("https://bottie-1.onrender.com/health")
        data = response.json()
        
        print(f"   Status: {data.get('status', 'Unknown')}")
        print(f"   Service: {data.get('service', 'Unknown')}")
        print(f"   Equity: ${data.get('equity', 0):,.2f}")
        print(f"   Exchange: {data.get('exchange', 'Unknown')}")
        
        if data.get('equity', 0) == 10000.0:
            print("   🟡 MODE: TESTNET (Simulated)")
            return False
        else:
            print("   🔴 MODE: LIVE TRADING")
            return True
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def show_render_instructions():
    """Show step-by-step Render instructions"""
    print("\n🚀 ENABLE LIVE TRADING ON RENDER")
    print("="*50)
    
    print("\n📋 STEP-BY-STEP INSTRUCTIONS:")
    print("1. 🌐 Open: https://dashboard.render.com")
    print("2. 🔍 Find your 'Bottie' service")
    print("3. ⚙️ Click 'Environment' tab")
    print("4. ➕ Click 'Add Environment Variable'")
    print("5. 📝 Enter:")
    print("     Name: LIVE_TRADING_ENABLED")
    print("     Value: true")
    print("6. 💾 Click 'Save Changes'")
    print("7. 🔄 Click 'Manual Deploy' or wait for auto-deploy")
    print("8. ⏰ Wait 2-3 minutes for deployment")
    
    print("\n⚠️ IMPORTANT:")
    print("   • This switches from fake money to REAL money")
    print("   • Your dashboard will show actual Binance balance")
    print("   • Monitor your positions carefully")

def test_live_connection():
    """Test what your live connection would look like"""
    print("\n🧪 TESTING YOUR LIVE BINANCE CONNECTION")
    print("="*50)
    
    try:
        import ccxt
        
        # Your actual API keys from the environment variables you showed
        exchange = ccxt.binance({
            'apiKey': 'xcZmoQQ2MEe4q3hx1uGBwR9GrfaCPTCIQLdQEWGiABXxsN4t2Z5GfYJUpNopfJGJ',
            'secret': '4BNmlQr4OvBwbbirXMM8p9LAuBw6JJUOyYD5qNKqSsDiQweFrI8iabWZYajBRRLr',
            'sandbox': False,  # REAL ACCOUNT
            'enableRateLimit': True,
        })
        
        print("✅ Connecting to your REAL Binance account...")
        exchange.load_markets()
        
        # Get your actual balance
        balance = exchange.fetch_balance()
        
        print("\n💰 YOUR REAL ACCOUNT BALANCE:")
        total_usdt = 0
        assets = 0
        
        for currency, amount in balance['total'].items():
            if amount > 0.001:
                assets += 1
                try:
                    if currency == 'USDT':
                        usdt_value = amount
                        print(f"   💵 {currency}: ${amount:.2f}")
                    else:
                        ticker = exchange.fetch_ticker(f"{currency}/USDT")
                        usdt_value = amount * ticker['last']
                        print(f"   🪙 {currency}: {amount:.6f} (≈ ${usdt_value:.2f})")
                    total_usdt += usdt_value
                except:
                    print(f"   🪙 {currency}: {amount:.6f}")
        
        print(f"\n💎 TOTAL PORTFOLIO: ${total_usdt:.2f}")
        print(f"📊 ASSETS: {assets}")
        
        # Check open orders
        orders = exchange.fetch_open_orders()
        print(f"📈 OPEN ORDERS: {len(orders)}")
        
        return total_usdt, assets, len(orders)
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return 0, 0, 0

def wait_for_deployment():
    """Wait for deployment and check when live trading is active"""
    print("\n⏰ WAITING FOR LIVE TRADING ACTIVATION")
    print("="*50)
    
    print("Checking every 30 seconds...")
    
    for i in range(10):  # Check for 5 minutes
        try:
            response = requests.get("https://bottie-1.onrender.com/health")
            data = response.json()
            
            equity = data.get('equity', 0)
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if equity != 10000.0:
                print(f"🎉 [{timestamp}] LIVE TRADING ACTIVATED!")
                print(f"   Real equity: ${equity:,.2f}")
                return True
            else:
                print(f"⏳ [{timestamp}] Still in testnet mode (${equity:,.2f})")
                
        except Exception as e:
            print(f"❌ [{timestamp}] Error checking: {e}")
        
        if i < 9:  # Don't sleep on last iteration
            time.sleep(30)
    
    print("⚠️ Deployment taking longer than expected")
    return False

def fix_dashboard_issues():
    """Fix common dashboard issues"""
    print("\n🔧 FIXING DASHBOARD ISSUES")
    print("="*50)
    
    print("If dashboard still shows simulated data:")
    print("1. 🔄 Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)")
    print("2. 🗑️ Clear browser cache:")
    print("   • Chrome: Settings → Privacy → Clear browsing data")
    print("   • Firefox: Settings → Privacy → Clear Data")
    print("3. 🔗 Check direct API:")
    print("   • https://bottie-1.onrender.com/status")
    print("   • Should show your real equity and positions")
    print("4. 📱 Try different browser or incognito mode")
    
    print("\n📊 Dashboard should show:")
    print("   • Your real Binance balance")
    print("   • Actual open positions")
    print("   • Live market prices")
    print("   • Real P&L calculations")

def main():
    """Main function to enable live trading"""
    print("🚀 ENABLE LIVE TRADING FOR BOTTIE")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Check current status
    is_live = check_current_status()
    
    if is_live:
        print("\n🎉 You're already in LIVE trading mode!")
    else:
        print("\n📝 You're currently in TESTNET mode")
        
        # Test live connection
        portfolio, assets, orders = test_live_connection()
        
        if portfolio > 0:
            print(f"\n✅ Your real account is ready:")
            print(f"   💰 Portfolio: ${portfolio:.2f}")
            print(f"   📊 Assets: {assets}")
            print(f"   📈 Orders: {orders}")
        
        # Show instructions
        show_render_instructions()
        
        # Ask if they want to wait for deployment
        print(f"\n🤔 After you enable LIVE_TRADING_ENABLED on Render:")
        print("1. Type 'y' to wait and monitor deployment")
        print("2. Type 'n' to continue manually")
        
        choice = input("\nWait for deployment? (y/n): ").lower().strip()
        
        if choice == 'y':
            print("\n⏰ Monitoring deployment...")
            success = wait_for_deployment()
            
            if success:
                print("\n🎉 SUCCESS! Live trading is now active!")
            else:
                print("\n⚠️ Please check Render dashboard manually")
    
    # Show dashboard fix instructions
    fix_dashboard_issues()
    
    print(f"\n🔗 Your Dashboard: https://helpful-maamoul-8aa9bd.netlify.app")
    print("="*60)

if __name__ == "__main__":
    main()
