# main.py - Enhanced Single-Pair Trading Bot with ML Integration
import os
import sys
import time
import json
import signal
from datetime import datetime, timedelta
from dotenv import load_dotenv
from binance.client import Client
import pandas as pd

# Import strategy modules
from strategy import check_breakout_enhanced, get_strategy_confidence, analyze_pair_strength
from enhanced_ml_strategy import get_ml_enhanced_signal, ml_strategy
from trader import (monitor_position_enhanced, calculate_dynamic_position_size, 
                   get_account_balance, execute_entry, execute_exit)
from logger import trading_logger

# ─── Load Environment Configuration ─────────────────────────────────
load_dotenv()

# API Configuration
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
TESTNET_URL = os.getenv("BINANCE_TESTNET_URL", "https://testnet.binance.vision/api")
LIVE_URL = os.getenv("BINANCE_LIVE_URL", "https://api.binance.com/api")

# Trading Configuration
TRADE_SYMBOL = os.getenv("TRADE_SYMBOL", "BTCUSDT")
BASE_TRADE_QTY = float(os.getenv("BASE_TRADE_QTY", "0.001"))
RISK_PERCENTAGE = float(os.getenv("RISK_PERCENTAGE", "0.015"))
USE_ML_ENHANCEMENT = os.getenv("USE_ML_ENHANCEMENT", "True").lower() == "true"
STRATEGY_COMPARISON_MODE = os.getenv("STRATEGY_COMPARISON_MODE", "False").lower() == "true"

# Bot Configuration
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "300"))  # 5 minutes
MAX_HOLD_TIME_MINUTES = int(os.getenv("MAX_HOLD_TIME_MINUTES", "240"))  # 4 hours
ENABLE_PAPER_TRADING = os.getenv("ENABLE_PAPER_TRADING", "False").lower() == "true"

