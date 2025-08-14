#!/usr/bin/env python3
"""
Comprehensive Dashboard Data Diagnostic
Check why positions, trades, and ML indicators are missing
"""

import requests
import json
import ccxt
from datetime import datetime

def test_direct_binance_connection():
    """Test direct connection to your Binance account"""
    print("🔗 TESTING DIRECT BINANCE CONNECTION")
    print("="*50)
    
    try:
        exchange = ccxt.binance({
            'apiKey': 'xcZmoQQ2MEe4q3hx1uGBwR9GrfaCPTCIQLdQEWGiABXxsN4t2Z5GfYJUpNopfJGJ',
            'secret': '4BNmlQr4OvBwbbirXMM8p9LAuBw6JJUOyYD5qNKqSsDiQweFrI8iabWZYajBRRLr',
            'sandbox': False,
            'enableRateLimit': True,
        })
        
        exchange.load_markets()
        print("✅ Exchange connection successful")
        
        # Get real account balance
        balance = exchange.fetch_balance()
        print(f"\n💰 YOUR REAL ACCOUNT BALANCE:")
        
        total_usdt = 0
        for currency, amount in balance['total'].items():
            if amount > 0.001:
                try:
                    if currency == 'USDT':
                        usdt_value = amount
                        print(f"   {currency}: ${amount:.2f}")
                    else:
                        ticker = exchange.fetch_ticker(f"{currency}/USDT")
                        usdt_value = amount * ticker['last']
                        print(f"   {currency}: {amount:.6f} (≈ ${usdt_value:.2f})")
                    total_usdt += usdt_value
                except:
                    print(f"   {currency}: {amount:.6f}")
        
        print(f"💎 Total Portfolio: ${total_usdt:.2f}")
        
        # Check open orders/positions
        open_orders = exchange.fetch_open_orders()
        print(f"📈 Open Orders: {len(open_orders)}")
        
        if open_orders:
            for order in open_orders[:3]:
                print(f"   {order['symbol']}: {order['side']} {order['amount']:.6f} @ ${order['price']:.2f}")
        
        return total_usdt, len(open_orders)
        
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        return 0, 0

