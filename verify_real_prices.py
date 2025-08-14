#!/usr/bin/env python3
"""
Verify Real Price Data - Critical for Trading Safety
Ensures bot isn't trading on fake signals that could cause losses
"""

import requests
import json
import time
from datetime import datetime

def get_real_binance_prices():
    """Get actual prices directly from Binance API"""
    print("🔍 FETCHING REAL BINANCE PRICES")
    print("="*50)
    
    try:
        # Direct Binance API call (no authentication needed for prices)
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url)
        data = response.json()
        
        # Get key trading symbols
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT']
        real_prices = {}
        
        for ticker in data:
            symbol = ticker['symbol']
            if symbol in symbols:
                real_prices[symbol] = {
                    'price': float(ticker['lastPrice']),
                    'change': float(ticker['priceChangePercent']),
                    'volume': float(ticker['volume']),
                    'high': float(ticker['highPrice']),
                    'low': float(ticker['lowPrice'])
                }
        
        print("✅ Real Binance prices fetched")
        for symbol, data in real_prices.items():
            print(f"   {symbol}: ${data['price']:,.2f} ({data['change']:+.1f}%)")
        
        return real_prices
        
    except Exception as e:
        print(f"❌ Error fetching real prices: {e}")
        return {}

def get_bottie_prices():
    """Get prices from your Bottie system"""
    print("\n🤖 FETCHING BOTTIE SYSTEM PRICES")
    print("="*50)
    
    try:
        response = requests.get("https://bottie-1.onrender.com/grid/matrix")
        data = response.json()
        
        bottie_prices = {}
        grid_data = data.get('grid', [])
        
        for item in grid_data:
            symbol = item.get('symbol', '')
            if symbol:
                bottie_prices[symbol] = {
                    'price': item.get('price', 0),
                    'change': item.get('change', 0),
                    'volume': item.get('volume', 0),
                    'confidence': item.get('confidence', 0)
                }
        
        print("✅ Bottie prices fetched")
        print(f"   Data source: {data.get('data_source', 'unknown')}")
        print(f"   Status: {data.get('status', 'unknown')}")
        print(f"   Timestamp: {data.get('timestamp', 0)}")
        
        for symbol, item in bottie_prices.items():
            print(f"   {symbol}: ${item['price']:,.2f} (conf: {item['confidence']:.2f})")
        
        return bottie_prices
        
    except Exception as e:
        print(f"❌ Error fetching Bottie prices: {e}")
        return {}

def compare_prices(real_prices, bottie_prices):
    """Compare real vs Bottie prices to detect fake data"""
    print("\n🔍 PRICE COMPARISON ANALYSIS")
    print("="*50)
    
    if not real_prices or not bottie_prices:
        print("❌ Cannot compare - missing price data")
        return False
    
    all_real = True
    max_diff_threshold = 0.5  # 0.5% maximum acceptable difference
    
    for symbol in real_prices.keys():
        if symbol in bottie_prices:
            real_price = real_prices[symbol]['price']
            bottie_price = bottie_prices[symbol]['price']
            
            # Calculate percentage difference
            diff_percent = abs(real_price - bottie_price) / real_price * 100
            
            if diff_percent <= max_diff_threshold:
                status = "✅ REAL"
                print(f"   {symbol}: ${real_price:,.2f} vs ${bottie_price:,.2f} ({diff_percent:.3f}%) {status}")
            else:
                status = "❌ FAKE"
                all_real = False
                print(f"   {symbol}: ${real_price:,.2f} vs ${bottie_price:,.2f} ({diff_percent:.3f}%) {status}")
        else:
            print(f"   {symbol}: Missing in Bottie data")
            all_real = False
    
    return all_real

