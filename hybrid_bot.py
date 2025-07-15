import streamlit as st
import threading
import time
import os
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
SCAN_INTERVAL = 30  # 30 seconds

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
        """Get portfolio balances with robust error handling"""
        if not self.client:
            return {}
        
        try:
            account = self.client.get_account()
            balances = {}
            
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    try:
                        ticker = f"{asset}USDT"
                        if asset == 'USDT':
                            price = 1.0
                        else:
                            price_data = self.client.get_symbol_ticker(symbol=ticker)
                            price = float(price_data['price'])
                        
                        usd_value = total * price
                        
                        if usd_value >= MIN_BALANCE_USD:
                            balances[asset] = {
                                'balance': total,
                                'price_usd': price,
                                'usd_value': usd_value,
                                'free': free,
                                'locked': locked
                            }
                    except Exception:
                        pass  # Skip assets with pricing errors
            
            return balances
        except Exception as e:
            self.log_to_console(f"❌ Error getting portfolio: {e}")
            return {}
    
    def scan_for_opportunities(self):
        """Scan for trading opportunities with robust error handling and user-selected strategy"""
        portfolio = self.get_portfolio_balances()
        
        # Get current strategy settings
        status = load_bot_status()
        selected_strategy = status.get('latest_strategy', 'Breakout')
        risk_level = status.get('latest_risk_level', 'Balanced')
        
        self.log_to_console(f"[SCAN] Strategy: {selected_strategy} | Risk: {risk_level} | Portfolio assets: {len(portfolio)}")
        
        opportunities = []
        
        # FIXED: Single set of thresholds - more lenient for actual trading
        base_thresholds = {
            'Breakout': {'change': 2.0, 'volume': 1.2, 'confidence': 0.5},
            'Scalping': {'change': 1.0, 'volume': 1.0, 'confidence': 0.45},
            'Swing': {'change': 3.0, 'volume': 1.1, 'confidence': 0.55},
        }
        
        # Risk level modifiers
        risk_modifiers = {
            'Conservative': 0.8,
            'Balanced': 1.0,
            'Aggressive': 1.2,
        }
        
        thresholds = base_thresholds.get(selected_strategy, base_thresholds['Breakout']).copy()
        modifier = risk_modifiers.get(risk_level, 1.0)
        
        # Apply risk modifier
        thresholds['change'] *= modifier
        thresholds['volume'] *= modifier
        thresholds['confidence'] *= modifier
        
        for asset, data in portfolio.items():
            if asset == 'USDT':
                continue
                
            try:
                symbol = f"{asset}USDT"
                
                # Get recent price data
                klines = self.client.get_klines(symbol=symbol, interval='1m', limit=60)
                
                if len(klines) >= 60:
                    # Calculate price change over 1 hour (more reasonable)
                    current_price = float(klines[-1][4])
                    price_1h_ago = float(klines[-60][4])
                    change_pct = ((current_price - price_1h_ago) / price_1h_ago) * 100
                    
                    # Calculate volume ratio
                    volumes = [float(k[5]) for k in klines[-10:]]
                    avg_volume = sum(volumes) / len(volumes)
                    current_volume = float(klines[-1][5])
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                    
                    # Simple confidence calculation
                    confidence = min(0.9, 0.5 + (abs(change_pct) / 10))
                    
                    self.log_to_console(f"[SCAN] {asset}: change={change_pct:.2f}%, volume={volume_ratio:.2f}x, conf={confidence:.2f}")
                    
                    # Check if meets criteria
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
                            'risk_level_used': risk_level
                        }
                        
                        opportunities.append(opportunity)
                        self.log_to_console(f"[OPPORTUNITY] {asset} {signal} - Change: {change_pct:.2f}% | Confidence: {confidence:.2f}")
                        
            except Exception as e:
                self.log_to_console(f"⚠️ Error analyzing {asset}: {e}")
        
        self.log_to_console(f"[SCAN] Complete: {len(opportunities)} opportunities found")
        return portfolio, opportunities
    
    def save_status(self, portfolio, opportunities):
        """Save bot status to multiple files for monitoring, preserving latest strategy and risk level"""
        # Read previous bot_status.json to preserve latest_strategy and latest_risk_level
        status_path = 'logs/bot_status.json'
        prev_strategy = None
        prev_risk = None
        try:
            if os.path.exists(status_path):
                with open(status_path, 'r') as f:
                    prev_status = json.load(f)
                prev_strategy = prev_status.get('latest_strategy')
                prev_risk = prev_status.get('latest_risk_level')
        except Exception:
            pass

        status = {
            'timestamp': datetime.now().isoformat(),
            'running': self.running,
            'scan_count': self.scan_count,
            'opportunities': opportunities,
            'portfolio': portfolio,
            'uptime_seconds': int((datetime.now() - self.start_time).total_seconds()),
            'heartbeat_count': self.heartbeat_count,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'mode': 'Testnet' if USE_TESTNET else 'Live Trading',
            'latest_strategy': prev_strategy if prev_strategy else 'Breakout',
            'latest_risk_level': prev_risk if prev_risk else 'Balanced'
        }

        try:
            self.log_to_console(f"[SAVE_STATUS] Saving portfolio with {len(portfolio)} assets")
            
            # Main status file for dashboard
            with open(status_path, 'w') as f:
                json.dump(status, f, indent=2)
            
            # Append to scan history
            with open('logs/robust_bot_scans.log', 'a') as f:
                f.write(f"{json.dumps(status)}\n")
                
        except Exception as e:
            self.log_to_console(f"❌ Error saving status: {e}")
    
    def run_continuous(self):
        """Main bot loop with robust error handling"""
        self.running = True
        self.start_time = datetime.now()
        
        self.log_to_console("🚀 Robust Trading Bot Started")
        self.log_to_console(f"📊 Scan Interval: {SCAN_INTERVAL} seconds")
        self.log_to_console(f"🔗 Mode: {'Testnet' if USE_TESTNET else 'Live Trading'}")
        self.log_to_console(f"💓 Keep-alive: Enabled")
        self.log_to_console("=" * 60)
        
        # Start heartbeat system
        self.start_keep_alive()
        
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.running:
            try:
                self.scan_count += 1
                self.log_to_console(f"🔍 Starting scan #{self.scan_count}")
                
                # Perform scan
                portfolio, opportunities = self.scan_for_opportunities()
                
                # Save status
                self.save_status(portfolio, opportunities)
                
                # Log results
                opp_count = len(opportunities)
                portfolio_count = len(portfolio)
                self.log_to_console(f"✅ Scan #{self.scan_count} complete - {portfolio_count} assets, {opp_count} opportunities")
                
                # Reset error counter on successful scan
                consecutive_errors = 0
                
                # Wait for next scan
                time.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                consecutive_errors += 1
                self.log_to_console(f"❌ Scan #{self.scan_count} error: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    self.log_to_console(f"🛑 Too many consecutive errors ({consecutive_errors}). Stopping bot.")
                    break
                
                # Progressive backoff on errors
                error_delay = min(300, 30 * consecutive_errors)  # Max 5 minutes
                self.log_to_console(f"⏰ Waiting {error_delay} seconds before retry...")
                time.sleep(error_delay)
        
        self.log_to_console("🛑 Background bot stopped")
    
    def stop(self):
        """Stop the background bot"""
        self.running = False
        self.log_to_console("🛑 Stop signal received")

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
    
    # Define market explanations FIRST
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
    """Render market indicators tab"""
    st.header("📊 Market Indicators & Signals")
    st.caption("Live summary of all tracked coins, signals, and movements.")
    
    status = load_bot_status()
    opportunities = status.get('opportunities', [])
    
    if st.session_state['background_bot_running']:
        st.success("🤖 Background bot is continuously scanning your portfolio...")
    else:
        st.warning("🤖 Background bot is stopped. Start it in Settings to begin scanning.")
    
    if opportunities:
        st.success(f"Found {len(opportunities)} trading opportunities!")
        
        for opp in opportunities:
            with st.expander(f"🎯 {opp['asset']} - {opp['signal']} (Confidence: {opp['confidence']:.1%})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", f"${opp['current_price']:.4f}")
                    st.metric("1h Change", f"{opp['change_pct']:+.2f}%")
                
                with col2:
                    st.metric("Your Balance", f"{opp['balance']:.6f} {opp['asset']}")
                    st.metric("USD Value", f"${opp['usd_value']:.2f}")
                
                with col3:
                    st.metric("Volume Ratio", f"{opp['volume_ratio']:.2f}x")
                    st.metric("Signal Strength", opp['signal'])
                    
                # Show which strategy/risk was used
                st.info(f"Strategy: {opp.get('strategy_used', 'Unknown')} | Risk: {opp.get('risk_level_used', 'Unknown')}")
    else:
        st.info("🔍 No trading opportunities found at this time.")

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

def render_performance_tab():
    """Render performance tab"""
    st.header("📊 Performance")
    st.caption("Trading performance metrics and live wallet")
    
    # Load trade data from both manual and bot logs
    df_bot = load_trade_data()
    manual_log_path = "logs/manual_trades.log"
    manual_trades = []
    if os.path.exists(manual_log_path):
        with open(manual_log_path, "r") as f:
            for line in f:
                try:
                    manual_trades.append(json.loads(line))
                except:
                    pass
    df_manual = pd.DataFrame(manual_trades)
    
    # Combine both
    if not df_bot.empty and not df_manual.empty:
        df_bot['source'] = 'Bot'
        df_manual['source'] = 'Manual'
        df = pd.concat([df_bot, df_manual], ignore_index=True, sort=False)
    elif not df_bot.empty:
        df_bot['source'] = 'Bot'
        df = df_bot.copy()
    elif not df_manual.empty:
        df_manual['source'] = 'Manual'
        df = df_manual.copy()
    else:
        df = pd.DataFrame()

    if not df.empty:
        # Fill missing columns for display
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        if 'pnl_percent' not in df.columns:
            df['pnl_percent'] = 0.0

        # Performance metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", len(df))
        with col2:
            win_rate = (df['pnl_percent'] > 0).mean() * 100 if 'pnl_percent' in df.columns else 0
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            total_pnl = df['pnl_percent'].sum() if 'pnl_percent' in df.columns else 0
            st.metric("Total P&L", f"{total_pnl:+.2f}%")
        with col4:
            avg_pnl = df['pnl_percent'].mean() if 'pnl_percent' in df.columns else 0
            st.metric("Avg P&L", f"{avg_pnl:+.2f}%")

        # Recent trades
        with st.expander("📋 Recent Trades"):
            recent_df = df.sort_values('timestamp').tail(10).copy()
            if 'timestamp' in recent_df.columns:
                recent_df['timestamp'] = pd.to_datetime(recent_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(recent_df, use_container_width=True, hide_index=True)

    else:
        st.info("No trade data available yet.")
    
    # Live Wallet
    st.subheader("💰 Live Wallet (Binance)")
    try:
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            client = Client(API_KEY, API_SECRET)
            if USE_TESTNET:
                client.API_URL = "https://testnet.binance.vision/api"
            
            account_info = client.get_account()
            balances = account_info['balances']
            
            # Filter balances with value > 0
            wallet_data = []
            for balance in balances:
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    wallet_data.append({
                        'Asset': balance['asset'],
                        'Free': f"{free:.8f}".rstrip('0').rstrip('.'),
                        'Locked': f"{locked:.8f}".rstrip('0').rstrip('.')
                    })
            
            if wallet_data:
                df_wallet = pd.DataFrame(wallet_data)
                st.dataframe(df_wallet, use_container_width=True, hide_index=True)
            else:
                st.info("No balances found.")
            
        else:
            st.warning("Binance API keys not configured.")
    except Exception as e:
        st.error(f"Error fetching wallet: {e}")

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

def render_settings_tab():
    """Render settings tab"""
    st.header("⚙️ Settings")
    st.caption("Bot controls and configuration")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🤖 Background Bot Control")
        
        if st.session_state['background_bot_running']:
            st.success("✅ Background bot is RUNNING 24/7")
            st.info("Bot scans every 30 seconds automatically")
            
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
        
        # Display current active settings
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

def render_strategy_tab():
    """Render strategy tab"""
    st.header("🧠 Strategy")
    st.caption("Strategy selection & configuration")
    
    # Get current strategy settings
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
        st.write("- Threshold: 2% price movement")
        st.write("- Volume: 1.2x average required")
        st.write("- Good for trending markets")
        
        st.write("**Scalping Strategy:**")
        st.write("- Threshold: 1% quick moves")
        st.write("- Volume: 1.0x average required")
        st.write("- High frequency trading")

    with col2:
        st.write("**Swing Strategy:**")
        st.write("- Threshold: 3% price movement")
        st.write("- Volume: 1.1x average required")
        st.write("- Longer hold periods")
        
        st.write("**Risk Levels:**")
        st.write("- Conservative: 0.8x thresholds")
        st.write("- Balanced: 1.0x thresholds")
        st.write("- Aggressive: 1.2x thresholds")

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
        
        # API connection status
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
        
        # Heartbeat info
        if 'last_heartbeat' in status:
            heartbeat_time = datetime.fromisoformat(status['last_heartbeat'])
            time_since_heartbeat = (datetime.now() - heartbeat_time).total_seconds()
            if time_since_heartbeat < 120:
                st.success(f"💓 Heartbeat: Active ({int(time_since_heartbeat)}s ago)")
            else:
                st.warning(f"⚠️ Heartbeat: {int(time_since_heartbeat)}s ago")
        else:
            st.info("💓 Heartbeat: No data")
        
        # Scan stats
        st.metric("Total Scans", status.get('scan_count', 0))
        uptime = status.get('uptime_seconds', 0)
        st.metric("Bot Uptime", f"{uptime // 3600:.0f}h {(uptime % 3600) // 60:.0f}m")
    
    # Log file check
    st.subheader("📁 Log File Status")
    if os.path.exists("logs/console_output.log"):
        st.success("✅ Log file accessible")
        
        with open("logs/console_output.log", "r", encoding="utf-8") as f:
            last_lines = f.readlines()[-10:]
        
        # Show last few log lines
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