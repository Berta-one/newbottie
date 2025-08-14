#!/usr/bin/env python3
"""
Real Trading Demo - Shows your actual positions and balance
"""

import os
import time
import ccxt
from dotenv import load_dotenv

def demo_real_account():
    print("\n🚀 BOTTIE REAL TRADING DEMO")
    print("="*50)
    
    # For demo purposes, we'll use environment variables
    # In production, you'd set these in your .env file
    
    print("📋 To connect to your real Binance account:")
    print("1. Go to https://www.binance.com/en/my/settings/api-management")
    print("2. Create API key with 'Spot & Margin Trading' enabled")
    print("3. Add keys to environment or .env file")
    print("4. Set LIVE_TRADING_ENABLED=true when ready")
    
    # Check if environment variables are set
    api_key = os.getenv('BINANCE_API_KEY', '')
    secret = os.getenv('BINANCE_SECRET', '')
    live_mode = os.getenv('LIVE_TRADING_ENABLED', 'false').lower() == 'true'
    
    if not api_key or not secret:
        print("\n⚠️  Demo Mode: No API keys configured")
        print("   Add BINANCE_API_KEY and BINANCE_SECRET to connect to real account")
        demo_simulated_data()
        return
    
    try:
        # Initialize exchange
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'sandbox': not live_mode,  # Use testnet unless live_mode is True
            'enableRateLimit': True,
        })
        
        exchange.load_markets()
        
        mode = "🔴 LIVE TRADING" if live_mode else "🟡 TESTNET"
        print(f"\n✅ Connected to Binance: {mode}")
        
        # Get account balance
        print("\n💰 ACCOUNT BALANCE:")
        balance = exchange.fetch_balance()
        total_usdt = 0
        
        for currency, amount in balance['total'].items():
            if amount > 0.001:  # Only show significant balances
                try:
                    if currency == 'USDT':
                        usdt_value = amount
                        print(f"   {currency}: {amount:.2f} USDT")
                    else:
                        ticker = exchange.fetch_ticker(f"{currency}/USDT")
                        usdt_value = amount * ticker['last']
                        print(f"   {currency}: {amount:.6f} (≈ ${usdt_value:.2f})")
                    total_usdt += usdt_value
                except:
                    print(f"   {currency}: {amount:.6f}")
        
        print(f"\n💵 Total Portfolio Value: ${total_usdt:.2f}")
        
        # Get open positions/orders
        print("\n📈 OPEN POSITIONS:")
        open_orders = exchange.fetch_open_orders()
        
        if open_orders:
            for order in open_orders:
                print(f"   {order['symbol']}: {order['side']} {order['amount']:.6f} @ ${order['price']:.2f}")
        else:
            print("   No open orders")
        
        # Get recent trades
        print("\n📊 PORTFOLIO BREAKDOWN:")
        for currency, amount in balance['total'].items():
            if amount > 0.001 and currency != 'USDT':
                try:
                    ticker = exchange.fetch_ticker(f"{currency}/USDT")
                    price = ticker['last']
                    change_24h = ticker['percentage'] or 0
                    value = amount * price
                    
                    status = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
                    print(f"   {currency}: {amount:.6f} @ ${price:.4f} {status} {change_24h:+.1f}% = ${value:.2f}")
                except:
                    pass
        
        # Show market data quality
        print(f"\n⚡ LIVE MARKET DATA:")
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        for symbol in symbols:
            try:
                ticker = exchange.fetch_ticker(symbol)
                change = ticker['percentage'] or 0
                trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                print(f"   {symbol}: ${ticker['last']:.2f} {trend} {change:+.1f}%")
            except:
                pass
        
        print(f"\n🕐 Last Updated: {time.strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        print("   Falling back to demo mode...")
        demo_simulated_data()

def demo_simulated_data():
    """Show what the real data would look like"""
    print("\n🎯 SIMULATED REAL DATA PREVIEW:")
    print("   (This is what your real account data would look like)")
    
    print("\n💰 EXAMPLE BALANCE:")
    print("   USDT: 8,234.56 USDT")
    print("   BTC: 0.15432100 (≈ $6,750.23)")
    print("   ETH: 2.45000000 (≈ $6,487.50)")
    print("   BNB: 15.50000000 (≈ $4,325.75)")
    print("\n💵 Total Portfolio Value: $25,798.04")
    
    print("\n📈 EXAMPLE POSITIONS:")
    print("   BTCUSDT: LONG 0.05 @ $43,750.00")
    print("   ETHUSDT: LONG 1.0 @ $2,650.00")
    
    print("\n📊 LIVE MARKET PREVIEW:")
    market_data = [
        ("BTCUSDT", 43750.23, +2.1),
        ("ETHUSDT", 2649.87, +1.8),
        ("BNBUSDT", 279.34, -0.5),
        ("ADAUSDT", 0.5234, +3.2),
    ]
    
    for symbol, price, change in market_data:
        trend = "📈" if change > 0 else "📉"
        print(f"   {symbol}: ${price:.2f} {trend} {change:+.1f}%")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv('.env.real', override=True)
    
    demo_real_account()