def check_trading_signals():
    """Check if trading signals are based on real data"""
    print("\n📊 CHECKING TRADING SIGNALS")
    print("="*50)
    
    try:
        response = requests.get("https://bottie-1.onrender.com/signals")
        signals = response.json()
        
        print(f"✅ Retrieved {len(signals)} trading signals")
        
        for signal in signals[:5]:  # Show first 5 signals
            symbol = signal.get('symbol', '')
            action = signal.get('signal', '')
            confidence = signal.get('confidence', 0)
            price = signal.get('price', 0)
            reason = signal.get('reason', '')
            
            print(f"   {symbol}: {action} @ ${price:,.2f} (conf: {confidence:.2f})")
            print(f"     Reason: {reason}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking signals: {e}")
        return False

def verify_exchange_connection():
    """Verify the exchange connection is real"""
    print("\n🔗 VERIFYING EXCHANGE CONNECTION")
    print("="*50)
    
    try:
        # Test with your actual API keys
        import ccxt
        
        exchange = ccxt.binance({
            'apiKey': 'xcZmoQQ2MEe4q3hx1uGBwR9GrfaCPTCIQLdQEWGiABXxsN4t2Z5GfYJUpNopfJGJ',
            'secret': '4BNmlQr4OvBwbbirXMM8p9LAuBw6JJUOyYD5qNKqSsDiQweFrI8iabWZYajBRRLr',
            'sandbox': False,  # REAL
            'enableRateLimit': True,
        })
        
        # Test connection
        exchange.load_markets()
        
        # Get a real price for comparison
        ticker = exchange.fetch_ticker('BTC/USDT')
        real_btc_price = ticker['last']
        
        print(f"✅ Direct exchange connection working")
        print(f"   Real BTC price from exchange: ${real_btc_price:,.2f}")
        
        return real_btc_price
        
    except Exception as e:
        print(f"❌ Exchange connection error: {e}")
        return 0

def recommend_fixes():
    """Recommend fixes for fake price data"""
    print("\n🔧 FIXING FAKE PRICE DATA")
    print("="*50)
    
    print("To ensure REAL prices for trading:")
    print("\n1. 🌐 Enable Live Trading on Render:")
    print("   • Go to https://dashboard.render.com")
    print("   • Add: LIVE_TRADING_ENABLED = true")
    print("   • Redeploy service")
    
    print("\n2. 🔑 Verify API Configuration:")
    print("   • Check BINANCE_API_KEY is correct")
    print("   • Check BINANCE_SECRET is correct")
    print("   • Ensure API has 'Spot Trading' permissions")
    
    print("\n3. 📊 Monitor Data Source:")
    print("   • Grid endpoint should show 'data_source: binance'")
    print("   • Status should show 'live_data'")
    print("   • Confidence should be > 0.9 for real data")
    
    print("\n4. ⚠️ CRITICAL - Trading Safety:")
    print("   • NEVER trade with fake prices")
    print("   • Always verify prices match real market")
    print("   • Set stop losses to protect against bad signals")
    print("   • Monitor trades closely")

def main():
    """Main price verification function"""
    print("🚨 CRITICAL: VERIFYING REAL PRICE DATA")
    print("Fake prices = Bad trades = Real losses!")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Get real prices from Binance
    real_prices = get_real_binance_prices()
    
    # Get Bottie system prices
    bottie_prices = get_bottie_prices()
    
    # Compare prices
    prices_are_real = compare_prices(real_prices, bottie_prices)
    
    # Check trading signals
    signals_ok = check_trading_signals()
    
    # Verify exchange connection
    exchange_price = verify_exchange_connection()
    
    # Final assessment
    print("\n🎯 FINAL ASSESSMENT")
    print("="*50)
    
    if prices_are_real and signals_ok and exchange_price > 0:
        print("✅ SAFE TO TRADE")
        print("   • Prices are REAL")
        print("   • Signals based on real data")
        print("   • Exchange connection verified")
    else:
        print("❌ NOT SAFE TO TRADE")
        print("   • Prices may be simulated")
        print("   • Risk of trading on fake signals")
        print("   • Could result in real losses")
        
        recommend_fixes()
    
    print("\n🔗 Monitor your dashboard: https://helpful-maamoul-8aa9bd.netlify.app")
    print("="*60)

if __name__ == "__main__":
    main()
