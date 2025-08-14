#!/usr/bin/env python3
"""
Test Your Real Binance Account Configuration
Using your exact Render environment variables
"""

import os
import json
import time
from datetime import datetime

# Your exact Render configuration
RENDER_CONFIG = {
    'BINANCE_API_KEY': 'xcZmoQQ2MEe4q3hx1uGBwR9GrfaCPTCIQLdQEWGiABXxsN4t2Z5GfYJUpNopfJGJ',
    'BINANCE_API_SECRET': '4BNmlQr4OvBwbbirXMM8p9LAuBw6JJUOyYD5qNKqSsDiQweFrI8iabWZYajBRRLr',
    'ENVIRONMENT': 'production',
    'EXCHANGE_ID': 'binance',
    'TRADE_ENABLED': '1',
    'TRADE_SYMBOLS': 'BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT',
    'MAX_OPEN_POSITIONS': '15',
    'TRADE_QUOTE_PER_ORDER': '100',
    'ML_ENABLED': '1',
    'QUANTUM_ENABLED': '1',
    'SENTIMENT_ENABLED': '1'
}

def test_binance_connection():
    """Test connection to your real Binance account"""
    print("🔍 Testing Your Real Binance Account Connection")
    print("="*60)
    
    try:
        import ccxt
        
        # Test with your exact API keys
        exchange = ccxt.binance({
            'apiKey': RENDER_CONFIG['BINANCE_API_KEY'],
            'secret': RENDER_CONFIG['BINANCE_API_SECRET'],
            'sandbox': False,  # REAL ACCOUNT
            'enableRateLimit': True,
        })
        
        print("✅ Connecting to LIVE Binance account...")
        
        # Test connection
        exchange.load_markets()
        print("✅ Markets loaded successfully")
        
        # Get account info
        balance = exchange.fetch_balance()
        print("✅ Account balance retrieved")
        
        print("\n💰 YOUR REAL ACCOUNT BALANCE:")
        print("-" * 40)
        
        total_usdt = 0
        asset_count = 0
        
        for currency, amount in balance['total'].items():
            if amount > 0.001:  # Only show significant balances
                asset_count += 1
                try:
                    if currency == 'USDT':
                        usdt_value = amount
                        print(f"   💵 {currency}: ${amount:.2f}")
                    else:
                        ticker = exchange.fetch_ticker(f"{currency}/USDT")
                        usdt_value = amount * ticker['last']
                        print(f"   🪙 {currency}: {amount:.6f} (≈ ${usdt_value:.2f})")
                    total_usdt += usdt_value
                except Exception as e:
                    print(f"   🪙 {currency}: {amount:.6f} (price unavailable)")
        
        print("-" * 40)
        print(f"💎 Total Portfolio Value: ${total_usdt:.2f}")
        print(f"📊 Assets Held: {asset_count}")
        
        # Check open orders
        print("\n📈 OPEN POSITIONS:")
        print("-" * 40)
        open_orders = exchange.fetch_open_orders()
        
        if open_orders:
            print(f"   Active Orders: {len(open_orders)}")
            for order in open_orders[:5]:  # Show first 5
                print(f"   🔄 {order['symbol']}: {order['side']} {order['amount']:.6f} @ ${order['price']:.2f}")
        else:
            print("   No open orders")
        
        # Test your trading symbols
        print(f"\n🎯 TESTING YOUR TRADING SYMBOLS:")
        print("-" * 40)
        symbols = RENDER_CONFIG['TRADE_SYMBOLS'].split(',')
        
        for symbol in symbols:
            try:
                ticker = exchange.fetch_ticker(symbol)
                change = ticker['percentage'] or 0
                trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                print(f"   {symbol}: ${ticker['last']:.4f} {trend} {change:+.1f}%")
            except Exception as e:
                print(f"   {symbol}: Error - {e}")
        
        print(f"\n⚡ CONNECTION STATUS:")
        print(f"   • Account Type: LIVE (Real Money)")
        print(f"   • Exchange: Binance")
        print(f"   • Status: ✅ Connected")
        print(f"   • Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True, total_usdt, asset_count, len(open_orders)
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False, 0, 0, 0

def show_render_activation_steps():
    """Show exact steps to activate live trading on Render"""
    print("\n" + "="*60)
    print("🚀 TO ACTIVATE LIVE TRADING ON RENDER:")
    print("="*60)
    
    print("\n1. 🌐 Go to: https://dashboard.render.com")
    print("2. 📱 Find your Bottie service")
    print("3. ⚙️ Click 'Environment' tab")
    print("4. ➕ Add new variable:")
    print("     Name: LIVE_TRADING_ENABLED")
    print("     Value: true")
    print("5. 💾 Save and redeploy")
    
    print("\n🎉 RESULT:")
    print("Your dashboard will immediately show:")
    print("   • Real account balance")
    print("   • Live trading positions")
    print("   • Actual P&L")
    print("   • Real market data")
    
    print("\n⚠️ IMPORTANT:")
    print("   • This switches from TESTNET to LIVE MONEY")
    print("   • Monitor your positions carefully")
    print("   • Start with small amounts")

def main():
    """Main test function"""
    print("🎯 BOTTIE REAL TRADING ACCOUNT TEST")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test connection
    success, portfolio_value, assets, orders = test_binance_connection()
    
    if success:
        print(f"\n🎉 SUCCESS! Your Binance account is ready for live trading!")
        print(f"   💰 Portfolio: ${portfolio_value:.2f}")
        print(f"   📊 Assets: {assets}")
        print(f"   📈 Open Orders: {orders}")
        
        show_render_activation_steps()
        
        print(f"\n🔗 Your Dashboard: https://helpful-maamoul-8aa9bd.netlify.app")
        
    else:
        print(f"\n❌ Connection failed. Check your API keys.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
