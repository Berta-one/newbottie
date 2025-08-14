#!/usr/bin/env python3
"""
Render Live Trading Deployment Script
Configures Bottie for real trading using existing Render environment variables
"""

import os
import json
import time
from typing import Dict, Any

def check_render_environment():
    """Check if we're running on Render with the required environment variables"""
    render_vars = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET'
    ]
    
    print("🔍 Checking Render Environment Variables...")
    
    missing_vars = []
    for var in render_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * (len(os.getenv(var, '')) - 4)}{os.getenv(var, '')[-4:]}")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    print("✅ All required environment variables found!")
    return True

def get_trading_mode():
    """Determine current trading mode"""
    live_trading = os.getenv('LIVE_TRADING_ENABLED', 'false').lower() == 'true'
    
    if live_trading:
        return "🔴 LIVE TRADING (Real Money)"
    else:
        return "🟡 TESTNET MODE (Safe Testing)"

def display_render_status():
    """Display current Render deployment status"""
    print("\n" + "="*60)
    print("🚀 BOTTIE RENDER DEPLOYMENT STATUS")
    print("="*60)
    
    # Check environment
    env_ready = check_render_environment()
    
    # Trading mode
    mode = get_trading_mode()
    print(f"\n📊 Trading Mode: {mode}")
    
    # Render info
    render_url = os.getenv('RENDER_EXTERNAL_URL', 'https://bottie-1.onrender.com')
    print(f"🌐 Render URL: {render_url}")
    
    # Dashboard info
    dashboard_url = "https://helpful-maamoul-8aa9bd.netlify.app"
    print(f"📱 Dashboard: {dashboard_url}")
    
    print("\n📋 CURRENT CONFIGURATION:")
    print(f"   • API Keys: {'✅ Configured' if env_ready else '❌ Missing'}")
    print(f"   • Live Trading: {'🔴 ENABLED' if os.getenv('LIVE_TRADING_ENABLED') == 'true' else '🟡 DISABLED'}")
    print(f"   • Exchange: Binance")
    print(f"   • Mode: {'Live Account' if os.getenv('LIVE_TRADING_ENABLED') == 'true' else 'Testnet'}")
    
    return env_ready

def enable_live_trading():
    """Instructions for enabling live trading on Render"""
    print("\n" + "="*60)
    print("🔴 ENABLE LIVE TRADING ON RENDER")
    print("="*60)
    
    print("To enable REAL trading with your existing Render API keys:")
    print("\n1. 🌐 Go to your Render Dashboard:")
    print("   https://dashboard.render.com")
    
    print("\n2. 📝 Add Environment Variable:")
    print("   Variable: LIVE_TRADING_ENABLED")
    print("   Value: true")
    
    print("\n3. 🔄 Redeploy your service")
    
    print("\n4. ✅ Your dashboard will show:")
    print("   • Real account balance")
    print("   • Actual trading positions")
    print("   • Live market prices")
    print("   • Real P&L calculations")
    
    print("\n⚠️  WARNING:")
    print("   • This enables REAL trading with REAL money")
    print("   • Monitor your positions carefully")
    print("   • Start with small amounts")
    
    print("\n🛡️  SAFETY FEATURES ACTIVE:")
    print("   • 1% risk per trade limit")
    print("   • Maximum 3 concurrent positions")
    print("   • 3% automatic stop loss")
    print("   • 5% daily loss limit")

def test_api_connection():
    """Test the API connection with current settings"""
    print("\n🧪 Testing API Connection...")
    
    try:
        if os.getenv('BINANCE_API_KEY') and os.getenv('BINANCE_SECRET'):
            import ccxt
            
            # Test with current settings
            use_live = os.getenv('LIVE_TRADING_ENABLED', 'false').lower() == 'true'
            
            exchange = ccxt.binance({
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET'),
                'sandbox': not use_live,
                'enableRateLimit': True,
            })
            
            # Test connection
            exchange.load_markets()
            
            mode = "LIVE" if use_live else "TESTNET"
            print(f"✅ Connection successful: {mode} mode")
            
            # Get balance
            balance = exchange.fetch_balance()
            total_usdt = balance['total'].get('USDT', 0)
            
            print(f"💰 Account Balance Preview:")
            for currency, amount in balance['total'].items():
                if amount > 0.001:
                    if currency == 'USDT':
                        print(f"   {currency}: ${amount:.2f}")
                    else:
                        try:
                            ticker = exchange.fetch_ticker(f"{currency}/USDT")
                            value = amount * ticker['last']
                            print(f"   {currency}: {amount:.6f} (≈ ${value:.2f})")
                            total_usdt += value
                        except:
                            print(f"   {currency}: {amount:.6f}")
            
            print(f"\n💵 Total Portfolio: ≈ ${total_usdt:.2f}")
            return True
            
        else:
            print("❌ API keys not configured")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Main deployment status check"""
    print("🚀 Bottie Real Trading - Render Deployment Check")
    
    # Display current status
    env_ready = display_render_status()
    
    if env_ready:
        # Test connection
        connection_ok = test_api_connection()
        
        if connection_ok:
            print("\n🎉 SUCCESS: Ready for real trading!")
            
            if os.getenv('LIVE_TRADING_ENABLED', 'false').lower() != 'true':
                print("\n📋 To enable live trading:")
                enable_live_trading()
            else:
                print("\n🔴 LIVE TRADING IS ACTIVE!")
                print("   Monitor your dashboard: https://helpful-maamoul-8aa9bd.netlify.app")
        else:
            print("\n❌ Connection test failed")
    else:
        print("\n❌ Environment not ready")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
