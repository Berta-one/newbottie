# robust_bot.py - Never-Stop Railway Trading Bot with Keep-Alive
import time
import os
import json
import signal
import sys
import subprocess
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
MIN_BALANCE_USD = float(os.getenv("MIN_BALANCE_USD", "10.0"))
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "30"))  # 30 seconds
RAILWAY_URL = os.getenv("RAILWAY_URL", "")  # Your Railway app URL for keep-alive

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

class RobustTradingBot:
    def __init__(self):
        self.running = False
        self.scan_count = 0
        self.client = None
        self.keep_alive_thread = None
        self.last_heartbeat = datetime.now()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.create_log_directories()
        self.initialize_client()
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received shutdown signal ({signum})")
        self.running = False
        sys.exit(0)
    
    def create_log_directories(self):
        """Create log directories"""
        os.makedirs('logs', exist_ok=True)
    
    def initialize_client(self):
        """Initialize Binance client with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
                    print("❌ Binance configuration missing")
                    return False
                
                self.client = Client(API_KEY, API_SECRET)
                if USE_TESTNET:
                    self.client.API_URL = "https://testnet.binance.vision/api"
                
                # Test connection
                self.client.get_account()
                print("✅ Binance client initialized and tested")
                return True
                
            except Exception as e:
                print(f"❌ Attempt {attempt + 1}: Error connecting to Binance: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait before retry
        
        print("❌ Failed to initialize Binance client after all retries")
        return False
    
    def keep_alive_ping(self):
        """Send keep-alive pings to prevent Railway from sleeping"""
        while self.running:
            try:
                # Update heartbeat
                self.last_heartbeat = datetime.now()
                
                # Log heartbeat
                self.log_bot_event('heartbeat', {
                    'scan_count': self.scan_count,
                    'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
                })
                
                # Ping Railway URL if provided (keep Railway awake)
                if RAILWAY_URL:
                    try:
                        requests.get(f"{RAILWAY_URL}/health", timeout=10)
                        print(f"💓 Keep-alive ping sent to {RAILWAY_URL}")
                    except:
                        pass  # Silent fail for keep-alive
                
                # Self-ping (keep process active)
                print(f"💓 Heartbeat #{self.scan_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Wait 5 minutes between heartbeats
                time.sleep(300)
                
            except Exception as e:
                print(f"⚠️ Keep-alive error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def start_keep_alive(self):
        """Start keep-alive thread"""
        if not self.keep_alive_thread or not self.keep_alive_thread.is_alive():
            self.keep_alive_thread = threading.Thread(target=self.keep_alive_ping, daemon=True)
            self.keep_alive_thread.start()
            print("💓 Keep-alive system started")
    
    def get_portfolio(self):
        """Get portfolio from Binance with error handling"""
        if not self.client:
            return {}
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                account = self.client.get_account()
                all_prices = self.client.get_all_tickers()
                price_dict = {ticker['symbol']: float(ticker['price']) for ticker in all_prices}
                
                portfolio = {}
                
                for balance in account['balances']:
                    asset = balance['asset']
                    free_balance = float(balance['free'])
                    locked_balance = float(balance['locked'])
                    total_balance = free_balance + locked_balance
                    
                    if total_balance > 0:
                        if asset == 'USDT':
                            portfolio[asset] = {
                                'balance': total_balance,
                                'price_usd': 1.0,
                                'usd_value': total_balance,
                                'symbol': 'USDT'
                            }
                        else:
                            trading_symbol = f"{asset}USDT"
                            if trading_symbol in price_dict:
                                price_usd = price_dict[trading_symbol]
                                usd_value = total_balance * price_usd
                                
                                if usd_value >= MIN_BALANCE_USD:
                                    portfolio[asset] = {
                                        'balance': total_balance,
                                        'price_usd': price_usd,
                                        'usd_value': usd_value,
                                        'symbol': trading_symbol
                                    }
                
                return portfolio
                
            except Exception as e:
                print(f"❌ Portfolio fetch attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait before retry
        
        print("❌ Failed to fetch portfolio after all retries")
        return {}
    
    def analyze_opportunity(self, symbol):
        """Analyze trading opportunity with error handling"""
        if not self.client:
            return None
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get 2 hours of 1-minute data
                klines = self.client.get_klines(symbol=symbol, interval='1m', limit=120)
                
                if len(klines) < 120:
                    return None
                
                # Calculate price change over 2 hours
                open_price = float(klines[0][1])
                close_price = float(klines[-1][4])
                change_pct = ((close_price - open_price) / open_price) * 100
                
                # Calculate volume ratio
                volumes = [float(kline[5]) for kline in klines[-20:]]
                avg_volume = sum(volumes) / len(volumes)
                current_volume = float(klines[-1][5])
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                
                # Generate signal
                signal = "HOLD"
                confidence = 0.5
                
                if abs(change_pct) >= 5.0 and volume_ratio >= 1.5:
                    if change_pct >= 5.0:
                        signal = "BUY_LONG"
                        confidence = min(0.95, 0.6 + (change_pct - 5) * 0.05)
                    elif change_pct <= -5.0:
                        signal = "BUY_SHORT"
                        confidence = min(0.95, 0.6 + (abs(change_pct) - 5) * 0.05)
                
                return {
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': confidence,
                    'change_pct': change_pct,
                    'volume_ratio': volume_ratio,
                    'current_price': close_price
                }
                
            except Exception as e:
                print(f"❌ Analysis attempt {attempt + 1} for {symbol} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
        
        print(f"❌ Failed to analyze {symbol} after all retries")
        return None
    
    def scan_portfolio(self):
        """Scan portfolio for opportunities"""
        portfolio = self.get_portfolio()
        opportunities = []
        
        if not portfolio:
            return opportunities
        
        for asset, data in portfolio.items():
            if asset == 'USDT':
                continue
            
            opportunity = self.analyze_opportunity(data['symbol'])
            
            if opportunity and opportunity['signal'] != 'HOLD':
                opportunity.update({
                    'asset': asset,
                    'balance': data['balance'],
                    'usd_value': data['usd_value']
                })
                opportunities.append(opportunity)
        
        return opportunities
    
    def log_scan_result(self, opportunities):
        """Log scan results to file"""
        scan_result = {
            'timestamp': datetime.now().isoformat(),
            'scan_count': self.scan_count,
            'opportunities_found': len(opportunities),
            'opportunities': opportunities,
            'bot_uptime_seconds': (datetime.now() - self.start_time).total_seconds()
        }
        
        try:
            # Write to current scan log
            with open('logs/robust_bot_scans.log', 'a') as f:
                f.write(f"{json.dumps(scan_result)}\n")
            
            # Write to status file (for dashboard)
            with open('logs/bot_status.json', 'w') as f:
                json.dump({
                    'running': True,
                    'scan_count': self.scan_count,
                    'last_scan': datetime.now().isoformat(),
                    'opportunities': opportunities,
                    'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
                }, f)
                
        except Exception as e:
            print(f"❌ Error logging scan result: {e}")
    
    def log_bot_event(self, event, data=None):
        """Log bot events"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'scan_count': self.scan_count,
            'data': data
        }
        
        try:
            with open('logs/robust_bot_events.log', 'a') as f:
                f.write(f"{json.dumps(log_entry)}\n")
        except:
            pass  # Silent fail for event logging
    
    def run_continuous(self):
        """Run continuous scanning loop with robust error handling"""
        self.running = True
        self.start_time = datetime.now()
        
        print("🚀 Robust Trading Bot Started")
        print(f"📊 Scan Interval: {SCAN_INTERVAL} seconds")
        print(f"🔗 Mode: {'Testnet' if USE_TESTNET else 'Live Trading'}")
        print(f"💓 Keep-alive: Enabled")
        print("=" * 60)
        
        # Start keep-alive system
        self.start_keep_alive()
        
        self.log_bot_event('bot_started', {
            'scan_interval': SCAN_INTERVAL,
            'testnet': USE_TESTNET,
            'keep_alive': True
        })
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        try:
            while self.running:
                try:
                    self.scan_count += 1
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    print(f"\n🔄 [{current_time}] Scan #{self.scan_count}")
                    
                    # Perform scan
                    opportunities = self.scan_portfolio()
                    
                    # Reset error counter on successful scan
                    consecutive_errors = 0
                    
                    # Log results
                    self.log_scan_result(opportunities)
                    
                    # Display results
                    if opportunities:
                        print(f"🎯 Found {len(opportunities)} trading opportunities:")
                        for opp in opportunities:
                            print(f"   {opp['asset']}: {opp['signal']} "
                                  f"({opp['confidence']:.1%} confidence, "
                                  f"{opp['change_pct']:+.2f}% change)")
                    else:
                        print("😴 No trading opportunities found")
                    
                    # Show uptime
                    uptime = datetime.now() - self.start_time
                    print(f"⏱️  Bot uptime: {uptime.total_seconds():.0f} seconds")
                    print(f"⏱️  Waiting {SCAN_INTERVAL} seconds until next scan...")
                    
                    # Wait for next scan
                    time.sleep(SCAN_INTERVAL)
                    
                except Exception as scan_error:
                    consecutive_errors += 1
                    print(f"❌ Scan error #{consecutive_errors}: {scan_error}")
                    
                    self.log_bot_event('scan_error', {
                        'error': str(scan_error),
                        'consecutive_errors': consecutive_errors
                    })
                    
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"🔴 Too many consecutive errors ({consecutive_errors}). Attempting restart...")
                        
                        # Try to reinitialize client
                        if self.initialize_client():
                            consecutive_errors = 0
                            print("✅ Client reinitialized successfully")
                        else:
                            print("❌ Client reinitialization failed. Continuing anyway...")
                    
                    # Wait longer on error
                    time.sleep(min(60, consecutive_errors * 10))
                
        except KeyboardInterrupt:
            print(f"\n🛑 Bot stopped by user after {self.scan_count} scans")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            self.log_bot_event('fatal_error', {'error': str(e)})
        finally:
            self.running = False
            self.log_bot_event('bot_stopped', {
                'final_scan_count': self.scan_count,
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            })
            print("🔴 Robust Trading Bot Stopped")

def create_health_endpoint():
    """Create a simple health endpoint to keep Railway happy"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Bot is alive')
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            pass  # Suppress HTTP logs
    
    def run_server():
        port = int(os.getenv('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        print(f"💓 Health endpoint running on port {port}")
        server.serve_forever()
    
    health_thread = threading.Thread(target=run_server, daemon=True)
    health_thread.start()

def main():
    """Main entry point"""
    print("🎯 Robust Background Crypto Trading Bot")
    print("=" * 50)
    
    # Start health endpoint for Railway
    create_health_endpoint()
    
    # Validate configuration
    if not API_KEY or not API_SECRET:
        print("❌ Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set")
        return
    
    if not BINANCE_AVAILABLE:
        print("❌ Error: python-binance library not available")
        print("Install with: pip install python-binance")
        return
    
    # Create and run bot
    bot = RobustTradingBot()
    bot.run_continuous()

if __name__ == "__main__":
    main()