def check_all_dashboard_endpoints():
    """Check all dashboard endpoints to see what data is missing"""
    print("\n📊 CHECKING ALL DASHBOARD ENDPOINTS")
    print("="*50)
    
    endpoints = [
        "/",
        "/health", 
        "/status",
        "/grid/matrix",
        "/signals",
        "/account/balance",
        "/account/positions",
        "/trades",
        "/ml/status",
        "/quantum/details",
        "/sentiment/articles"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"https://bottie-1.onrender.com{endpoint}"
            response = requests.get(url)
            data = response.json()
            
            print(f"\n✅ {endpoint}:")
            
            if endpoint == "/status":
                print(f"   Equity: ${data.get('equity', 0):,.2f}")
                print(f"   Positions: {len(data.get('positions', {}))}")
                print(f"   Active Trades: {data.get('active_trades', 0)}")
                print(f"   Total P&L: ${data.get('total_pnl', 0):.2f}")
                print(f"   Mode: {data.get('mode', 'Unknown')}")
                
            elif endpoint == "/ml/status":
                print(f"   ML Enabled: {data.get('enabled', False)}")
                print(f"   ML Loaded: {data.get('loaded', False)}")
                
            elif endpoint == "/account/balance":
                if isinstance(data, dict):
                    total = sum(v for v in data.values() if isinstance(v, (int, float)))
                    print(f"   Account Balance: ${total:,.2f}")
                else:
                    print(f"   Account Balance: {data}")
                    
            elif endpoint == "/account/positions":
                if isinstance(data, dict):
                    print(f"   Positions Count: {len(data)}")
                    for symbol, pos in list(data.items())[:3]:
                        print(f"     {symbol}: {pos}")
                else:
                    print(f"   Positions: {data}")
                    
            elif endpoint == "/trades":
                if isinstance(data, list):
                    print(f"   Recent Trades: {len(data)}")
                else:
                    print(f"   Trades: {data}")
                    
            elif endpoint == "/signals":
                if isinstance(data, list):
                    print(f"   Trading Signals: {len(data)}")
                    for signal in data[:2]:
                        print(f"     {signal.get('symbol', '')}: {signal.get('signal', '')}")
                else:
                    print(f"   Signals: {data}")
                    
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

def check_missing_features():
    """Identify what specific features are missing"""
    print("\n🔍 ANALYZING MISSING FEATURES")
    print("="*50)
    
    missing_features = []
    
    try:
        # Check status for comprehensive info
        response = requests.get("https://bottie-1.onrender.com/status")
        status_data = response.json()
        
        equity = status_data.get('equity', 0)
        positions = status_data.get('positions', {})
        active_trades = status_data.get('active_trades', 0)
        
        if equity == 10000.0:
            missing_features.append("Real account balance (showing simulated $10,000)")
            
        if len(positions) == 0:
            missing_features.append("Trading positions")
            
        if active_trades == 0:
            missing_features.append("Active trades")
        
        # Check ML status
        ml_response = requests.get("https://bottie-1.onrender.com/ml/status")
        ml_data = ml_response.json()
        
        if not ml_data.get('enabled', False):
            missing_features.append("ML indicators")
            
        if not ml_data.get('loaded', False):
            missing_features.append("ML models")
        
        # Check trades
        trades_response = requests.get("https://bottie-1.onrender.com/trades")
        trades_data = trades_response.json()
        
        if isinstance(trades_data, list) and len(trades_data) == 0:
            missing_features.append("Trade history")
        
        return missing_features
        
    except Exception as e:
        print(f"❌ Error analyzing features: {e}")
        return ["Unable to analyze - connection error"]

def provide_solutions(missing_features, real_balance, real_positions):
    """Provide specific solutions for missing features"""
    print("\n🔧 SOLUTIONS FOR MISSING FEATURES")
    print("="*50)
    
    print("Based on your real account analysis:")
    print(f"   Real Balance: ${real_balance:,.2f}")
    print(f"   Real Positions: {real_positions}")
    
    for feature in missing_features:
        print(f"\n❌ Missing: {feature}")
        
        if "Real account balance" in feature:
            print("   Solution: Exchange client not properly initialized")
            print("   Fix: Check exchange initialization in startup_event()")
            
        elif "Trading positions" in feature:
            if real_positions > 0:
                print("   Solution: You have real positions but API not fetching them")
                print("   Fix: Fix get_real_positions() function")
            else:
                print("   Solution: No actual positions in your Binance account")
                print("   Fix: This is normal if you haven't placed trades yet")
                
        elif "ML indicators" in feature:
            print("   Solution: ML system not enabled or initialized")
            print("   Fix: Check ML_ENABLED environment variable and model loading")
            
        elif "Trade history" in feature:
            print("   Solution: No recent trades to display")
            print("   Fix: This is normal for a new account or if not trading actively")

def main():
    """Main diagnostic function"""
    print("🚨 COMPREHENSIVE DASHBOARD DIAGNOSTIC")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Test direct Binance connection
    real_balance, real_positions = test_direct_binance_connection()
    
    # Check all dashboard endpoints
    check_all_dashboard_endpoints()
    
    # Identify missing features
    missing_features = check_missing_features()
    
    print(f"\n📋 MISSING FEATURES SUMMARY:")
    print("="*50)
    for feature in missing_features:
        print(f"   ❌ {feature}")
    
    # Provide solutions
    provide_solutions(missing_features, real_balance, real_positions)
    
    print(f"\n🔗 Dashboard: https://helpful-maamoul-8aa9bd.netlify.app")
    print("="*60)

if __name__ == "__main__":
    main()
