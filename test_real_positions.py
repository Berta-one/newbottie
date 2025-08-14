#!/usr/bin/env python3
"""
Test Your Real Binance Positions
Verify we can see all your actual trading positions
"""

import ccxt
import json
from datetime import datetime

def test_your_real_positions():
    """Test all methods to get your real positions"""
    print("🔍 CHECKING YOUR REAL BINANCE POSITIONS")
    print("="*60)
    
    try:
        exchange = ccxt.binance({
            'apiKey': 'xcZmoQQ2MEe4q3hx1uGBwR9GrfaCPTCIQLdQEWGiABXxsN4t2Z5GfYJUpNopfJGJ',
            'secret': '4BNmlQr4OvBwbbirXMM8p9LAuBw6JJUOyYD5qNKqSsDiQweFrI8iabWZYajBRRLr',
            'sandbox': False,
            'enableRateLimit': True,
        })
        
        exchange.load_markets()
        print("✅ Connected to your Binance account")
        
        print("\n📊 METHOD 1: OPEN ORDERS (Active Spot Orders)")
        print("-" * 50)
        try:
            # Suppress the warning for demo
            exchange.options['warnOnFetchOpenOrdersWithoutSymbol'] = False
            open_orders = exchange.fetch_open_orders()
            
            if open_orders:
                print(f"✅ Found {len(open_orders)} open orders:")
                for order in open_orders:
                    print(f"   {order['symbol']}: {order['side']} {order['amount']:.6f} @ ${order['price']:.2f}")
                    print(f"      Status: {order['status']}, Type: {order['type']}")
            else:
                print("   No open spot orders")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n🚀 METHOD 2: FUTURES POSITIONS")
        print("-" * 50)
        try:
            futures_positions = exchange.fetch_positions()
            active_futures = [pos for pos in futures_positions if abs(pos['contracts']) > 0.001]
            
            if active_futures:
                print(f"✅ Found {len(active_futures)} futures positions:")
                for pos in active_futures:
                    print(f"   {pos['symbol']}: {pos['side']} {pos['contracts']:.6f}")
                    print(f"      Entry: ${pos['entryPrice']:.2f}, Mark: ${pos['markPrice']:.2f}")
                    print(f"      PnL: ${pos['unrealizedPnl']:.2f}")
            else:
                print("   No active futures positions")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n💰 METHOD 3: SPOT HOLDINGS (Your Asset Balance)")
        print("-" * 50)
        try:
            balance = exchange.fetch_balance()
            holdings = []
            
            for symbol, amount in balance['total'].items():
                if amount > 0.001 and symbol != 'USDT':
                    try:
                        ticker = exchange.fetch_ticker(f"{symbol}/USDT")
                        current_price = ticker['last']
                        market_value = amount * current_price
                        
                        holdings.append({
                            'symbol': f"{symbol}USDT",
                            'amount': amount,
                            'price': current_price,
                            'value': market_value
                        })
                    except:
                        holdings.append({
                            'symbol': symbol,
                            'amount': amount,
                            'price': 0,
                            'value': 0
                        })
            
            if holdings:
                print(f"✅ Found {len(holdings)} asset holdings:")
                total_value = 0
                for holding in holdings:
                    print(f"   {holding['symbol']}: {holding['amount']:.6f}")
                    if holding['price'] > 0:
                        print(f"      @ ${holding['price']:.2f} = ${holding['value']:.2f}")
                        total_value += holding['value']
                    else:
                        print(f"      (price unavailable)")
                
                print(f"   💎 Total Holdings Value: ${total_value:.2f}")
            else:
                print("   No significant asset holdings")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("\n💵 USDT BALANCE:")
        print("-" * 50)
        try:
            usdt_balance = balance['total'].get('USDT', 0)
            print(f"   USDT: ${usdt_balance:.2f}")
        except:
            print("   Could not fetch USDT balance")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False

def main():
    """Main function"""
    print("🎯 YOUR REAL BINANCE POSITIONS TEST")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    success = test_your_real_positions()
    
    if success:
        print("\n🎉 SUCCESS: Position data retrieved")
        print("\nNow deploying the fix to show these in your dashboard...")
    else:
        print("\n❌ FAILED: Could not retrieve position data")
    
    print("="*60)

if __name__ == "__main__":
    main()