class EnhancedSinglePairBot:
    def __init__(self):
        self.client = None
        self.in_position = False
        self.current_position = None
        self.trade_count = 0
        self.session_start_time = datetime.now()
        self.performance_metrics = {
            'total_pnl_percent': 0.0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_trades': 0,
            'max_drawdown': 0.0,
            'current_drawdown': 0.0,
            'peak_pnl': 0.0
        }
        
        # Strategy comparison tracking
        self.strategy_comparison_log = []
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging system"""
        os.makedirs("logs", exist_ok=True)
        
        # Redirect stdout to log file
        log_file = open("logs/console_output.log", "a", buffering=1, encoding="utf-8")
        sys.stdout = log_file
        
        self.safe_print("=" * 80)
        self.safe_print(f"🤖 Enhanced Single-Pair Bot Started - {datetime.now()}")
        self.safe_print("=" * 80)
    
    def safe_print(self, *args, **kwargs):
        """Safe printing with error handling"""
        try:
            print(*args, **kwargs)
        except Exception as e:
            print(f"[Logging Error] {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.safe_print(f"\n🛑 Received shutdown signal ({signum})")
        self.shutdown_bot()
        sys.exit(0)
    
    def shutdown_bot(self):
        """Graceful bot shutdown"""
        self.safe_print("\n🔄 Shutting down Enhanced Single-Pair Bot...")
        
        # Close position if active
        if self.in_position and self.current_position:
            self.safe_print("⚠️  Closing active position due to shutdown...")
            try:
                current_price = float(self.client.get_symbol_ticker(symbol=TRADE_SYMBOL)['price'])
                self.close_position(current_price, "Bot Shutdown")
            except Exception as e:
                self.safe_print(f"❌ Error closing position during shutdown: {e}")
        
        # Save final performance report
        self.save_session_report()
        self.safe_print("✅ Bot shutdown complete")
    
    def initialize_bot(self):
        """Initialize the trading bot with safety checks"""
        self.safe_print("🔧 Initializing Enhanced Single-Pair Trading Bot...")
        
        # Configuration summary
        self.safe_print(f"📊 Configuration:")
        self.safe_print(f"   Symbol: {TRADE_SYMBOL}")
        self.safe_print(f"   Base Quantity: {BASE_TRADE_QTY}")
        self.safe_print(f"   Risk per Trade: {RISK_PERCENTAGE:.1%}")
        self.safe_print(f"   ML Enhancement: {'✅ Enabled' if USE_ML_ENHANCEMENT else '❌ Disabled'}")
        self.safe_print(f"   Strategy Comparison: {'✅ Enabled' if STRATEGY_COMPARISON_MODE else '❌ Disabled'}")
        self.safe_print(f"   Paper Trading: {'✅ Enabled' if ENABLE_PAPER_TRADING else '❌ Disabled'}")
        self.safe_print(f"   Scan Interval: {SCAN_INTERVAL}s")
        
        # Initialize Binance client
        try:
            self.client = Client(API_KEY, API_SECRET)
            
            # Set API URL based on mode
            if USE_TESTNET:
                self.client.API_URL = TESTNET_URL
                self.safe_print("🧪 Running in TESTNET mode")
            else:
                self.client.API_URL = LIVE_URL
                self.safe_print("🚀 Running in LIVE mode")
                if not ENABLE_PAPER_TRADING:
                    self.safe_print("⚠️  WARNING: This is live trading with real money!")
            
            # Test connection
            server_time = self.client.get_server_time()
            account_balance = get_account_balance(self.client, 'USDT')
            
            self.safe_print(f"✅ Connected to Binance")
            self.safe_print(f"🕐 Server Time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
            self.safe_print(f"💰 Account Balance: ${account_balance:.2f} USDT")
            
            if account_balance < 50 and not ENABLE_PAPER_TRADING:
                self.safe_print("⚠️  Warning: Low account balance for trading")
            
            return True
            
        except Exception as e:
            self.safe_print(f"❌ Initialization failed: {e}")
            return False
    
    def get_market_data(self):
        """Get comprehensive market data for analysis"""
        try:
            # Get 2 hours of 1-minute candlestick data
            klines = self.client.get_klines(
                symbol=TRADE_SYMBOL,
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=120
            )
            
            if not klines or len(klines) < 120:
                self.safe_print("⚠️  Insufficient market data")
                return None
            
            # Get current ticker info
            ticker = self.client.get_symbol_ticker(symbol=TRADE_SYMBOL)
            current_price = float(ticker['price'])
            
            # Get 24h ticker for additional context
            ticker_24h = self.client.get_ticker(symbol=TRADE_SYMBOL)
            
            market_data = {
                'klines': klines,
                'current_price': current_price,
                'price_change_24h': float(ticker_24h['priceChangePercent']),
                'volume_24h': float(ticker_24h['volume']),
                'high_24h': float(ticker_24h['highPrice']),
                'low_24h': float(ticker_24h['lowPrice'])
            }
            
            return market_data
            
        except Exception as e:
            self.safe_print(f"❌ Error fetching market data: {e}")
            return None
    
    def analyze_market(self, market_data):
        """Comprehensive market analysis using multiple strategies"""
        klines = market_data['klines']
        current_price = market_data['current_price']
        
        analysis_results = {
            'timestamp': datetime.now(),
            'current_price': current_price,
            'market_context': market_data
        }
        
        # Traditional strategy analysis
        traditional_signal = check_breakout_enhanced(klines)
        traditional_confidence = get_strategy_confidence(klines)
        
        analysis_results['traditional'] = {
            'signal': traditional_signal,
            'confidence': traditional_confidence
        }
        
        # ML-enhanced strategy analysis
        if USE_ML_ENHANCEMENT:
            try:
                ml_signal, ml_confidence = get_ml_enhanced_signal(klines)
                analysis_results['ml_enhanced'] = {
                    'signal': ml_signal,
                    'confidence': ml_confidence
                }
            except Exception as e:
                self.safe_print(f"⚠️  ML analysis failed: {e}")
                analysis_results['ml_enhanced'] = {
                    'signal': traditional_signal,
                    'confidence': traditional_confidence,
                    'error': str(e)
                }
        
        # Pair strength analysis
        try:
            pair_analysis = analyze_pair_strength(klines, TRADE_SYMBOL)
            analysis_results['pair_analysis'] = pair_analysis
        except Exception as e:
            self.safe_print(f"⚠️  Pair analysis failed: {e}")
        
        # Strategy comparison logging
        if STRATEGY_COMPARISON_MODE and 'ml_enhanced' in analysis_results:
            comparison = {
                'timestamp': datetime.now().isoformat(),
                'traditional_signal': traditional_signal,
                'traditional_confidence': traditional_confidence,
                'ml_signal': analysis_results['ml_enhanced']['signal'],
                'ml_confidence': analysis_results['ml_enhanced']['confidence'],
                'agreement': traditional_signal == analysis_results['ml_enhanced']['signal'],
                'confidence_diff': abs(traditional_confidence - analysis_results['ml_enhanced']['confidence'])
            }
            self.strategy_comparison_log.append(comparison)
        
        return analysis_results
    
    def make_trading_decision(self, analysis_results):
        """Make final trading decision based on analysis"""
        
        # Choose strategy based on configuration
        if USE_ML_ENHANCEMENT and 'ml_enhanced' in analysis_results:
            chosen_strategy = 'ml_enhanced'
            signal = analysis_results['ml_enhanced']['signal']
            confidence = analysis_results['ml_enhanced']['confidence']
        else:
            chosen_strategy = 'traditional'
            signal = analysis_results['traditional']['signal']
            confidence = analysis_results['traditional']['confidence']
        
        # Additional filters
        if signal != "HOLD":
            # Minimum confidence filter
            if confidence < 0.5:
                signal = "HOLD"
                self.safe_print(f"🚫 Signal rejected: Low confidence ({confidence:.2f})")
            
            # Market context filters
            pair_analysis = analysis_results.get('pair_analysis', {})
            volume_ratio = pair_analysis.get('volume_ratio', 0)
            
            if volume_ratio < 1.2:
                signal = "HOLD" 
                self.safe_print(f"🚫 Signal rejected: Low volume ratio ({volume_ratio:.2f})")
        
        return {
            'final_signal': signal,
            'final_confidence': confidence,
            'chosen_strategy': chosen_strategy,
            'analysis_timestamp': analysis_results['timestamp']
        }
    
    def execute_entry_trade(self, decision, market_data):
        """Execute entry trade based on decision"""
        signal = decision['final_signal']
        confidence = decision['final_confidence']
        current_price = market_data['current_price']
        
        try:
            self.safe_print(f"\n💰 EXECUTING ENTRY TRADE:")
            self.safe_print(f"   Symbol: {TRADE_SYMBOL}")
            self.safe_print(f"   Signal: {signal}")
            self.safe_print(f"   Confidence: {confidence:.2f}")
            self.safe_print(f"   Strategy: {decision['chosen_strategy']}")
            self.safe_print(f"   Current Price: ${current_price:.4f}")
            
            # Get account balance for position sizing
            account_balance = get_account_balance(self.client, 'USDT')
            
            # Calculate dynamic position size
            position_size = calculate_dynamic_position_size(
                account_balance=account_balance,
                base_quantity=BASE_TRADE_QTY,
                confidence=confidence,
                volatility=0.03,  # Default volatility
                risk_percentage=RISK_PERCENTAGE
            )
            
            self.safe_print(f"   Account Balance: ${account_balance:.2f}")
            self.safe_print(f"   Position Size: {position_size}")
            self.safe_print(f"   Risk Amount: ${account_balance * RISK_PERCENTAGE:.2f}")
            
            if ENABLE_PAPER_TRADING:
                # Paper trading simulation
                self.safe_print("📝 PAPER TRADE EXECUTED")
                entry_result = {
                    'status': 'SUCCESS',
                    'entry_price': current_price,
                    'quantity': position_size,
                    'timestamp': datetime.now(),
                    'order_id': f'PAPER_{int(time.time())}',
                    'paper_trade': True
                }
            else:
                # Real trade execution
                entry_result = execute_entry(self.client, TRADE_SYMBOL, position_size, signal)
            
            if entry_result['status'] == 'SUCCESS':
                # Update position tracking
                self.current_position = {
                    'symbol': TRADE_SYMBOL,
                    'signal_type': signal,
                    'entry_price': entry_result['entry_price'],
                    'quantity': entry_result['quantity'],
                    'entry_time': entry_result['timestamp'],
                    'confidence': confidence,
                    'strategy_used': decision['chosen_strategy'],
                    'order_id': entry_result['order_id'],
                    'paper_trade': entry_result.get('paper_trade', False)
                }
                
                self.in_position = True
                self.trade_count += 1
                
                self.safe_print(f"✅ Entry executed successfully!")
                self.safe_print(f"   Entry Price: ${entry_result['entry_price']:.4f}")
                self.safe_print(f"   Quantity: {entry_result['quantity']}")
                self.safe_print(f"   Order ID: {entry_result['order_id']}")
                
                return True
            else:
                self.safe_print(f"❌ Entry execution failed: {entry_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.safe_print(f"❌ Error executing entry trade: {e}")
            return False
    
    def monitor_position(self, market_data):
        """Monitor current position and check for exit conditions"""
        if not self.in_position or not self.current_position:
            return
        
        current_price = market_data['current_price']
        position = self.current_position
        entry_price = position['entry_price']
        
        # Calculate current P&L
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        time_held = (datetime.now() - position['entry_time']).total_seconds() / 60
        
        # Display position status
        self.safe_print(f"\n📊 POSITION MONITORING:")
        self.safe_print(f"   Symbol: {position['symbol']}")
        self.safe_print(f"   Entry: ${entry_price:.4f}")
        self.safe_print(f"   Current: ${current_price:.4f}")
        self.safe_print(f"   P&L: {pnl_pct:+.2f}%")
        self.safe_print(f"   Time Held: {time_held:.0f} minutes")
        self.safe_print(f"   Strategy: {position['strategy_used']}")
        
        # Check exit conditions
        should_exit, exit_reason = self.check_exit_conditions(
            position, current_price, pnl_pct, time_held, market_data
        )
        
        if should_exit:
            self.close_position(current_price, exit_reason)
    
    def check_exit_conditions(self, position, current_price, pnl_pct, time_held, market_data):
        """Check various exit conditions"""
        confidence = position['confidence']
        
        # Dynamic exit levels based on confidence
        if confidence > 0.8:
            take_profit = 12.0
            stop_loss = 12.0
        elif confidence > 0.6:
            take_profit = 10.0
            stop_loss = 10.0
        else:
            take_profit = 8.0
            stop_loss = 8.0
        
        # Exit condition checks
        if pnl_pct >= take_profit:
            return True, f"Take Profit: {pnl_pct:+.2f}%"
        
        if pnl_pct <= -stop_loss:
            return True, f"Stop Loss: {pnl_pct:+.2f}%"
        
        if time_held >= MAX_HOLD_TIME_MINUTES:
            return True, f"Time Limit: {pnl_pct:+.2f}% ({time_held:.0f}m)"
        
        # Trailing stop for profitable positions
        if pnl_pct > 5.0:
            trailing_stop = 3.0
            if pnl_pct < trailing_stop:
                return True, f"Trailing Stop: {pnl_pct:+.2f}%"
        
        # Emergency exit for extreme moves
        if abs(pnl_pct) > 15:
            return True, f"Emergency Exit: {pnl_pct:+.2f}%"
        
        # Technical exit signals (re-analyze market)
        try:
            klines = market_data['klines']
            current_signal = check_breakout_enhanced(klines)
            
            # Exit if signal reverses with high confidence
            if current_signal != position['signal_type'] and confidence > 0.7:
                return True, f"Signal Reversal: {current_signal}"
        except:
            pass  # Ignore technical analysis errors
        
        return False, ""
    
    def close_position(self, exit_price, reason):
        """Close current position and log trade"""
        if not self.current_position:
            return
        
        position = self.current_position
        
        try:
            self.safe_print(f"\n🔄 CLOSING POSITION:")
            self.safe_print(f"   Reason: {reason}")
            self.safe_print(f"   Exit Price: ${exit_price:.4f}")
            
            if position.get('paper_trade', False):
                # Paper trading - simulate exit
                self.safe_print("📝 PAPER TRADE CLOSED")
                exit_result = {
                    'status': 'SUCCESS',
                    'exit_price': exit_price,
                    'order_id': f'PAPER_EXIT_{int(time.time())}'
                }
            else:
                # Real trade exit
                exit_result = execute_exit(
                    self.client, 
                    position['symbol'], 
                    position['quantity'], 
                    exit_price, 
                    position['entry_price'], 
                    reason
                )
            
            if exit_result['status'] == 'SUCCESS':
                # Calculate final P&L
                final_exit_price = exit_result.get('exit_price', exit_price)
                pnl_pct = ((final_exit_price - position['entry_price']) / position['entry_price']) * 100
                pnl_amount = (final_exit_price - position['entry_price']) * position['quantity']
                time_held = (datetime.now() - position['entry_time']).total_seconds() / 60
                
                # Update performance metrics
                self.update_performance_metrics(pnl_pct)
                
                # Create trade record
                trade_record = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': position['symbol'],
                    'signal_type': position['signal_type'],
                    'entry_price': position['entry_price'],
                    'exit_price': final_exit_price,
                    'quantity': position['quantity'],
                    'pnl_percent': pnl_pct,
                    'pnl_amount': pnl_amount,
                    'confidence': position['confidence'],
                    'reason': reason,
                    'time_held_minutes': time_held,
                    'strategy_used': position['strategy_used'],
                    'entry_order_id': position['order_id'],
                    'exit_order_id': exit_result['order_id'],
                    'paper_trade': position.get('paper_trade', False)
                }
                
                # Log trade
                trading_logger.log_trade(trade_record)
                
                # Log to performance file
                self.log_trade_performance(trade_record)
                
                self.safe_print(f"✅ Position closed successfully!")
                self.safe_print(f"   Final P&L: {pnl_pct:+.2f}% (${pnl_amount:+.4f})")
                self.safe_print(f"   Time Held: {time_held:.0f} minutes")
                self.safe_print(f"   Total Trades: {self.trade_count}")
                
                # Reset position
                self.current_position = None
                self.in_position = False
                
            else:
                self.safe_print(f"❌ Position close failed: {exit_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.safe_print(f"❌ Error closing position: {e}")
    
    def update_performance_metrics(self, pnl_pct):
        """Update session performance metrics"""
        self.performance_metrics['total_trades'] += 1
        self.performance_metrics['total_pnl_percent'] += pnl_pct
        
        if pnl_pct > 0:
            self.performance_metrics['winning_trades'] += 1
        else:
            self.performance_metrics['losing_trades'] += 1
        
        # Update drawdown tracking
        if self.performance_metrics['total_pnl_percent'] > self.performance_metrics['peak_pnl']:
            self.performance_metrics['peak_pnl'] = self.performance_metrics['total_pnl_percent']
            self.performance_metrics['current_drawdown'] = 0.0
        else:
            current_dd = self.performance_metrics['peak_pnl'] - self.performance_metrics['total_pnl_percent']
            self.performance_metrics['current_drawdown'] = current_dd
            if current_dd > self.performance_metrics['max_drawdown']:
                self.performance_metrics['max_drawdown'] = current_dd
    
    def log_trade_performance(self, trade_record):
        """Log trade to performance file"""
        log_file = "logs/single_pair_performance.json"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                json.dump(trade_record, f, default=str)
                f.write("\n")
        except Exception as e:
            self.safe_print(f"❌ Error logging performance: {e}")
    
    def display_session_summary(self):
        """Display current session performance summary"""
        if self.performance_metrics['total_trades'] == 0:
            return
        
        metrics = self.performance_metrics
        win_rate = (metrics['winning_trades'] / metrics['total_trades']) * 100
        avg_trade = metrics['total_pnl_percent'] / metrics['total_trades']
        session_time = (datetime.now() - self.session_start_time).total_seconds() / 3600
        
        self.safe_print(f"\n📊 SESSION SUMMARY:")
        self.safe_print(f"   Uptime: {session_time:.1f} hours")
        self.safe_print(f"   Total Trades: {metrics['total_trades']}")
        self.safe_print(f"   Win Rate: {win_rate:.1f}%")
        self.safe_print(f"   Total P&L: {metrics['total_pnl_percent']:+.2f}%")
        self.safe_print(f"   Average Trade: {avg_trade:+.2f}%")
        self.safe_print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
        self.safe_print(f"   Current Drawdown: {metrics['current_drawdown']:.2f}%")
    
    def save_session_report(self):
        """Save comprehensive session report"""
        session_report = {
            'session_info': {
                'start_time': self.session_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_hours': (datetime.now() - self.session_start_time).total_seconds() / 3600,
                'trade_symbol': TRADE_SYMBOL,
                'configuration': {
                    'use_ml_enhancement': USE_ML_ENHANCEMENT,
                    'strategy_comparison_mode': STRATEGY_COMPARISON_MODE,
                    'enable_paper_trading': ENABLE_PAPER_TRADING,
                    'risk_percentage': RISK_PERCENTAGE,
                    'base_trade_qty': BASE_TRADE_QTY
                }
            },
            'performance_metrics': self.performance_metrics,
            'strategy_comparison': self.strategy_comparison_log if STRATEGY_COMPARISON_MODE else None,
            'final_position': self.current_position
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f'logs/session_report_{timestamp}.json'
        
        try:
            with open(report_file, 'w') as f:
                json.dump(session_report, f, indent=2, default=str)
            self.safe_print(f"📄 Session report saved to {report_file}")
        except Exception as e:
            self.safe_print(f"❌ Error saving session report: {e}")
    
    def main_trading_loop(self):
        """Main trading loop with enhanced features"""
        self.safe_print(f"\n🎯 Starting Enhanced Trading Loop")
        self.safe_print(f"⏱️  Scan interval: {SCAN_INTERVAL} seconds")
        self.safe_print("─" * 80)
        
        loop_count = 0
        last_summary_time = datetime.now()
        
        try:
            while True:
                loop_count += 1
                current_time = datetime.now()
                
                self.safe_print(f"\n🔄 [{current_time.strftime('%H:%M:%S')}] Loop #{loop_count}")
                
                # Get market data
                market_data = self.get_market_data()
                if not market_data:
                    self.safe_print("⚠️  Market data unavailable, skipping cycle")
                    time.sleep(30)
                    continue
                
                # Analyze market
                analysis_results = self.analyze_market(market_data)
                
                # Display analysis summary
                self.display_analysis_summary(analysis_results)
                
                # Monitor existing position
                if self.in_position:
                    self.monitor_position(market_data)
                
                # Look for new entry if not in position
                elif not self.in_position:
                    decision = self.make_trading_decision(analysis_results)
                    
                    if decision['final_signal'] != "HOLD":
                        self.execute_entry_trade(decision, market_data)
                
                # Display session summary every 10 loops or 30 minutes
                if (loop_count % 10 == 0 or 
                    (current_time - last_summary_time).total_seconds() > 1800):
                    self.display_session_summary()
                    last_summary_time = current_time
                
                # Save strategy comparison data
                if STRATEGY_COMPARISON_MODE and loop_count % 20 == 0:
                    self.save_strategy_comparison()
                
                # Wait for next cycle
                self.safe_print(f"⏱️  Waiting {SCAN_INTERVAL} seconds...")
                time.sleep(SCAN_INTERVAL)
                
        except KeyboardInterrupt:
            self.safe_print(f"\n🛑 Bot stopped by user after {loop_count} loops")
        except Exception as e:
            self.safe_print(f"\n❌ Unexpected error in main loop: {e}")
        finally:
            self.shutdown_bot()
    
    def display_analysis_summary(self, analysis_results):
        """Display market analysis summary"""
        current_price = analysis_results['current_price']
        market_context = analysis_results['market_context']
        
        self.safe_print(f"📈 Market Analysis:")
        self.safe_print(f"   Price: ${current_price:.4f}")
        self.safe_print(f"   24h Change: {market_context['price_change_24h']:+.2f}%")
        
        # Traditional strategy
        trad = analysis_results['traditional']
        self.safe_print(f"   Traditional: {trad['signal']} (conf: {trad['confidence']:.2f})")
        
        # ML-enhanced strategy
        if 'ml_enhanced' in analysis_results:
            ml = analysis_results['ml_enhanced']
            if 'error' in ml:
                self.safe_print(f"   ML Enhanced: Error - {ml['error']}")
            else:
                self.safe_print(f"   ML Enhanced: {ml['signal']} (conf: {ml['confidence']:.2f})")
        
        # Pair analysis
        if 'pair_analysis' in analysis_results:
            pair = analysis_results['pair_analysis']
            self.safe_print(f"   Volume Ratio: {pair.get('volume_ratio', 0):.2f}x")
            self.safe_print(f"   RSI: {pair.get('rsi', 50):.1f}")
            self.safe_print(f"   Volatility: {pair.get('volatility', 0):.1%}")
            self.safe_print(f"   Market Structure: {pair.get('market_structure', 'Unknown')}")
    
    def save_strategy_comparison(self):
        """Save strategy comparison data for analysis"""
        if not self.strategy_comparison_log:
            return
        
        comparison_file = 'logs/strategy_comparison.json'
        
        try:
            # Load existing data
            existing_data = []
            if os.path.exists(comparison_file):
                with open(comparison_file, 'r') as f:
                    existing_data = json.load(f)
            
            # Append new data
            existing_data.extend(self.strategy_comparison_log)
            
            # Keep only last 10000 records
            existing_data = existing_data[-10000:]
            
            # Save updated data
            with open(comparison_file, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)
            
            self.safe_print(f"📊 Strategy comparison data saved ({len(self.strategy_comparison_log)} new records)")
            self.strategy_comparison_log = []  # Clear buffer
            
        except Exception as e:
            self.safe_print(f"❌ Error saving strategy comparison: {e}")

def main():
    """Main entry point for Enhanced Single-Pair Trading Bot"""
    print("🚀 Enhanced Single-Pair Crypto Trading Bot v3.0")
    print("=" * 80)
    
    # Validate configuration
    if not API_KEY or not API_SECRET:
        print("❌ Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env file")
        return
    
    # Initialize and run bot
    bot = EnhancedSinglePairBot()
    
    if bot.initialize_bot():
        bot.main_trading_loop()
    else:
        print("❌ Bot initialization failed")

# Additional utility functions for standalone execution
def run_bot_loop(is_running_check):
    """Compatibility function for external controllers"""
    bot = EnhancedSinglePairBot()
    if bot.initialize_bot():
        loop_count = 0
        while is_running_check():
            try:
                loop_count += 1
                
                # Get market data
                market_data = bot.get_market_data()
                if not market_data:
                    time.sleep(30)
                    continue
                
                # Analyze and execute
                analysis_results = bot.analyze_market(market_data)
                bot.display_analysis_summary(analysis_results)
                
                if bot.in_position:
                    bot.monitor_position(market_data)
                else:
                    decision = bot.make_trading_decision(analysis_results)
                    if decision['final_signal'] != "HOLD":
                        bot.execute_entry_trade(decision, market_data)
                
                # Summary every 10 loops
                if loop_count % 10 == 0:
                    bot.display_session_summary()
                
                time.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                bot.safe_print(f"❌ Loop error: {e}")
                time.sleep(60)
    
    return True

def initialize_bot():
    """Compatibility function for external controllers"""
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = TESTNET_URL
        client.get_server_time()
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

if __name__ == "__main__":
    main()