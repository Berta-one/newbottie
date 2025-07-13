# scanner_main.py - Multi-Pair Trading Bot Main Loop
import time
import os
from dotenv import load_dotenv
from binance.client import Client
from multi_pair_scanner import CryptoPairScanner, scan_all_pairs, scan_selected_pairs, scan_custom_pairs
from trader import (monitor_position_enhanced, calculate_dynamic_position_size, 
                   get_account_balance, execute_entry, calculate_portfolio_metrics)
from datetime import datetime
import json
import signal
import sys

load_dotenv()

# Configuration
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
TESTNET_URL = os.getenv("BINANCE_TESTNET_URL", "https://testnet.binance.vision/api")
LIVE_URL = os.getenv("BINANCE_LIVE_URL", "https://api.binance.com/api")

# Trading Configuration
SCAN_MODE = os.getenv("SCAN_MODE", "SELECTED")  # Options: "ALL", "SELECTED", "CUSTOM"
CUSTOM_SYMBOLS = os.getenv("CUSTOM_SYMBOLS", "BTCUSDT,ETHUSDT,ADAUSDT,SOLUSDT,BNBUSDT").split(",")
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.65"))
MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "3"))
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "300"))  # 5 minutes
RISK_PERCENTAGE = float(os.getenv("RISK_PERCENTAGE", "0.015"))  # 1.5% per trade

