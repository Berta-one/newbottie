# hybrid_bot.py - Complete Dashboard + Never-Stop Background Bot + Manual Trading
import os

# FORCE OVERRIDE (add to top of your script)
os.environ['PAPER_TRADING'] = 'False'
os.environ['TEST_MODE'] = 'False'
os.environ['MIN_CONFIDENCE'] = '0.65'
os.environ['SCAN_INTERVAL'] = '60'

print("🚨 FORCED OVERRIDES APPLIED")
import streamlit as st
import threading
import time
import json
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px

# Load environment variables
load_dotenv()

# Configuration
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
MIN_BALANCE_USD = float(os.getenv("MIN_BALANCE_USD", "10.0"))
SCAN_INTERVAL = 60  # 60 seconds - reduced API calls

# Check for Binance library
try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# Initialize session state
if 'dashboard_password' not in st.session_state:
    st.session_state['dashboard_password'] = 'bottie'  # Default password
if 'password_authenticated' not in st.session_state:
    st.session_state['password_authenticated'] = False
if 'background_bot_running' not in st.session_state:
    st.session_state['background_bot_running'] = False
if 'background_bot_thread' not in st.session_state:
    st.session_state['background_bot_thread'] = None
if 'selected_strategy' not in st.session_state:
    st.session_state['selected_strategy'] = 'Breakout'
if 'settings_risk_level' not in st.session_state:
    st.session_state['settings_risk_level'] = 'Balanced'

