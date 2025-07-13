# main.py - Enhanced Single-Pair Trading Bot
import time
import os
from dotenv import load_dotenv
from binance.client import Client
from strategy import check_breakout_enhanced, get_strategy_confidence
from trader import monitor_position_enhanced, calculate_dynamic_position_size, get_account_balance
from datetime import datetime
import json

load_dotenv()

# Configuration
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
TESTNET_URL = os.getenv("BINANCE_TESTNET_URL", "https://testnet.binance.vision/api")

TRADE_SYMBOL = "BTCUSDT"
BASE_TRADE_QTY = 0.001
RISK_PERCENTAGE = float(os.getenv("RISK_PERCENTAGE", "0.015"))

# Trading state
in_position = False
entry_price = None
trade_count = 0
total_pnl = 0.0
performance_log = []

def log_performance(trade_result):
    """Log trade performance for analysis"""
    global total_pnl, trade_count
    
    if 'pnl_percent' in trade_result:
        total_pnl += trade_result['pnl_percent']
        trade_count += 1
        
        performance_log.append({
            'trade_number': trade_count,
            'timestamp': trade_result['timestamp'].isoformat(),
            'symbol': trade_result['symbol'],
            'entry_price': trade_result['entry_price'],
            'exit_price': trade_result['exit_price'],
            'pnl_percent': trade_result['pnl_percent'],
            'reason': trade_result['reason'],
            'cumulative_pnl': total_pnl
        })
        
        # Save to file
        os.makedirs('logs', exist_ok=True)
        with open('logs/single_pair_performance.json', 'w') as f:
            json.dump(performance_log, f, indent=2, default=str)
        
        # Print summary
        avg_pnl = total_pnl / trade_count if trade_count > 0 else 0
        win_rate = len([t for t in performance_log if t['pnl_percent'] > 0]) / trade_count * 100
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Total Trades: {trade_count}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Average P&L: {avg_pnl:.2f}%")
        print(f"   Cumulative P&L: {total_pnl:+.2f}%")
        print("─" * 40)

def initialize_bot():
    """Initialize the trading bot"""
    global client
    
    print("🤖 Initializing Single-Pair Trading Bot...")
    print(f"🎯 Target Symbol: {TRADE_SYMBOL}")
    print(f"💰 Base Quantity: {BASE_TRADE_QTY}")
    print(f"⚠️  Risk per Trade: {RISK_PERCENTAGE:.1%}")
    
    client = Client(API_KEY, API_SECRET)
    
    if USE_TESTNET:
        client.API_URL = TESTNET_URL
        print("🧪 Running in TESTNET mode")
    else:
        print("🚀 Running in LIVE mode")
        print("⚠️  WARNING: This is live trading with real money!")
    
    os.makedirs('logs', exist_ok=True)
    
    try:
        server_time = client.get_server_time()
        balance = get_account_balance(client, 'USDT')
        print(f"✅ Connected to Binance (Server time: {datetime.fromtimestamp(server_time['serverTime']/1000)})")
        print(f"💰 Account Balance: ${balance:.2f} USDT")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main_trading_loop():
    """Enhanced main trading loop"""
    global in_position, entry_price
    
    print(f"\n🎯 Starting enhanced trading on {TRADE_SYMBOL}")
    print("─" * 50)
    
    while True:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n🔄 [{current_time}] Checking market...")
            
            # Fetch 2 hours of 1-minute candles
            klines = client.get_klines(
                symbol=TRADE_SYMBOL,
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=120
            )
            
            # Get trading decision
            decision = check_breakout_enhanced(klines)
            confidence = get_strategy_confidence(klines)
            
            print(f"📈 Decision: {decision} (Confidence: {confidence:.2f})")
            
            # Execute trade if not in position
            if not in_position and decision in ["BUY_LONG", "BUY_SHORT"]:
                
                # Get current account balance
                account_balance = get_account_balance(client, 'USDT')
                
                # Calculate dynamic position size
                from strategy import calculate_volatility
                volatility = calculate_volatility(klines, 20)
                
                dynamic_quantity = calculate_dynamic_position_size(
                    account_balance=account_balance,
                    base_quantity=BASE_TRADE_QTY,
                    confidence=confidence,
                    volatility=volatility,
                    risk_percentage=RISK_PERCENTAGE
                )
                
                print(f"💱 Executing {decision}:")
                print(f"   💰 Account Balance: ${account_balance:.2f}")
                print(f"   📊 Confidence: {confidence:.2f}")
                print(f"   📈 Volatility: {volatility:.4f}")
                print(f"   🎯 Position Size: {dynamic_quantity:.6f} BTC")
                
                try:
                    # Place market buy order
                    order = client.order_market_buy(
                        symbol=TRADE_SYMBOL,
                        quantity=f"{dynamic_quantity:.6f}"
                    )
                    
                    entry_price = float(order['fills'][0]['price'])
                    actual_quantity = float(order['executedQty'])
                    in_position = True
                    
                    print(f"✅ Order executed!")
                    print(f"   💰 Entry Price: ${entry_price:.2f}")
                    print(f"   📊 Actual Quantity: {actual_quantity:.6f}")
                    print(f"   🆔 Order ID: {order['orderId']}")
                    
                    # Start position monitoring
                    print(f"\n📊 Starting position monitoring...")
                    result = monitor_position_enhanced(
                        entry_price=entry_price,
                        symbol=TRADE_SYMBOL,
                        quantity=actual_quantity,
                        client=client,
                        klines=klines
                    )
                    
                    # Log the trade result
                    log_performance(result)
                    
                    in_position = False
                    entry_price = None
                    
                    print(f"🏁 Position closed. Waiting for next opportunity...")
                    
                except Exception as e:
                    print(f"❌ Error executing trade: {e}")
                    in_position = False
                    
            elif in_position:
                print(f"⏳ Already in position (Entry: ${entry_price:.2f})")
                
            else:
                print(f"😴 No trading opportunity")
            
            # Wait 5 minutes before next check
            print(f"⏱️  Waiting 5 minutes until next check...")
            time.sleep(300)
            
        except KeyboardInterrupt:
            print(f"\n🛑 Bot stopped by user")
            break
            
        except Exception as e:
            print(f"⚠️ Error in main loop: {e}")
            print(f"⏱️  Waiting 1 minute before retry...")
            time.sleep(60)

if __name__ == "__main__":
    if initialize_bot():
        main_trading_loop()
    else:
        print("❌ Failed to initialize bot")