class MultiPairTradingBot:
    def __init__(self, client):
        self.client = client
        self.scanner = CryptoPairScanner(client)
        self.active_positions = {}
        self.trade_history = []
        self.performance_metrics = {}
        self.bot_start_time = datetime.now()
        self.total_scans = 0
        self.opportunities_found = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received shutdown signal ({signum})")
        self.shutdown_bot()
        sys.exit(0)
        
    def shutdown_bot(self):
        """Graceful bot shutdown"""
        print("🔄 Shutting down bot...")
        
        # Close any open positions (optional - you might want to keep them)
        if self.active_positions:
            print(f"⚠️  Warning: {len(self.active_positions)} positions still active")
            for symbol in self.active_positions:
                print(f"   - {symbol}: Entry ${self.active_positions[symbol]['entry_price']:.4f}")
        
        # Save final performance report
        self.save_performance_report()
        print("✅ Bot shutdown complete")

    def initialize_bot(self):
        """Initialize the trading bot with safety checks"""
        print("🤖 Initializing Multi-Pair Trading Bot...")
        print(f"📊 Configuration:")
        print(f"   Scan Mode: {SCAN_MODE}")
        print(f"   Min Confidence: {MIN_CONFIDENCE}")
        print(f"   Max Positions: {MAX_POSITIONS}")
        print(f"   Risk per Trade: {RISK_PERCENTAGE:.1%}")
        print(f"   Scan Interval: {SCAN_INTERVAL}s")
        
        # Set API URL based on mode
        if USE_TESTNET:
            self.client.API_URL = TESTNET_URL
            print("🧪 Running in TESTNET mode")
        else:
            self.client.API_URL = LIVE_URL
            print("🚀 Running in LIVE mode")
            print("⚠️  WARNING: This is live trading with real money!")
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Test connection and get account info
        try:
            server_time = self.client.get_server_time()
            account_balance = get_account_balance(self.client, 'USDT')
            
            print(f"✅ Connected to Binance")
            print(f"🕐 Server Time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
            print(f"💰 Account Balance: ${account_balance:.2f} USDT")
            
            if account_balance < 50:
                print("⚠️  Warning: Low account balance for trading")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def get_trading_opportunities(self):
        """Get trading opportunities based on scan mode"""
        self.total_scans += 1
        
        try:
            if SCAN_MODE == "ALL":
                print("🌍 Scanning ALL crypto pairs...")
                opportunities = scan_all_pairs(self.client, min_volume=3000000, top_n=40)
                
            elif SCAN_MODE == "SELECTED":
                print("📋 Scanning SELECTED crypto pairs...")
                opportunities = scan_selected_pairs(self.client)
                
            elif SCAN_MODE == "CUSTOM":
                print(f"🎯 Scanning CUSTOM pairs: {CUSTOM_SYMBOLS}")
                opportunities = scan_custom_pairs(self.client, CUSTOM_SYMBOLS)
                
            else:
                print("❌ Invalid SCAN_MODE. Using SELECTED pairs.")
                opportunities = scan_selected_pairs(self.client)
            
            self.opportunities_found += len([opp for opp in opportunities if opp['decision'] != 'HOLD'])
            return opportunities
            
        except Exception as e:
            print(f"❌ Error during scan: {e}")
            return []

    def select_best_opportunity(self, opportunities):
        """Select the best trading opportunity from scan results"""
        # Filter opportunities
        filtered_opps = self.scanner.filter_opportunities(
            opportunities, 
            min_confidence=MIN_CONFIDENCE,
            max_positions=MAX_POSITIONS
        )
        
        # Remove pairs we're already trading
        available_opps = [opp for opp in filtered_opps 
                         if opp['symbol'] not in self.active_positions]
        
        if not available_opps:
            return None
        
        # Calculate combined score for ranking
        for opp in available_opps:
            # Base score from confidence and scan score
            base_score = (opp['confidence'] * 0.6) + (opp['scan_score'] * 0.4)
            
            # Volume bonus (normalize to 0-1)
            volume_score = min(opp.get('volume_ratio', 0) / 5.0, 1.0)
            
            # Category risk adjustment
            risk_multiplier = opp.get('risk_multiplier', 1.0)
            
            # Combined final score
            opp['final_score'] = base_score * 0.7 + volume_score * 0.2 + risk_multiplier * 0.1
        
        # Sort by final score
        available_opps.sort(key=lambda x: x['final_score'], reverse=True)
        
        return available_opps[0]
    def execute_trade(self, opportunity):
        """Execute a trade based on opportunity"""
        symbol = opportunity['symbol']
        decision = opportunity['decision']
        confidence = opportunity['confidence']
        base_qty = opportunity.get('base_qty', 0.001)
        risk_multiplier = opportunity.get('risk_multiplier', 1.0)
        
        try:
            print(f"\n💰 EXECUTING TRADE:")
            print(f"   Symbol: {symbol}")
            print(f"   Signal: {decision}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Current Price: ${opportunity['current_price']:.4f}")
            print(f"   Category: {opportunity['category']}")
            
            # Get account balance
            account_balance = get_account_balance(self.client, 'USDT')
            
            # Calculate position size with risk adjustment
            adjusted_risk = RISK_PERCENTAGE * risk_multiplier
            dynamic_quantity = calculate_dynamic_position_size(
                account_balance=account_balance,
                base_quantity=base_qty,
                confidence=confidence,
                volatility=opportunity.get('volatility', 0.02),
                risk_percentage=adjusted_risk
            )
            
            print(f"   Account Balance: ${account_balance:.2f}")
            print(f"   Risk Percentage: {adjusted_risk:.2%}")
            print(f"   Position Size: {dynamic_quantity}")
            
            # Execute entry
            entry_result = execute_entry(self.client, symbol, dynamic_quantity, decision)
            
            if entry_result['status'] == 'SUCCESS':
                # Add to active positions
                self.active_positions[symbol] = {
                    'entry_price': entry_result['entry_price'],
                    'quantity': entry_result['quantity'],
                    'entry_time': entry_result['timestamp'],
                    'confidence': confidence,
                    'signal_type': decision,
                    'category': opportunity['category'],
                    'order_id': entry_result['order_id']
                }
                
                print(f"✅ Trade executed successfully!")
                print(f"   Entry Price: ${entry_result['entry_price']:.4f}")
                print(f"   Quantity: {entry_result['quantity']}")
                print(f"   Order ID: {entry_result['order_id']}")
                
                return True
            else:
                print(f"❌ Trade execution failed: {entry_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error executing trade for {symbol}: {e}")
            return False

    def monitor_all_positions(self):
        """Monitor all active positions"""
        if not self.active_positions:
            return
        
        print(f"\n📊 Monitoring {len(self.active_positions)} active positions...")
        
        positions_to_close = []
        
        for symbol, position in self.active_positions.items():
            try:
                # Get current price
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                entry_price = position['entry_price']
                
                # Calculate P&L and time held
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                time_held = (datetime.now() - position['entry_time']).total_seconds() / 60
                
                print(f"   {symbol:<12}: ${current_price:.4f} | P&L: {pnl_pct:+.2f}% | Time: {time_held:.0f}m | Cat: {position['category']}")
                
                # Check if position should be closed
                should_close, reason = self.check_exit_conditions(symbol, position, current_price, pnl_pct, time_held)
                
                if should_close:
                    self.close_position(symbol, position, current_price, reason)
                    positions_to_close.append(symbol)
                    
            except Exception as e:
                print(f"❌ Error monitoring {symbol}: {e}")
        
        # Remove closed positions
        for symbol in positions_to_close:
            del self.active_positions[symbol]

    def check_exit_conditions(self, symbol, position, current_price, pnl_pct, time_held):
        """Check if position should be exited"""
        confidence = position['confidence']
        
        # Dynamic stop/take levels based on confidence
        if confidence > 0.8:
            take_profit = 12.0
            stop_loss = 12.0
        elif confidence > 0.6:
            take_profit = 10.0
            stop_loss = 10.0
        else:
            take_profit = 8.0
            stop_loss = 8.0
        
        # Exit conditions
        if pnl_pct >= take_profit:
            return True, f"Take Profit: {pnl_pct:.2f}%"
        elif pnl_pct <= -stop_loss:
            return True, f"Stop Loss: {pnl_pct:.2f}%"
        elif time_held >= 240:  # 4 hours
            return True, f"Time Limit: {pnl_pct:.2f}%"
        elif pnl_pct > 5.0:  # Trailing stop for profitable positions
            # Simple trailing stop
            if pnl_pct < 3.0:  # Trail by 3%
                return True, f"Trailing Stop: {pnl_pct:.2f}%"
        elif abs(pnl_pct) > 15:  # Emergency exit
            return True, f"Emergency Exit: {pnl_pct:.2f}%"
        
        return False, ""

    def close_position(self, symbol, position, exit_price, reason):
        """Close a position and log the trade"""
        try:
            # Execute market sell
            order = self.client.order_market_sell(
                symbol=symbol,
                quantity=position['quantity']
            )
            
            # Calculate final P&L
            actual_exit_price = float(order['fills'][0]['price']) if order['fills'] else exit_price
            pnl_pct = ((actual_exit_price - position['entry_price']) / position['entry_price']) * 100
            
            # Create trade record
            trade_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'entry_price': position['entry_price'],
                'exit_price': actual_exit_price,
                'quantity': position['quantity'],
                'pnl_percent': pnl_pct,
                'pnl_amount': (actual_exit_price - position['entry_price']) * position['quantity'],
                'reason': reason,
                'confidence': position['confidence'],
                'signal_type': position['signal_type'],
                'category': position['category'],
                'time_held_minutes': (datetime.now() - position['entry_time']).total_seconds() / 60,
                'entry_order_id': position['order_id'],
                'exit_order_id': order.get('orderId', 'Unknown')
            }
            
            # Add to trade history
            self.trade_history.append(trade_record)
            
            # Save trade log
            self.save_trade_log(trade_record)
            
            print(f"🔄 Position closed: {symbol}")
            print(f"   {reason}")
            print(f"   Exit Price: ${actual_exit_price:.4f}")
            print(f"   P&L: {pnl_pct:+.2f}%")
            
        except Exception as e:
            print(f"❌ Error closing position {symbol}: {e}")

    def save_trade_log(self, trade_record):
        """Save individual trade to log file"""
        log_file = 'logs/multi_pair_trades.json'
        
        # Load existing logs
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        
        # Add new trade
        logs.append(trade_record)
        
        # Save updated logs
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2, default=str)

    def calculate_and_display_performance(self):
        """Calculate and display current performance metrics"""
        if not self.trade_history:
            print("\n📊 No completed trades yet")
            return
        
        # Calculate metrics
        metrics = calculate_portfolio_metrics(self.trade_history)
        
        # Update instance metrics
        self.performance_metrics = {
            **metrics,
            'bot_uptime_hours': (datetime.now() - self.bot_start_time).total_seconds() / 3600,
            'total_scans': self.total_scans,
            'opportunities_found': self.opportunities_found,
            'active_positions': len(self.active_positions),
            'last_updated': datetime.now().isoformat()
        }
        
        # Display performance summary
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Bot Uptime: {self.performance_metrics['bot_uptime_hours']:.1f} hours")
        print(f"   Total Scans: {self.total_scans}")
        print(f"   Opportunities Found: {self.opportunities_found}")
        print(f"   Completed Trades: {metrics['total_trades']}")
        print(f"   Win Rate: {metrics['win_rate']:.1f}%")
        print(f"   Average P&L: {metrics.get('total_pnl_percent', 0) / max(metrics['total_trades'], 1):.2f}%")
        print(f"   Total P&L: {metrics.get('total_pnl_percent', 0):+.2f}%")
        print(f"   Active Positions: {len(self.active_positions)}")

    def save_performance_report(self):
        """Save comprehensive performance report"""
        report = {
            'bot_info': {
                'start_time': self.bot_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'configuration': {
                    'scan_mode': SCAN_MODE,
                    'min_confidence': MIN_CONFIDENCE,
                    'max_positions': MAX_POSITIONS,
                    'risk_percentage': RISK_PERCENTAGE,
                    'scan_interval': SCAN_INTERVAL,
                    'use_testnet': USE_TESTNET
                }
            },
            'performance_metrics': self.performance_metrics,
            'trade_history': self.trade_history,
            'scan_statistics': self.scanner.get_scan_statistics(),
            'active_positions': {
                symbol: {
                    **position,
                    'entry_time': position['entry_time'].isoformat() if isinstance(position['entry_time'], datetime) else position['entry_time']
                }
                for symbol, position in self.active_positions.items()
            }
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f'logs/performance_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Performance report saved to {report_file}")

    def main_trading_loop(self):
        """Main trading loop"""
        print(f"\n🎯 Starting multi-pair trading loop")
        print(f"⏱️  Scan interval: {SCAN_INTERVAL} seconds")
        print("─" * 60)
        
        loop_count = 0
        
        try:
            while True:
                loop_count += 1
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n🔄 [{current_time}] Loop #{loop_count} - Starting scan cycle...")
                
                # Monitor existing positions first
                if self.active_positions:
                    self.monitor_all_positions()
                
                # Look for new opportunities if we have capacity
                available_slots = MAX_POSITIONS - len(self.active_positions)
                
                if available_slots > 0:
                    print(f"🔍 Looking for new opportunities ({available_slots} slots available)...")
                    
                    # Get opportunities
                    opportunities = self.get_trading_opportunities()
                    
                    if opportunities:
                        # Select and execute best opportunity
                        best_opportunity = self.select_best_opportunity(opportunities)
                        
                        if best_opportunity:
                            print(f"\n🎯 Selected opportunity: {best_opportunity['symbol']} ({best_opportunity['decision']}, Conf: {best_opportunity['confidence']:.2f})")
                            self.execute_trade(best_opportunity)
                        else:
                            print("😴 No suitable opportunities found meeting criteria")
                    else:
                        print("❌ No opportunities detected in scan")
                else:
                    print(f"⏳ Maximum positions reached ({MAX_POSITIONS})")
                
                # Display performance summary every 5 loops
                if loop_count % 5 == 0:
                    self.calculate_and_display_performance()
                
                # Save performance report every 20 loops
                if loop_count % 20 == 0:
                    self.save_performance_report()
                
                # Wait before next scan
                print(f"⏱️  Waiting {SCAN_INTERVAL} seconds until next scan...")
                time.sleep(SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Bot stopped by user after {loop_count} loops")
        except Exception as e:
            print(f"\n❌ Unexpected error in main loop: {e}")
            print("🔄 Attempting to save state before shutdown...")
        finally:
            self.shutdown_bot()

def main():
    """Main entry point"""
    print("🚀 Multi-Pair Crypto Trading Bot v2.0")
    print("=" * 60)
    
    # Validate configuration
    if not API_KEY or not API_SECRET:
        print("❌ Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env file")
        return
    
    if SCAN_MODE not in ["ALL", "SELECTED", "CUSTOM"]:
        print(f"❌ Error: Invalid SCAN_MODE '{SCAN_MODE}'. Must be ALL, SELECTED, or CUSTOM")
        return
    
    # Initialize Binance client
    try:
        client = Client(API_KEY, API_SECRET)
    except Exception as e:
        print(f"❌ Error creating Binance client: {e}")
        return
    
    # Initialize and run bot
    bot = MultiPairTradingBot(client)
    
    if bot.initialize_bot():
        bot.main_trading_loop()
    else:
        print("❌ Bot initialization failed")

if __name__ == "__main__":
    main()