class RobustBackgroundBot:
    """Never-stop background trading bot with robust error handling"""
    
    def __init__(self):
        self.running = False
        self.scan_count = 0
        self.client = None
        self.start_time = datetime.now()
        self.heartbeat_count = 0
        self.last_heartbeat = datetime.now()
        self.create_log_directories()
        self.initialize_client()

        # Add rate limiting
        self.last_portfolio_fetch = 0
        self.portfolio_cache = {}
        self.portfolio_cache_duration = 60  # Cache for 60 seconds
        self.last_price_fetch = {}
        self.price_cache = {}
        self.price_cache_duration = 30  # Cache prices for 30 seconds
    
    def create_log_directories(self):
        """Create log directories"""
        os.makedirs('logs', exist_ok=True)
    
    def initialize_client(self):
        """Initialize Binance client with error handling"""
        if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
            return False
        
        try:
            self.client = Client(API_KEY, API_SECRET)
            if USE_TESTNET:
                self.client.API_URL = "https://testnet.binance.vision/api"
            return True
        except Exception as e:
            self.log_to_console(f"❌ Error connecting to Binance: {e}")
            return False
    
    def log_to_console(self, message):
        """Log message to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        try:
            with open('logs/console_output.log', 'a', encoding='utf-8') as f:
                f.write(f"{log_line}\n")
        except:
            pass
    
    def start_keep_alive(self):
        """Start heartbeat system"""
        def heartbeat_loop():
            while self.running:
                try:
                    self.heartbeat_count += 1
                    self.last_heartbeat = datetime.now()
                    self.log_to_console(f"💓 Heartbeat #{self.heartbeat_count} - Bot alive and scanning")
                    time.sleep(60)  # Heartbeat every minute
                except:
                    break
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
    
    def get_portfolio_balances(self):
        """Get portfolio balances with rate limiting and caching"""
        current_time = time.time()
        
        # Use cached portfolio if recent
        if (current_time - self.last_portfolio_fetch) < self.portfolio_cache_duration:
            if self.portfolio_cache:
                self.log_to_console(f"[CACHE] Using cached portfolio data ({len(self.portfolio_cache)} assets)")
                return self.portfolio_cache
        
        if not self.client:
            return {}
        
        try:
            # Rate limiting - wait if needed
            time_since_last = current_time - self.last_portfolio_fetch
            if time_since_last < 5:  # Minimum 5 seconds between portfolio fetches
                wait_time = 5 - time_since_last
                self.log_to_console(f"[RATE_LIMIT] Waiting {wait_time:.1f}s before portfolio fetch")
                time.sleep(wait_time)
            
            self.log_to_console("[API] Fetching account balances...")
            account = self.client.get_account()
            balances = {}
            
            # Get all non-zero balances first
            non_zero_assets = []
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    non_zero_assets.append({
                        'asset': asset,
                        'balance': total,
                        'free': free,
                        'locked': locked
                    })
            
            self.log_to_console(f"[API] Found {len(non_zero_assets)} assets with balances")
            
            # Get prices for assets in batches to avoid rate limits
            for i, asset_data in enumerate(non_zero_assets):
                asset = asset_data['asset']
                
                try:
                    if asset == 'USDT':
                        price = 1.0
                    else:
                        # Use cached price if available and recent
                        cache_key = f"{asset}USDT"
                        if (cache_key in self.price_cache and 
                            current_time - self.last_price_fetch.get(cache_key, 0) < self.price_cache_duration):
                            price = self.price_cache[cache_key]
                            self.log_to_console(f"[CACHE] Using cached price for {asset}: ${price:.4f}")
                        else:
                            # Add small delay between price requests
                            if i > 0:
                                time.sleep(0.1)  # 100ms delay between requests
                            
                            ticker = f"{asset}USDT"
                            price_data = self.client.get_symbol_ticker(symbol=ticker)
                            price = float(price_data['price'])
                            
                            # Cache the price
                            self.price_cache[cache_key] = price
                            self.last_price_fetch[cache_key] = current_time
                            
                            self.log_to_console(f"[API] Fetched price for {asset}: ${price:.4f}")
                    
                    usd_value = asset_data['balance'] * price
                    
                    if usd_value >= MIN_BALANCE_USD:
                        balances[asset] = {
                            'balance': asset_data['balance'],
                            'price_usd': price,
                            'usd_value': usd_value,
                            'free': asset_data['free'],
                            'locked': asset_data['locked']
                        }
                        
                except Exception as e:
                    self.log_to_console(f"⚠️ Error getting price for {asset}: {e}")
                    continue
            
            # Update cache
            self.portfolio_cache = balances
            self.last_portfolio_fetch = current_time
            
            self.log_to_console(f"[API] Portfolio updated: {len(balances)} assets worth ${sum(b['usd_value'] for b in balances.values()):.2f}")
            return balances
            
        except Exception as e:
            self.log_to_console(f"❌ Error getting portfolio: {e}")
            
            # Return cached data if available
            if self.portfolio_cache:
                self.log_to_console("[FALLBACK] Using cached portfolio due to API error")
                return self.portfolio_cache
            
            return {}

    def scan_for_opportunities(self):
        """Scan for trading opportunities with rate limiting"""
        portfolio = self.get_portfolio_balances()
        
        # Get current strategy settings - check override first
        selected_strategy = 'Breakout'
        risk_level = 'Balanced'
        
        # Priority 1: Check override file
        try:
            override_path = 'logs/strategy_override.json'
            if os.path.exists(override_path):
                with open(override_path, 'r') as f:
                    override_data = json.load(f)
                if override_data.get('active', False):
                    selected_strategy = override_data.get('strategy', 'Breakout')
                    risk_level = override_data.get('risk_level', 'Balanced')
                    self.log_to_console(f"[STRATEGY] Using OVERRIDE: {selected_strategy}/{risk_level}")
        except Exception as e:
            self.log_to_console(f"[STRATEGY] Error reading override: {e}")
        
        # Priority 2: If no override, use bot status
        if selected_strategy == 'Breakout' and risk_level == 'Balanced':
            status = load_bot_status()
            selected_strategy = status.get('latest_strategy', 'Breakout')
            risk_level = status.get('latest_risk_level', 'Balanced')
            self.log_to_console(f"[STRATEGY] Using bot status: {selected_strategy}/{risk_level}")
        
        self.log_to_console(f"[SCAN] Strategy: {selected_strategy} | Risk: {risk_level} | Portfolio assets: {len(portfolio)}")
        
        opportunities = []
        
        # More lenient thresholds
        base_thresholds = {
            'Breakout': {'change': 0.5, 'volume': 0.8, 'confidence': 0.3},
            'Scalping': {'change': 0.3, 'volume': 0.7, 'confidence': 0.25},
            'Swing': {'change': 0.8, 'volume': 0.6, 'confidence': 0.35},
        }
        
        risk_modifiers = {
            'Conservative': 0.7,
            'Balanced': 1.0,
            'Aggressive': 1.3,
        }
        
        thresholds = base_thresholds.get(selected_strategy, base_thresholds['Breakout']).copy()
        modifier = risk_modifiers.get(risk_level, 1.0)
        
        # Apply risk modifier
        thresholds['change'] *= modifier
        thresholds['volume'] *= modifier
        thresholds['confidence'] *= modifier
        
        self.log_to_console(f"[SCAN] Thresholds: change={thresholds['change']:.2f}%, volume={thresholds['volume']:.2f}x")
        
        # Limit to top 5 assets by value to reduce API calls
        sorted_assets = sorted(
            [(asset, data) for asset, data in portfolio.items() if asset != 'USDT'],
            key=lambda x: x[1]['usd_value'],
            reverse=True
        )[:5]  # Only analyze top 5 assets
        
        self.log_to_console(f"[SCAN] Analyzing top {len(sorted_assets)} assets by value")
        
        for i, (asset, data) in enumerate(sorted_assets):
            try:
                symbol = f"{asset}USDT"
                
                # Add delay between API calls
                if i > 0:
                    time.sleep(0.2)  # 200ms delay
                
                # Get recent price data - reduced to minimize API calls
                klines = self.client.get_klines(symbol=symbol, interval='5m', limit=12)  # 1 hour of 5min candles
                
                if len(klines) >= 6:
                    # Calculate price change over 30 minutes (6 * 5min candles)
                    current_price = float(klines[-1][4])
                    price_30m_ago = float(klines[-6][4])
                    change_pct = ((current_price - price_30m_ago) / price_30m_ago) * 100
                    
                    # Simple volume calculation
                    recent_volume = sum([float(k[5]) for k in klines[-3:]])  # Last 15 minutes
                    prev_volume = sum([float(k[5]) for k in klines[-6:-3]])  # Previous 15 minutes
                    
                    volume_ratio = recent_volume / prev_volume if prev_volume > 0 else 1
                    
                    # Confidence calculation
                    confidence = min(0.95, 0.4 + (abs(change_pct) / 5))
                    
                    self.log_to_console(f"[SCAN] {asset}: change={change_pct:.3f}%, volume={volume_ratio:.2f}x, conf={confidence:.3f}")
                    
                    # Check criteria
                    if (abs(change_pct) >= thresholds['change'] and 
                        volume_ratio >= thresholds['volume'] and 
                        confidence >= thresholds['confidence']):
                        
                        signal = "BUY" if change_pct > 0 else "SELL"
                        
                        opportunity = {
                            'asset': asset,
                            'signal': signal,
                            'confidence': confidence,
                            'current_price': current_price,
                            'change_pct': change_pct,
                            'volume_ratio': volume_ratio,
                            'balance': data['balance'],
                            'usd_value': data['usd_value'],
                            'timestamp': datetime.now().isoformat(),
                            'strategy_used': selected_strategy,
                            'risk_level_used': risk_level,
                            'timeframe': '30m'
                        }
                        
                        opportunities.append(opportunity)
                        self.log_to_console(f"[OPPORTUNITY] {asset} {signal} - {change_pct:.3f}% | {volume_ratio:.2f}x")
                        
            except Exception as e:
                self.log_to_console(f"⚠️ Error analyzing {asset}: {e}")
                continue
        
        # Create test opportunity if none found
        if len(opportunities) == 0 and len(portfolio) > 0:
            test_asset = next((asset for asset in portfolio.keys() if asset != 'USDT'), None)
            if test_asset:
                opportunities.append({
                    'asset': test_asset,
                    'signal': 'BUY',
                    'confidence': 0.6,
                    'current_price': portfolio[test_asset]['price_usd'],
                    'change_pct': 0.5,
                    'volume_ratio': 1.2,
                    'balance': portfolio[test_asset]['balance'],
                    'usd_value': portfolio[test_asset]['usd_value'],
                    'timestamp': datetime.now().isoformat(),
                    'strategy_used': selected_strategy,
                    'risk_level_used': risk_level,
                    'timeframe': '30m',
                    'is_test': True
                })
                self.log_to_console(f"[TEST] Created test opportunity for {test_asset}")
        
        self.log_to_console(f"[SCAN] Complete: {len(opportunities)} opportunities found")
        return portfolio, opportunities

    def save_status(self, portfolio, opportunities):
        """Save current status to file for dashboard"""
        # Get strategy from override file if it exists
        override_strategy = None
        override_risk = None
        try:
            override_path = 'logs/strategy_override.json'
            if os.path.exists(override_path):
                with open(override_path, 'r') as f:
                    override_data = json.load(f)
                if override_data.get('active', False):
                    override_strategy = override_data.get('strategy')
                    override_risk = override_data.get('risk_level')
                    self.log_to_console(f"[OVERRIDE] Using strategy override: {override_strategy}/{override_risk}")
        except Exception as e:
            self.log_to_console(f"[OVERRIDE] Error reading override: {e}")
        
        # Use override if available, otherwise use previous values
        final_strategy = override_strategy if override_strategy else st.session_state.get('selected_strategy', 'Breakout')
        final_risk = override_risk if override_risk else st.session_state.get('settings_risk_level', 'Balanced')
        status = {
            'timestamp': datetime.now().isoformat(),
            'running': self.running,
            'scan_count': self.scan_count,
            'opportunities': opportunities,
            'portfolio': portfolio,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'heartbeat_count': self.heartbeat_count,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'latest_strategy': final_strategy,
            'latest_risk_level': final_risk
        }
        
        try:
            status_path = 'logs/bot_status.json'
            with open(status_path, 'w') as f:
                json.dump(status, f, indent=2)
            with open('logs/robust_bot_scans.log', 'a') as f:
                f.write(f"{json.dumps(status)}\n")
        except Exception as e:
            self.log_to_console(f"❌ Error saving status: {e}")

    def run_continuous(self):
        """Main bot loop with rate limit handling"""
        self.running = True
        self.start_time = datetime.now()
        
        self.log_to_console("🚀 Robust Trading Bot Started")
        self.log_to_console(f"📊 Scan Interval: {SCAN_INTERVAL} seconds")
        self.log_to_console(f"🔗 Mode: {'Testnet' if USE_TESTNET else 'Live Trading'}")
        self.log_to_console("=" * 60)
        
        # Start heartbeat system
        self.start_keep_alive()
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.running:
            try:
                self.scan_count += 1
                self.log_to_console(f"🔍 Starting scan #{self.scan_count}")
                
                # Perform scan
                portfolio, opportunities = self.scan_for_opportunities()
                
                # Save status
                self.save_status(portfolio, opportunities)
                
                # Log results
                self.log_to_console(f"✅ Scan #{self.scan_count} complete - {len(portfolio)} assets, {len(opportunities)} opportunities")
                
                # Reset error counter
                consecutive_errors = 0
                
                # Wait for next scan
                time.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                consecutive_errors += 1
                error_msg = str(e)
                
                # Handle rate limit errors specifically
                if "Too much request weight" in error_msg or "code=-1003" in error_msg:
                    self.log_to_console(f"⚠️ Rate limit hit - waiting 60 seconds before retry...")
                    time.sleep(60)
                    consecutive_errors = 0
                elif "code=-1021" in error_msg:
                    self.log_to_console(f"⚠️ Timestamp error - waiting 5 seconds...")
                    time.sleep(5)
                    consecutive_errors = 0
                else:
                    self.log_to_console(f"❌ Scan #{self.scan_count} error: {e}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        self.log_to_console(f"🛑 Too many consecutive errors. Stopping bot.")
                        break
                    
                    # Progressive backoff
                    error_delay = min(300, 30 * consecutive_errors)
                    self.log_to_console(f"⏰ Waiting {error_delay} seconds before retry...")
                    time.sleep(error_delay)
        
        self.log_to_console("🛑 Background bot stopped")
    
    def stop(self):
        """Stop the background bot"""
        self.running = False

# Global bot instance
if 'background_bot' not in st.session_state:
    st.session_state['background_bot'] = RobustBackgroundBot()

def start_background_bot():
    """Start background bot in thread"""
    if not st.session_state['background_bot_running']:
        bot = st.session_state['background_bot']
        thread = threading.Thread(target=bot.run_continuous, daemon=True)
        thread.start()
        st.session_state['background_bot_thread'] = thread
        st.session_state['background_bot_running'] = True
        return True
    return False

def stop_background_bot():
    """Stop background bot"""
    if st.session_state['background_bot_running']:
        bot = st.session_state['background_bot']
        bot.stop()
        st.session_state['background_bot_running'] = False
        return True
    return False

def get_tailscale_ip():
    """Get Tailscale IP for remote access"""
    try:
        output = subprocess.check_output("tailscale ip -4", shell=True, text=True).strip()
        return output.splitlines()[0]
    except:
        return "Unavailable"

def load_logs(log_file, max_lines=200):
    """Load log file contents"""
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.readlines()[-max_lines:]
    return ["No logs found."]

def load_trade_data():
    """Load trade performance data"""
    log_path = "logs/single_pair_performance.json"
    try:
        df = pd.read_json(log_path, lines=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        return df
    except Exception:
        return pd.DataFrame()

def load_bot_status():
    """Load bot status from file"""
    try:
        if os.path.exists('logs/bot_status.json'):
            with open('logs/bot_status.json', 'r') as f:
                return json.load(f)
    except:
        pass
    
    return {
        'timestamp': datetime.now().isoformat(),
        'running': False,
        'scan_count': 0,
        'opportunities': [],
        'portfolio': {},
        'uptime_seconds': 0,
        'heartbeat_count': 0,
        'last_heartbeat': datetime.now().isoformat(),
        'latest_strategy': 'Breakout',
        'latest_risk_level': 'Balanced'
    }

def get_gbp_exchange_rate():
    """Get USD to GBP exchange rate"""
    try:
        import requests
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return response.json()['rates']['GBP']
    except:
        return 0.79

def color_line(line):
    """Color code log lines"""
    if "error" in line.lower():
        return f":red[{line.strip()}]"
    elif any(x in line.lower() for x in ["profit", "+", "✅", "success"]):
        return f":green[{line.strip()}]"
    elif any(x in line.lower() for x in ["heartbeat", "💓"]):
        return f":blue[{line.strip()}]"
    elif "🔍" in line or "scan" in line.lower():
        return f":orange[{line.strip()}]"
    return f"{line.strip()}"

def simulate_market_analysis(portfolio):
    """Simulate market condition analysis"""
    if not portfolio:
        return "UNCERTAIN", 0.5, 2.0
    
    # Simple volatility calculation based on portfolio size
    volatility = min(5.0, len(portfolio) * 0.5 + 1.0)
    
    if volatility > 3.5:
        condition = "HIGH_VOLATILITY"
        score = 0.7
    elif volatility > 2.0:
        condition = "CONSOLIDATING"
        score = 0.6
    else:
        condition = "BULL_TRENDING"
        score = 0.8
    
    return condition, score, volatility

def render_portfolio_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility):
    """Render portfolio overview tab"""
    st.header("💼 Portfolio Overview")
    st.caption("Live portfolio analysis with dynamic risk management")
    
    # Define market explanations
    market_explanations = {
        "BULL_TRENDING": {
            "emoji": "🟢",
            "description": "Bullish Market",
            "explanation": "Assets are generally trending upward with positive momentum.",
            "best_strategies": ["Swing", "Breakout"],
            "risk_level": "Medium to High"
        },
        "BEAR_TRENDING": {
            "emoji": "🔴", 
            "description": "Bearish Market",
            "explanation": "Assets are trending downward with negative momentum.",
            "best_strategies": ["Conservative", "Scalping"],
            "risk_level": "Low"
        },
        "HIGH_VOLATILITY": {
            "emoji": "⚡",
            "description": "High Volatility",
            "explanation": "Rapid price movements in both directions.",
            "best_strategies": ["Scalping", "Breakout"],
            "risk_level": "High"
        },
        "CONSOLIDATING": {
            "emoji": "🟡",
            "description": "Consolidating",
            "explanation": "Prices are moving sideways in a range.",
            "best_strategies": ["Scalping", "Balanced"],
            "risk_level": "Medium"
        },
        "UNCERTAIN": {
            "emoji": "❓",
            "description": "Uncertain Market",
            "explanation": "Mixed signals and unclear direction.",
            "best_strategies": ["Conservative", "Balanced"],
            "risk_level": "Low to Medium"
        }
    }
    
    # Get current strategy settings
    status = load_bot_status()
    actual_strategy = status.get('latest_strategy', 'Breakout')
    actual_risk = status.get('latest_risk_level', 'Balanced')
    
    # Determine profile
    if market_condition == "BULL_TRENDING":
        profile = "Swing"
    elif market_condition == "BEAR_TRENDING":
        profile = "Conservative"
    elif market_condition == "HIGH_VOLATILITY":
        profile = "Scalping"
    else:
        profile = "Balanced"
    
    if not portfolio:
        st.warning("⚠️ No portfolio data available.")
        # Show metrics even with no data
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💷 Portfolio Value", "£0.00")
        with col2:
            condition_color = "🟢" if condition_score > 0.6 else "🟡" if condition_score > 0.4 else "🔴"
            st.metric(f"{condition_color} Market", market_condition.replace('_', ' ').title())
        with col3:
            st.metric("📈 Volatility", f"{avg_volatility:.1f}%")
        with col4:
            st.metric("🎯 Active Profile", profile)
        return
    
    # Calculate totals
    total_usd = sum(coin['usd_value'] for coin in portfolio.values())
    total_gbp = total_usd * gbp_rate
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💷 Portfolio Value", f"£{total_gbp:,.2f}")
    with col2:
        condition_color = "🟢" if condition_score > 0.6 else "🟡" if condition_score > 0.4 else "🔴"
        st.metric(f"{condition_color} Market", market_condition.replace('_', ' ').title())
    with col3:
        st.metric("📈 Volatility", f"{avg_volatility:.1f}%")
    with col4:
        st.metric("🎯 Active Profile", profile)
    
    st.divider()
    
    # Market Analysis
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Market Analysis")
        current_market = market_explanations.get(market_condition, market_explanations["UNCERTAIN"])
        st.write(f"**{current_market['emoji']} {current_market['description']}**")
        st.write(current_market['explanation'])
        st.write(f"• **Best Strategies:** {', '.join(current_market['best_strategies'])}")
        st.write(f"• **Risk Level:** {current_market['risk_level']}")
    
    with col2:
        st.subheader("🎛️ Your Current Settings")
        st.success(f"**🚀 {actual_strategy} Strategy**")
        st.info(f"**Risk Level:** {actual_risk}")
    
    # Portfolio holdings
    st.subheader("💼 Portfolio Holdings")
    
    portfolio_data = []
    for asset, data in portfolio.items():
        portfolio_data.append({
            'Asset': asset,
            'Balance': f"{data['balance']:.8f}".rstrip('0').rstrip('.'),
            'Price (USD)': f"${data['price_usd']:.4f}",
            'Value (USD)': f"${data['usd_value']:.2f}",
            'Value (GBP)': f"£{data['usd_value'] * gbp_rate:.2f}",
            'Percentage': f"{(data['usd_value'] / total_usd * 100):.1f}%"
        })
    
    df = pd.DataFrame(portfolio_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Quick action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Portfolio"):
            st.rerun()
    
    with col2:
        if st.button("⚙️ Adjust Strategy"):
            st.info("💡 Go to Settings tab to change your strategy and risk level")
    
    with col3:
        if st.button("📊 View Opportunities"):
            st.info("💡 Go to Market Indicators tab to see current trading opportunities")

def render_market_indicators_tab():
    """Enhanced market indicators tab with debugging info"""
    st.header("📊 Market Indicators & Signals")
    st.caption("Live summary of all tracked coins, signals, and movements.")
    
    # Load status
    status = load_bot_status()
    opportunities = status.get('opportunities', [])
    portfolio = status.get('portfolio', {})
    
    # Debug information
    with st.expander("🔍 Debug Information"):
        st.write(f"**Bot Status:** {'Running' if st.session_state['background_bot_running'] else 'Stopped'}")
        st.write(f"**Last Scan:** {status.get('timestamp', 'Never')}")
        st.write(f"**Scan Count:** {status.get('scan_count', 0)}")
        st.write(f"**Portfolio Assets:** {len(portfolio)}")
        st.write(f"**Opportunities Found:** {len(opportunities)}")
        
        if portfolio:
            st.write("**Portfolio Assets:**")
            for asset, data in portfolio.items():
                st.write(f"- {asset}: ${data.get('usd_value', 0):.2f}")
        
        # Show current strategy settings
        current_strategy = status.get('latest_strategy', 'Unknown')
        current_risk = status.get('latest_risk_level', 'Unknown')
        st.write(f"**Current Strategy:** {current_strategy}")
        st.write(f"**Current Risk Level:** {current_risk}")
        
        # Show raw opportunities data
        if opportunities:
            st.write("**Raw Opportunities Data:**")
            st.json(opportunities)
    
    # Bot status
    if st.session_state['background_bot_running']:
        st.success("🤖 Background bot is continuously scanning your portfolio...")
        
        # Show heartbeat info
        if 'last_heartbeat' in status:
            heartbeat_time = datetime.fromisoformat(status['last_heartbeat'])
            time_since_heartbeat = (datetime.now() - heartbeat_time).total_seconds()
            if time_since_heartbeat < 120:
                st.success(f"💓 Bot heartbeat: {int(time_since_heartbeat)}s ago")
            else:
                st.warning(f"⚠️ Bot heartbeat: {int(time_since_heartbeat)}s ago (may be stuck)")
    else:
        st.warning("🤖 Background bot is stopped. Start it in Settings to begin scanning.")
        st.info("👆 Click the sidebar 'Start Bot' button or go to Settings tab")
    
    # Manual refresh button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Opportunities"):
            st.rerun()
    
    with col2:
        if st.button("🔍 Force Scan Now"):
            if st.session_state['background_bot_running']:
                st.info("Bot is running - next scan will happen automatically")
            else:
                st.warning("Start the bot first to enable scanning")
    
    # Display opportunities
    if opportunities:
        st.success(f"🎯 Found {len(opportunities)} trading opportunities!")
        
        # Summary metrics
        buy_signals = [opp for opp in opportunities if opp['signal'] == 'BUY']
        sell_signals = [opp for opp in opportunities if opp['signal'] == 'SELL']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Opportunities", len(opportunities))
        with col2:
            st.metric("Buy Signals", len(buy_signals))
        with col3:
            st.metric("Sell Signals", len(sell_signals))
        
        st.divider()
        
        # Display each opportunity
        for i, opp in enumerate(opportunities):
            is_test = opp.get('is_test', False)
            test_label = " (TEST DATA)" if is_test else ""
            
            # Color based on signal
            if opp['signal'] == 'BUY':
                signal_color = "🟢"
            else:
                signal_color = "🔴"
            
            with st.expander(f"{signal_color} {opp['asset']} - {opp['signal']} (Confidence: {opp['confidence']:.1%}){test_label}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", f"${opp['current_price']:.4f}")
                    st.metric("Price Change", f"{opp['change_pct']:+.2f}%")
                    if is_test:
                        st.warning("⚠️ This is test data")
                
                with col2:
                    st.metric("Your Balance", f"{opp['balance']:.6f} {opp['asset']}")
                    st.metric("USD Value", f"${opp['usd_value']:.2f}")
                    st.metric("Volume Ratio", f"{opp['volume_ratio']:.2f}x")
                
                with col3:
                    st.metric("Signal Strength", opp['signal'])
                    st.metric("Confidence", f"{opp['confidence']:.1%}")
                    st.metric("Timeframe", opp.get('timeframe', 'N/A'))
                    
                # Show which strategy/risk was used
                strategy_used = opp.get('strategy_used', 'Unknown')
                risk_used = opp.get('risk_level_used', 'Unknown')
                st.info(f"📊 Strategy: {strategy_used} | Risk: {risk_used}")
                
                # Show timestamp
                timestamp = opp.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        st.caption(f"⏰ Found at: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        st.caption(f"⏰ Found at: {timestamp}")
    else:
        st.info("🔍 No trading opportunities found at this time.")
        
        # Help text
        st.markdown("""
        **Why might no opportunities be showing?**
        
        1. **Bot not running** - Check if the background bot is started
        2. **Strict thresholds** - Current settings might be too conservative
        3. **Low market volatility** - Markets might be too quiet
        4. **Small portfolio** - Need assets worth more than $10 to analyze
        5. **Recent restart** - Bot might need time to gather data
        
        **Try these steps:**
        1. Start the bot in Settings or sidebar
        2. Wait 2-3 minutes for initial scans
        3. Check the Logs tab for scanning activity
        4. Adjust strategy to 'Scalping' for more sensitive detection
        """)
        
        # Show portfolio info
        if portfolio:
            st.subheader("📊 Your Portfolio Being Monitored")
            portfolio_data = []
            for asset, data in portfolio.items():
                portfolio_data.append({
                    'Asset': asset,
                    'Balance': f"{data['balance']:.8f}".rstrip('0').rstrip('.'),
                    'USD Value': f"${data['usd_value']:.2f}",
                    'Price': f"${data['price_usd']:.4f}"
                })
            
            df = pd.DataFrame(portfolio_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ No portfolio data found. Make sure your API keys are configured and the bot is running.")

def render_manual_trading_tab():
    """Render manual trading tab with live trading capabilities"""
    st.header("📈 Manual Trading")
    st.caption("Execute trades manually with real-time market data and safety controls")
    
    # Check if API is available
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        st.error("❌ Binance API not configured. Please check your environment variables.")
        return
    
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = "https://testnet.binance.vision/api"
        
        # Test connection
        account = client.get_account()
        balances = account['balances']
        
    except Exception as e:
        st.error(f"❌ Error connecting to Binance: {e}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛒 Place Order")
        
        # Get portfolio for trading options
        portfolio_balances = {}
        for balance in balances:
            if float(balance['free']) > 0:
                portfolio_balances[balance['asset']] = {
                    'free': float(balance['free']),
                    'locked': float(balance['locked'])
                }
        
        # Trade direction
        trade_direction = st.radio("Trade Direction", ["Buy", "Sell"])
        
        if trade_direction == "Buy":
            # Buy crypto with USDT
            st.write("**Buy Cryptocurrency with USDT**")
            
            # Available cryptos to buy
            available_cryptos = ["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "DOGE"]
            selected_crypto = st.selectbox("Select Cryptocurrency", available_cryptos)
            
            # Get current USDT balance
            usdt_balance = portfolio_balances.get('USDT', {}).get('free', 0)
            st.info(f"💰 Available USDT: {usdt_balance:.2f}")
            
            # Get current price
            try:
                symbol = f"{selected_crypto}USDT"
                ticker = client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                st.success(f"💰 Current {selected_crypto} Price: ${current_price:.4f}")
                
                # Calculate quantity
                usdt_amount = st.number_input(
                    f"USDT Amount to spend",
                    min_value=10.0,
                    max_value=float(usdt_balance),
                    value=min(100.0, usdt_balance),
                    step=10.0
                )
                
                quantity = usdt_amount / current_price
                st.info(f"📊 You'll get approximately **{quantity:.6f} {selected_crypto}**")
                
            except Exception as e:
                st.error(f"Error getting price for {selected_crypto}: {e}")
                current_price = 0
                quantity = 0
        
        else:
            # Sell crypto for USDT
            st.write("**Sell Cryptocurrency for USDT**")
            
            # Available assets to sell
            available_assets = [asset for asset in portfolio_balances.keys() if asset != 'USDT' and portfolio_balances[asset]['free'] > 0]
            
            if not available_assets:
                st.warning("⚠️ No assets available to sell")
                return
            
            selected_asset = st.selectbox("Select Asset to Sell", available_assets)
            asset_balance = portfolio_balances.get(selected_asset, {}).get('free', 0)
            
            st.info(f"💰 Available {selected_asset}: {asset_balance:.8f}")
            
            # Get current price
            try:
                symbol = f"{selected_asset}USDT"
                ticker = client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                st.success(f"💰 Current {selected_asset} Price: ${current_price:.4f}")
                
                # Quantity to sell
                quantity = st.number_input(
                    f"Quantity to sell",
                    min_value=0.000001,
                    max_value=float(asset_balance),
                    value=min(float(asset_balance), float(asset_balance) * 0.1),
                    format="%.8f"
                )
                
                estimated_usdt = quantity * current_price
                st.info(f"💳 You'll receive approximately **${estimated_usdt:.2f} USDT**")
                
            except Exception as e:
                st.error(f"Error getting price for {selected_asset}: {e}")
                current_price = 0
                quantity = 0
        
        # Order type
        order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
        
        # Execute button
        if trade_direction == "Buy":
            button_text = f"🛒 Buy {quantity:.6f} {selected_crypto}"
            symbol = f"{selected_crypto}USDT"
            side = "BUY"
        else:
            button_text = f"🔥 Sell {quantity:.6f} {selected_asset}"
            symbol = f"{selected_asset}USDT"
            side = "SELL"
        
        # Validation
        can_execute = quantity > 0 and current_price > 0
        
        if st.button(button_text, type="primary", disabled=not can_execute):
            if can_execute:
                try:
                    # Execute the trade
                    if order_type == "MARKET":
                        order = client.create_order(
                            symbol=symbol,
                            side=side,
                            type="MARKET",
                            quantity=quantity
                        )
                    else:
                        order = client.create_order(
                            symbol=symbol,
                            side=side,
                            type="LIMIT",
                            timeInForce="GTC",
                            quantity=quantity,
                            price=current_price
                        )
                    
                    st.success(f"✅ Order placed successfully!")
                    st.json(order)
                    
                    # Log the trade
                    trade_data = {
                        'timestamp': datetime.now().isoformat(),
                        'type': 'manual_trade',
                        'symbol': symbol,
                        'side': side,
                        'quantity': quantity,
                        'price': current_price,
                        'order_id': order['orderId'],
                        'status': order['status']
                    }
                    
                    with open('logs/manual_trades.log', 'a') as f:
                        f.write(f"{json.dumps(trade_data)}\n")
                    
                except Exception as e:
                    st.error(f"❌ Error executing trade: {e}")
    
    with col2:
        st.subheader("💰 Account Balance")
        
        # Display balances
        balance_data = []
        for asset, balance in portfolio_balances.items():
            total_balance = balance['free'] + balance['locked']
            
            # Get USD value
            try:
                if asset == 'USDT':
                    usd_value = total_balance
                else:
                    ticker = client.get_symbol_ticker(symbol=f"{asset}USDT")
                    usd_value = total_balance * float(ticker['price'])
            except:
                usd_value = 0
            
            if usd_value >= 1:  # Only show assets worth $1+
                balance_data.append({
                    'Asset': asset,
                    'Free': f"{balance['free']:.6f}".rstrip('0').rstrip('.'),
                    'Locked': f"{balance['locked']:.6f}".rstrip('0').rstrip('.'),
                    'USD Value': f"${usd_value:.2f}"
                })
        
        if balance_data:
            df_balance = pd.DataFrame(balance_data)
            st.dataframe(df_balance, use_container_width=True, hide_index=True)
        
        # Current opportunities
        st.markdown("---")
        st.subheader("🎯 Trading Opportunities")
        
        status = load_bot_status()
        opportunities = status.get('opportunities', [])
        
        if opportunities:
            st.success(f"Found {len(opportunities)} opportunities")
            
            for opp in opportunities[:3]:  # Show top 3
                with st.expander(f"{opp['asset']} - {opp['signal']}"):
                    st.metric("Confidence", f"{opp['confidence']:.1%}")
                    st.metric("Price Change", f"{opp['change_pct']:+.2f}%")
                    st.metric("Volume Ratio", f"{opp['volume_ratio']:.2f}x")
        else:
            st.info("No opportunities found")

def get_trade_history_from_api(client, days_back=30):
    """Get trade history from Binance API with P&L calculations - FIXED for 24h limit"""
    try:
        st.info("🔍 Getting your account balances to find traded assets...")
        account = client.get_account()
        traded_assets = set()
        for balance in account['balances']:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            if free > 0 or locked > 0:
                traded_assets.add(asset)
        common_pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT', 
                      'LINKUSDT', 'LTCUSDT', 'BCHUSDT', 'XRPUSDT', 'DOGEUSDT',
                      'SOLUSDT', 'MATICUSDT', 'AVAXUSDT', 'UNIUSDT', 'ATOMUSDT']
        symbols_to_check = []
        for asset in traded_assets:
            if asset != 'USDT':
                symbols_to_check.append(f"{asset}USDT")
        for symbol in common_pairs:
            if symbol not in symbols_to_check:
                symbols_to_check.append(symbol)
        symbols_to_check = list(set(symbols_to_check))
        st.info(f"📈 Checking trades for {len(symbols_to_check)} symbols over {days_back} days")
        all_trades = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        current_time = int(datetime.now().timestamp() * 1000)
        chunk_size = 24 * 60 * 60 * 1000
        total_operations = len(symbols_to_check) * days_back
        completed_operations = 0
        for symbol_index, symbol in enumerate(symbols_to_check):
            try:
                symbol_trades = []
                for day in range(days_back):
                    try:
                        end_time = current_time - (day * chunk_size)
                        start_time = end_time - chunk_size
                        completed_operations += 1
                        progress = completed_operations / total_operations
                        progress_bar.progress(progress)
                        status_text.text(f"Checking {symbol} - Day {day+1}/{days_back} ({completed_operations}/{total_operations})")
                        trades = client.get_my_trades(symbol=symbol, startTime=start_time, endTime=end_time)
                        if trades:
                            symbol_trades.extend(trades)
                        time.sleep(0.1)
                    except Exception as e:
                        if "Invalid symbol" not in str(e) and "code=-1127" not in str(e):
                            st.warning(f"Error getting {symbol} for day {day+1}: {e}")
                        continue
                if symbol_trades:
                    st.success(f"✅ Found {len(symbol_trades)} trades for {symbol}")
                    for trade in symbol_trades:
                        all_trades.append({
                            'symbol': symbol,
                            'id': trade['id'],
                            'orderId': trade['orderId'],
                            'price': float(trade['price']),
                            'qty': float(trade['qty']),
                            'quoteQty': float(trade['quoteQty']),
                            'commission': float(trade['commission']),
                            'commissionAsset': trade['commissionAsset'],
                            'time': trade['time'],
                            'isBuyer': trade['isBuyer'],
                            'isMaker': trade['isMaker'],
                            'isBestMatch': trade['isBestMatch']
                        })
            except Exception as e:
                if "Invalid symbol" not in str(e):
                    st.warning(f"Could not get trades for {symbol}: {e}")
                continue
        progress_bar.empty()
        status_text.empty()
        if all_trades:
            all_trades.sort(key=lambda x: x['time'])
            st.success(f"✅ Found {len(all_trades)} total trades across {len(set([t['symbol'] for t in all_trades]))} symbols")
        else:
            st.info("ℹ️ No trades found in the selected period")
        return all_trades
    except Exception as e:
        st.error(f"Error fetching trade history: {e}")
        return []

def get_trade_history_simple(client, days_back=30):
    """Simple trade history using account snapshot method"""
    try:
        st.info("🔍 Using alternative method to get trade history...")
        account = client.get_account()
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = end_time - (days_back * 24 * 60 * 60 * 1000)
        symbols_to_check = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT',
            'LINKUSDT', 'LTCUSDT', 'BCHUSDT', 'XRPUSDT', 'DOGEUSDT',
            'SOLUSDT', 'MATICUSDT', 'AVAXUSDT', 'UNIUSDT', 'ATOMUSDT'
        ]
        all_trades = []
        for symbol in symbols_to_check:
            try:
                trades = client.get_my_trades(symbol=symbol, startTime=start_time, endTime=end_time)
                for trade in trades:
                    all_trades.append({
                        'symbol': symbol,
                        'id': trade['id'],
                        'orderId': trade['orderId'],
                        'price': float(trade['price']),
                        'qty': float(trade['qty']),
                        'quoteQty': float(trade['quoteQty']),
                        'commission': float(trade['commission']),
                        'commissionAsset': trade['commissionAsset'],
                        'time': trade['time'],
                        'isBuyer': trade['isBuyer'],
                        'isMaker': trade['isMaker'],
                        'isBestMatch': trade['isBestMatch']
                    })
                time.sleep(0.1)
            except:
                continue
        return all_trades
    except Exception as e:
        st.error(f"Error in simple trade history: {e}")
        return []

def get_trade_history_recent(client, days_back=7):
    """Get recent trade history - faster method for recent trades only"""
    try:
        st.info("🔍 Getting recent trade history (last 7 days)...")
        account = client.get_account()
        traded_assets = []
        for balance in account['balances']:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            if (free > 0 or locked > 0) and asset != 'USDT':
                traded_assets.append(f"{asset}USDT")
        common_recent = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT']
        for symbol in common_recent:
            if symbol not in traded_assets:
                traded_assets.append(symbol)
        traded_assets = list(set(traded_assets))
        st.info(f"📈 Checking recent trades for {len(traded_assets)} symbols")
        all_trades = []
        current_time = int(datetime.now().timestamp() * 1000)
        progress_bar = st.progress(0)
        for i, symbol in enumerate(traded_assets):
            try:
                progress_bar.progress((i + 1) / len(traded_assets))
                start_time = current_time - (24 * 60 * 60 * 1000)
                trades = client.get_my_trades(symbol=symbol, startTime=start_time, endTime=current_time)
                if trades:
                    st.success(f"✅ Found {len(trades)} recent trades for {symbol}")
                    for trade in trades:
                        all_trades.append({
                            'symbol': symbol,
                            'id': trade['id'],
                            'orderId': trade['orderId'],
                            'price': float(trade['price']),
                            'qty': float(trade['qty']),
                            'quoteQty': float(trade['quoteQty']),
                            'commission': float(trade['commission']),
                            'commissionAsset': trade['commissionAsset'],
                            'time': trade['time'],
                            'isBuyer': trade['isBuyer'],
                            'isMaker': trade['isMaker'],
                            'isBestMatch': trade['isBestMatch']
                        })
                time.sleep(0.1)
            except Exception as e:
                if "Invalid symbol" not in str(e):
                    st.warning(f"Could not get recent trades for {symbol}: {e}")
                continue
        progress_bar.empty()
        if all_trades:
            all_trades.sort(key=lambda x: x['time'])
            st.success(f"✅ Found {len(all_trades)} total recent trades")
        else:
            st.info("ℹ️ No recent trades found")
        return all_trades
    except Exception as e:
        st.error(f"Error fetching recent trade history: {e}")
        return []

def calculate_position_pnl(trades, current_prices, gbp_rate):
    """Calculate P&L for each position and individual trades"""
    positions = {}
    trade_details = []
    
    # Sort trades by time
    sorted_trades = sorted(trades, key=lambda x: x['time'])
    
    for trade in sorted_trades:
        symbol = trade['symbol']
        asset = symbol.replace('USDT', '')
        
        if symbol not in positions:
            positions[symbol] = {
                'asset': asset,
                'total_bought': 0,
                'total_sold': 0,
                'avg_buy_price': 0,
                'avg_sell_price': 0,
                'realized_pnl_usd': 0,
                'unrealized_pnl_usd': 0,
                'current_holding': 0,
                'total_commission_usd': 0,
                'trades': []
            }
        
        pos = positions[symbol]
        
        # Calculate commission in USD
        commission_usd = 0
        if trade['commissionAsset'] == 'USDT':
            commission_usd = trade['commission']
        elif trade['commissionAsset'] == asset:
            commission_usd = trade['commission'] * trade['price']
        else:
            # For BNB commission, approximate
            commission_usd = trade['commission'] * 300  # Rough BNB price
        
        pos['total_commission_usd'] += commission_usd
        
        if trade['isBuyer']:
            # Buy trade
            pos['total_bought'] += trade['qty']
            pos['avg_buy_price'] = ((pos['avg_buy_price'] * (pos['total_bought'] - trade['qty'])) + 
                                   (trade['price'] * trade['qty'])) / pos['total_bought']
            pos['current_holding'] += trade['qty']
            
            trade_type = 'BUY'
            pnl_usd = 0  # No realized P&L on buy
            
        else:
            # Sell trade
            pos['total_sold'] += trade['qty']
            if pos['total_sold'] > 0:
                pos['avg_sell_price'] = ((pos['avg_sell_price'] * (pos['total_sold'] - trade['qty'])) + 
                                        (trade['price'] * trade['qty'])) / pos['total_sold']
            
            pos['current_holding'] -= trade['qty']
            
            # Calculate realized P&L for this sell
            if pos['avg_buy_price'] > 0:
                pnl_usd = (trade['price'] - pos['avg_buy_price']) * trade['qty'] - commission_usd
                pos['realized_pnl_usd'] += pnl_usd
            else:
                pnl_usd = 0
            
            trade_type = 'SELL'
        
        # Add to trade details
        trade_details.append({
            'timestamp': pd.to_datetime(trade['time'], unit='ms'),
            'symbol': symbol,
            'asset': asset,
            'type': trade_type,
            'quantity': trade['qty'],
            'price_usd': trade['price'],
            'value_usd': trade['quoteQty'],
            'commission_usd': commission_usd,
            'pnl_usd': pnl_usd,
            'pnl_gbp': pnl_usd * gbp_rate,
            'pnl_percent': (pnl_usd / trade['quoteQty'] * 100) if trade['quoteQty'] > 0 else 0,
            'order_id': trade['orderId']
        })
        
        pos['trades'].append(trade_details[-1])
    
    # Calculate unrealized P&L for current holdings
    for symbol, pos in positions.items():
        if pos['current_holding'] > 0 and symbol in current_prices:
            current_price = current_prices[symbol]
            if pos['avg_buy_price'] > 0:
                pos['unrealized_pnl_usd'] = (current_price - pos['avg_buy_price']) * pos['current_holding']
    
    return positions, trade_details

def render_performance_tab():
    """Enhanced render performance tab with detailed P&L analysis"""
    st.header("📊 Performance & Trade Analysis")
    st.caption("Detailed P&L analysis for all your trades")
    
    # Get GBP exchange rate
    gbp_rate = get_gbp_exchange_rate()
    
    # Check if API is available
    if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
        st.error("❌ Binance API not configured for trade analysis")
        return
    
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = "https://testnet.binance.vision/api"
        
        # Get trade history with multiple options
        col1, col2 = st.columns(2)
        with col1:
            days_back = st.slider("Days of history", 1, 30, 7)
        with col2:
            method = st.selectbox("Fetch method", [
                "Recent trades (last 24h - fastest)",
                "Full history (slower but complete)",
                "Manual symbols only"
            ])
        if method == "Recent trades (last 24h - fastest)":
            with st.spinner("📥 Fetching recent trades..."):
                all_trades = get_trade_history_recent(client, 1)
        elif method == "Full history (slower but complete)":
            with st.spinner("📥 Fetching full trade history..."):
                all_trades = get_trade_history_from_api(client, days_back)
        else:
            with st.spinner("📥 Fetching trade history (manual symbols)..."):
                all_trades = get_trade_history_simple(client, days_back)
        
        if not all_trades:
            st.info("No trades found in the selected period.")
            return
        
        # Get current prices for unrealized P&L
        current_prices = {}
        unique_symbols = list(set([trade['symbol'] for trade in all_trades]))
        
        with st.spinner("💰 Getting current prices..."):
            for symbol in unique_symbols:
                try:
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    current_prices[symbol] = float(ticker['price'])
                except:
                    continue
        
        # Calculate P&L
        positions, trade_details = calculate_position_pnl(all_trades, current_prices, gbp_rate)
        
        # Create DataFrame for analysis
        df_trades = pd.DataFrame(trade_details)
        
        if df_trades.empty:
            st.info("No processed trades found.")
            return
        
        # Performance Summary
        st.subheader("📈 Performance Summary")
        
        total_realized_pnl_usd = sum([pos['realized_pnl_usd'] for pos in positions.values()])
        total_unrealized_pnl_usd = sum([pos['unrealized_pnl_usd'] for pos in positions.values()])
        total_commission_usd = sum([pos['total_commission_usd'] for pos in positions.values()])
        total_pnl_usd = total_realized_pnl_usd + total_unrealized_pnl_usd
        
        # Winning trades
        winning_trades = df_trades[df_trades['pnl_usd'] > 0]
        losing_trades = df_trades[df_trades['pnl_usd'] < 0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total P&L", 
                f"£{total_pnl_usd * gbp_rate:,.2f}", 
                delta=f"${total_pnl_usd:,.2f} USD"
            )
        
        with col2:
            st.metric(
                "Realized P&L", 
                f"£{total_realized_pnl_usd * gbp_rate:,.2f}",
                delta=f"${total_realized_pnl_usd:,.2f} USD"
            )
        
        with col3:
            win_rate = (len(winning_trades) / len(df_trades[df_trades['type'] == 'SELL']) * 100) if len(df_trades[df_trades['type'] == 'SELL']) > 0 else 0
            st.metric("Win Rate", f"{win_rate:.1f}%")
        
        with col4:
            st.metric(
                "Total Fees", 
                f"£{total_commission_usd * gbp_rate:,.2f}",
                delta=f"${total_commission_usd:,.2f} USD"
            )
        
        # Trade History Table
        st.subheader("📋 Recent Trades")
        
        # Format the display DataFrame
        display_df = df_trades.copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df['quantity'] = display_df['quantity'].apply(lambda x: f"{x:.6f}".rstrip('0').rstrip('.'))
        display_df['price_usd'] = display_df['price_usd'].apply(lambda x: f"${x:.4f}")
        display_df['value_usd'] = display_df['value_usd'].apply(lambda x: f"${x:.2f}")
        display_df['pnl_gbp'] = display_df['pnl_gbp'].apply(lambda x: f"£{x:.2f}")
        display_df['pnl_percent'] = display_df['pnl_percent'].apply(lambda x: f"{x:+.2f}%")
        
        # Reorder columns for better display
        display_columns = ['timestamp', 'asset', 'type', 'quantity', 'price_usd', 'value_usd', 'pnl_gbp', 'pnl_percent']
        display_df = display_df[display_columns]
        
        # Rename columns for display
        display_df.columns = ['Time', 'Asset', 'Type', 'Quantity', 'Price (USD)', 'Value (USD)', 'P&L (GBP)', 'P&L %']
        
        # Sort by timestamp descending (most recent first)
        display_df = display_df.sort_values('Time', ascending=False)
        
        # Display with styling
        st.dataframe(display_df.head(20), use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Error analyzing trades: {e}")
        st.info("Make sure your Binance API keys have the necessary permissions to read trade history.")

def render_logs_tab():
    """Render logs tab"""
    st.header("📡 Logs")
    st.caption("Live logs from your bot will appear here")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        refresh_rate = st.slider("🔁 Refresh every (seconds)", 5, 30, 10)
    
    with col2:
        if st.button("🔄 Manual Refresh"):
            st.rerun()
    
    # Bot status
    status = load_bot_status()
    if st.session_state['background_bot_running']:
        st.success(f"🟢 Background bot is running (Scan #{status.get('scan_count', 0)})")
        
        # Heartbeat check
        if 'last_heartbeat' in status:
            heartbeat_time = datetime.fromisoformat(status['last_heartbeat'])
            time_since_heartbeat = (datetime.now() - heartbeat_time).total_seconds()
            if time_since_heartbeat < 120:  # Within 2 minutes
                st.success(f"💓 Heartbeat active ({int(time_since_heartbeat)}s ago)")
            else:
                st.warning(f"⚠️ Last heartbeat {int(time_since_heartbeat)}s ago")
    else:
        st.warning("🔴 Background bot is stopped")
    
    # Display logs with color coding
    lines = load_logs("logs/console_output.log")
    colored_logs = []
    for line in lines:
        colored_logs.append(color_line(line))
    
    log_output = "\n".join(colored_logs[-50:])  # Show last 50 lines
    st.text_area("Recent Logs", log_output, height=400)

def force_update_strategy(strategy, risk_level):
    """Force update strategy settings in all files"""
    import os, json
    from datetime import datetime
    timestamp = datetime.now().isoformat()
    # Update bot_status.json
    try:
        status_path = 'logs/bot_status.json'
        status = {}
        if os.path.exists(status_path):
            with open(status_path, 'r') as f:
                status = json.load(f)
        status['latest_strategy'] = strategy
        status['latest_risk_level'] = risk_level
        status['last_strategy_update'] = timestamp
        status['strategy_source'] = 'user_override'
        with open(status_path, 'w') as f:
            json.dump(status, f, indent=2)
        st.success(f"✅ Updated bot_status.json: {strategy}/{risk_level}")
    except Exception as e:
        st.error(f"❌ Error updating bot_status.json: {e}")
    # Create strategy override file
    try:
        override_path = 'logs/strategy_override.json'
        override_data = {
            'strategy': strategy,
            'risk_level': risk_level,
            'timestamp': timestamp,
            'active': True
        }
        with open(override_path, 'w') as f:
            json.dump(override_data, f, indent=2)
        st.success(f"✅ Created strategy override: {strategy}/{risk_level}")
    except Exception as e:
        st.error(f"❌ Error creating strategy override: {e}")

def render_settings_tab():
    """Render settings tab"""
    st.header("⚙️ Settings")
    st.caption("Bot controls and configuration")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🤖 Background Bot Control")
        
        if st.session_state['background_bot_running']:
            st.success("✅ Background bot is RUNNING 24/7")
            st.info("Bot scans every 60 seconds automatically")
            
            if st.button("🛑 Stop Background Bot", type="secondary"):
                if stop_background_bot():
                    st.success("Background bot stopped")
                    st.rerun()
        else:
            st.warning("⏹️ Background bot is STOPPED")
            
            if st.button("▶️ Start Background Bot", type="primary"):
                if start_background_bot():
                    st.success("🚀 Background bot started!")
                    st.rerun()
        
        # Password change
        st.markdown("---")
        st.subheader("🔐 Change Dashboard Password")
        new_password = st.text_input("New Password", type="password")
        if st.button("Set New Password"):
            if new_password:
                st.session_state['dashboard_password'] = new_password
                st.success("Password updated.")
            else:
                st.warning("Password cannot be empty.")
    
    with col2:
        st.subheader("🎛️ Trading Configuration")
        
        # Get current values from bot_status.json
        current_strategy = "Unknown"
        current_risk = "Unknown"
        try:
            status_path = 'logs/bot_status.json'
            if os.path.exists(status_path):
                with open(status_path, 'r') as f:
                    status = json.load(f)
                current_strategy = status.get('latest_strategy', 'Unknown')
                current_risk = status.get('latest_risk_level', 'Unknown')
        except Exception:
            pass
        
        st.info(f"**Currently Active:** Strategy: {current_strategy}, Risk: {current_risk}")
        
        # Strategy and Risk Level Selection
        st.markdown("### 🎯 Strategy & Risk Configuration")
        
        strategy_options = ["Breakout", "Scalping", "Swing"]
        risk_options = ["Conservative", "Balanced", "Aggressive"]
        
        # User selection form
        with st.form(key="strategy_risk_form"):
            st.write("**Select New Configuration:**")
            
            selected_strategy = st.selectbox(
                "Strategy", 
                strategy_options, 
                index=strategy_options.index(st.session_state['selected_strategy']) if st.session_state['selected_strategy'] in strategy_options else 0
            )
            
            risk_level = st.selectbox(
                "Risk Level", 
                risk_options,
                index=risk_options.index(st.session_state['settings_risk_level']) if st.session_state['settings_risk_level'] in risk_options else 1
            )
            
            submitted = st.form_submit_button("✅ Apply New Strategy & Risk", type="primary")
            
            if submitted:
                # Update session state
                st.session_state['selected_strategy'] = selected_strategy
                st.session_state['settings_risk_level'] = risk_level
                
                # Update bot_status.json
                try:
                    status_path = 'logs/bot_status.json'
                    
                    if os.path.exists(status_path):
                        with open(status_path, 'r') as f:
                            status = json.load(f)
                    else:
                        status = {}
                    
                    status['latest_strategy'] = selected_strategy
                    status['latest_risk_level'] = risk_level
                    status['last_updated'] = datetime.now().isoformat()
                    
                    with open(status_path, 'w') as f:
                        json.dump(status, f, indent=2)
                    
                    st.success(f"✅ Updated! Strategy: {selected_strategy}, Risk: {risk_level}")
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error updating settings: {e}")
        
        # Manual strategy update section
        st.markdown("---")
        st.subheader("🔧 Manual Strategy Override")
        col1, col2, col3 = st.columns(3)
        with col1:
            manual_strategy = st.selectbox("Force Strategy", ["Breakout", "Scalping", "Swing"], key="manual_strategy")
        with col2:
            manual_risk = st.selectbox("Force Risk", ["Conservative", "Balanced", "Aggressive"], key="manual_risk")
        with col3:
            if st.button("🚀 FORCE UPDATE NOW", type="primary"):
                force_update_strategy(manual_strategy, manual_risk)
                st.success(f"✅ FORCED: {manual_strategy} / {manual_risk}")
                st.info("Check logs to confirm bot is using new strategy")
                time.sleep(1)
                st.rerun()

def render_strategy_tab():
    """Render strategy tab"""
    st.header("🧠 Strategy")
    st.caption("Strategy selection & configuration")
    status = load_bot_status()
    current_strategy = status.get('latest_strategy', 'Breakout')
    current_risk = status.get('latest_risk_level', 'Balanced')
    st.success(f"✅ Active Strategy: {current_strategy}")
    st.success(f"✅ Risk Level: {current_risk}")
    st.markdown("---")
    st.subheader("📊 Strategy Information")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Breakout Strategy:**")
        st.write("- Threshold: 0.5% price movement")
        st.write("- Volume: 0.8x average required")
        st.write("- Good for trending markets")
        st.write("**Scalping Strategy:**")
        st.write("- Threshold: 0.3% quick moves")
        st.write("- Volume: 0.7x average required")
        st.write("- High frequency trading")
    with col2:
        st.write("**Swing Strategy:**")
        st.write("- Threshold: 0.8% price movement")
        st.write("- Volume: 0.6x average required")
        st.write("- Longer hold periods")
        st.write("**Risk Levels:**")
        st.write("- Conservative: 0.7x thresholds")
        st.write("- Balanced: 1.0x thresholds")
        st.write("- Aggressive: 1.3x thresholds")
    st.markdown("---")
    st.subheader("🎯 Current Opportunities")
    opportunities = status.get('opportunities', [])
    if opportunities:
        st.success(f"Current opportunities: {len(opportunities)}")
        for opp in opportunities[:3]:
            strategy_used = opp.get('strategy_used', 'Unknown')
            risk_used = opp.get('risk_level_used', 'Unknown')
            st.write(f"• {opp['asset']}: {opp['signal']} (Confidence: {opp['confidence']:.1%}) - {strategy_used}/{risk_used}")
    else:
        st.info("No current opportunities detected.")

def render_health_tab():
    """Render health tab"""
    st.header("💓 Health")
    st.caption("Bot health & connection status")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🤖 Bot Status")
        if st.session_state['background_bot_running']:
            st.success("🟢 Bot is RUNNING")
        else:
            st.error("🔴 Bot is STOPPED")
        st.subheader("🔗 API Connection")
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            st.success("✅ Binance API Connected")
            mode = "Testnet" if USE_TESTNET else "Live Trading"
            st.info(f"📡 Mode: {mode}")
        else:
            st.error("❌ Binance API Not Connected")
    with col2:
        st.subheader("📊 Health Metrics")
        status = load_bot_status()
        if 'last_heartbeat' in status:
            heartbeat_time = datetime.fromisoformat(status['last_heartbeat'])
            time_since_heartbeat = (datetime.now() - heartbeat_time).total_seconds()
            if time_since_heartbeat < 120:
                st.success(f"💓 Heartbeat: Active ({int(time_since_heartbeat)}s ago)")
            else:
                st.warning(f"⚠️ Heartbeat: {int(time_since_heartbeat)}s ago")
        else:
            st.info("💓 Heartbeat: No data")
        st.metric("Total Scans", status.get('scan_count', 0))
        uptime = status.get('uptime_seconds', 0)
        st.metric("Bot Uptime", f"{uptime // 3600:.0f}h {(uptime % 3600) // 60:.0f}m")
    st.subheader("📁 Log File Status")
    if os.path.exists("logs/console_output.log"):
        st.success("✅ Log file accessible")
        with open("logs/console_output.log", "r", encoding="utf-8") as f:
            last_lines = f.readlines()[-10:]
        st.subheader("📝 Recent Log Activity")
        st.code("\n".join([line.strip() for line in last_lines]))
    else:
        st.error("❌ Log file not found")
def dashboard():
    """Main dashboard function"""
    # Get Tailscale IP and setup sidebar controls
    ts_ip = get_tailscale_ip()
    remote_url = f"http://{ts_ip}:8501" if ts_ip != "Unavailable" else "Unavailable"
    
    # Sidebar setup
    st.sidebar.markdown(f"**Tailscale IP:** `{ts_ip}`")
    st.sidebar.text_input("🔗 Access URL", value=remote_url, key="url", label_visibility="collapsed")
    st.sidebar.download_button("📥 Download Logs", data="\n".join(load_logs("logs/console_output.log")), file_name="console_output.log")

    # Bot status in sidebar
    st.sidebar.subheader("🤖 Bot Status")
    if st.session_state['background_bot_running']:
        st.sidebar.success("🟢 Bot is running")
        if st.sidebar.button("🛑 Stop Bot"):
            stop_background_bot()
            st.sidebar.info("Bot stopped.")
    else:
        st.sidebar.warning("🔴 Bot is stopped")
        if st.sidebar.button("▶️ Start Bot"):
            if start_background_bot():
                st.sidebar.success("Bot started.")
            else:
                st.sidebar.error("Failed to start bot.")

    if st.sidebar.button("🔄 Refresh Dashboard"):
        st.rerun()

    # Auto-start background bot on first load
    if not st.session_state['background_bot_running'] and BINANCE_AVAILABLE and API_KEY and API_SECRET:
        start_background_bot()

    # Sidebar navigation
    selected_tab = st.sidebar.radio(
        "Select Dashboard Tab",
        ["Portfolio Overview", "Market Indicators", "Trading", "Performance", "Logs", "Settings", "Strategy", "Health"]
    )
    
    # Get portfolio data for all tabs
    status = load_bot_status()
    portfolio = status.get('portfolio', {})
    gbp_rate = get_gbp_exchange_rate()
    
    if portfolio:
        market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    else:
        market_condition, condition_score, avg_volatility = "UNCERTAIN", 0.5, 2.0
    
    # Render selected tab
    if selected_tab == "Portfolio Overview":
        render_portfolio_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility)
    elif selected_tab == "Market Indicators":
        render_market_indicators_tab()
    elif selected_tab == "Trading":
        render_manual_trading_tab()
    elif selected_tab == "Performance":
        render_performance_tab()
    elif selected_tab == "Logs":
        render_logs_tab()
    elif selected_tab == "Settings":
        render_settings_tab()
    elif selected_tab == "Strategy":
        render_strategy_tab()
    elif selected_tab == "Health":
        render_health_tab()

def main():
    """Main application entry point"""
    st.set_page_config(page_title="🤖 Crypto Trading Bot Dashboard", layout="wide")
    
    # Password authentication
    if not st.session_state['password_authenticated']:
        st.title("🔒 Enter Dashboard Password")
        input_password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if input_password == st.session_state['dashboard_password']:
                st.session_state['password_authenticated'] = True
                st.success("Access granted!")
                st.rerun()
            else:
                st.error("Incorrect password.")
                st.stop()
        
        if not st.session_state['password_authenticated']:
            st.stop()
    
    # Main dashboard
    st.title("🤖 Crypto Trading Bot Dashboard")
    st.caption("Professional trading with 24/7 background scanning")
    
    dashboard()

if __name__ == "__main__":
    main()