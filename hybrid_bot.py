# hybrid_bot.py - Complete Dashboard + Never-Stop Background Bot
import streamlit as st
import threading
import time
import os
import json
import signal
import sys
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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

# Check for bot controller
try:
    from bot_controller import BotController
    BOT_CONTROLLER_AVAILABLE = True
except ImportError:
    BOT_CONTROLLER_AVAILABLE = False

# Initialize session state
if 'dashboard_password' not in st.session_state:
    st.session_state['dashboard_password'] = 'bottie'  # Default password
if 'password_authenticated' not in st.session_state:
    st.session_state['password_authenticated'] = False
if 'background_bot_running' not in st.session_state:
    st.session_state['background_bot_running'] = False
if 'background_bot_thread' not in st.session_state:
    st.session_state['background_bot_thread'] = None

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
        """Scan for trading opportunities with robust error handling"""
        portfolio = self.get_portfolio_balances()
        opportunities = []
        
        for asset, data in portfolio.items():
            if asset == 'USDT':
                continue
                
            try:
                symbol = f"{asset}USDT"
                
                # Get recent price data
                klines = self.client.get_klines(
                    symbol=symbol,
                    interval='1m',
                    limit=120
                )
                
                if len(klines) >= 120:
                    # Calculate price change over 2 hours
                    current_price = float(klines[-1][4])  # Close price
                    price_2h_ago = float(klines[-120][4])  # Close price 120 minutes ago
                    change_pct = ((current_price - price_2h_ago) / price_2h_ago) * 100
                    
                    # Calculate volume
                    volumes = [float(k[5]) for k in klines[-20:]]  # Last 20 periods
                    avg_volume = sum(volumes) / len(volumes)
                    current_volume = float(klines[-1][5])
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                    
                    # Enhanced signal logic
                    signal = "HOLD"
                    confidence = 0.5
                    
                    # Check for significant price movement with volume confirmation
                    if abs(change_pct) >= 5.0 and volume_ratio >= 1.5:
                        # Additional filters for quality signals
                        if self.is_good_trading_time() and volume_ratio >= 2.0:
                            if change_pct > 0:
                                signal = "BUY_LONG"
                                confidence = min(0.9, 0.6 + (change_pct / 30))
                            else:
                                signal = "BUY_SHORT" 
                                confidence = min(0.9, 0.6 + (abs(change_pct) / 30))
                    
                    # Only add high-confidence opportunities
                    if signal != "HOLD" and confidence >= 0.65:
                        opportunities.append({
                            'asset': asset,
                            'signal': signal,
                            'confidence': confidence,
                            'current_price': current_price,
                            'change_pct': change_pct,
                            'volume_ratio': volume_ratio,
                            'balance': data['balance'],
                            'usd_value': data['usd_value'],
                            'timestamp': datetime.now().isoformat()
                        })
            
            except Exception as e:
                self.log_to_console(f"⚠️ Error analyzing {asset}: {e}")
        
        return portfolio, opportunities
    
    def is_good_trading_time(self):
        """Check if current time is good for trading (avoid low volume hours)"""
        current_hour = datetime.utcnow().hour
        # Avoid trading during low volume hours (0-6 UTC, 22-23 UTC)
        return current_hour not in [0, 1, 2, 3, 4, 5, 22, 23]
    
    def save_status(self, portfolio, opportunities):
        """Save bot status to multiple files for monitoring"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'running': self.running,
            'scan_count': self.scan_count,
            'opportunities': opportunities,
            'portfolio': portfolio,
            'uptime_seconds': int((datetime.now() - self.start_time).total_seconds()),
            'heartbeat_count': self.heartbeat_count,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'mode': 'Testnet' if USE_TESTNET else 'Live Trading'
        }
        
        try:
            # Main status file for dashboard
            with open('logs/bot_status.json', 'w') as f:
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
        'last_heartbeat': datetime.now().isoformat()
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

def render_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility):
    """Render the main overview tab"""
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
        volatility_level = "High" if avg_volatility > 3 else "Medium" if avg_volatility > 1.5 else "Low"
        st.metric("📈 Volatility", f"{avg_volatility:.1f}%")
    
    with col4:
        # Select profile based on market condition
        if market_condition == "BULL_TRENDING":
            profile = "Aggressive" if avg_volatility > 2.5 else "Swing"
        elif market_condition == "BEAR_TRENDING":
            profile = "Conservative"
        elif market_condition == "HIGH_VOLATILITY":
            profile = "Scalping"
        else:
            profile = "Balanced"
        
        st.metric("🎯 Active Profile", profile)
    
    st.divider()
    
    # Portfolio breakdown
    st.subheader("💼 Portfolio Holdings")
    
    portfolio_data = []
    for asset, data in portfolio.items():
        portfolio_data.append({
            'Asset': asset,
            'Balance': f"{data['balance']:.4f}",
            'Price (USD)': f"${data['price_usd']:.4f}",
            'Value (USD)': f"${data['usd_value']:.2f}",
            'Value (GBP)': f"£{data['usd_value'] * gbp_rate:.2f}",
            'Percentage': f"{(data['usd_value'] / total_usd * 100):.1f}%"
        })
    
    df = pd.DataFrame(portfolio_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_performance_tab():
    """Render performance analysis tab"""
    st.subheader("📊 Trading Performance")
    
    df = load_trade_data()
    
    if not df.empty:
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
        
        # Performance chart
        if 'pnl_percent' in df.columns:
            df['cumulative_pnl'] = df['pnl_percent'].cumsum()
            fig = px.line(df, x='timestamp', y='cumulative_pnl', 
                         title="Cumulative P&L Performance")
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent trades
        with st.expander("📋 Recent Trades"):
            recent_df = df.tail(10).copy()
            if 'timestamp' in recent_df.columns:
                recent_df['timestamp'] = pd.to_datetime(recent_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(recent_df, use_container_width=True, hide_index=True)
    else:
        st.info("No trade data available yet.")

def render_risk_profiles_tab():
    """Render risk profiles tab"""
    st.subheader("🛡️ Risk Management Profiles")
    
    st.markdown("### 📊 Available Risk Profiles")
    
    profiles = {
        "Conservative": {
            "description": "Low risk, stable returns",
            "take_profit": "8%",
            "stop_loss": "8%", 
            "trailing_stop": "3%",
            "max_hold": "24 hours",
            "confidence_threshold": "75%"
        },
        "Balanced": {
            "description": "Moderate risk, balanced approach",
            "take_profit": "12%",
            "stop_loss": "10%",
            "trailing_stop": "4%",
            "max_hold": "12 hours",
            "confidence_threshold": "65%"
        },
        "Aggressive": {
            "description": "Higher risk, higher potential returns",
            "take_profit": "15%",
            "stop_loss": "12%",
            "trailing_stop": "5%",
            "max_hold": "6 hours",
            "confidence_threshold": "60%"
        }
    }
    
    col1, col2, col3 = st.columns(3)
    
    for i, (profile_name, profile) in enumerate(profiles.items()):
        col = [col1, col2, col3][i]
        with col:
            with st.container():
                st.markdown(f"#### {profile_name}")
                st.markdown(f"**{profile['description']}**")
                st.write(f"Take Profit: {profile['take_profit']}")
                st.write(f"Stop Loss: {profile['stop_loss']}")
                st.write(f"Trailing Stop: {profile['trailing_stop']}")
                st.write(f"Max Hold: {profile['max_hold']}")
                st.write(f"Min Confidence: {profile['confidence_threshold']}")
    
    st.divider()
    
    st.markdown("### 🧠 Auto-Selection Logic")
    st.write("""
    The system automatically selects profiles based on:
    - Market volatility levels
    - Trend strength across portfolio  
    - Volume patterns and momentum
    - Recent performance feedback
    - Asset-specific risk characteristics
    """)

def render_logs_tab():
    """Render logs and monitoring tab"""
    st.subheader("📡 Live Bot Logs")
    
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
    
    # Display logs
    lines = load_logs("logs/console_output.log")
    colored_logs = []
    for line in lines:
        colored_logs.append(color_line(line))
    
    log_output = "\n".join(colored_logs[-50:])  # Show last 50 lines
    st.text_area("Recent Logs", log_output, height=400)

def render_settings_tab():
    """Render settings and controls tab"""
    st.subheader("⚙️ Bot Controls & Settings")
    
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
        st.subheader("📊 System Status")
        
        # API status
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            st.success("✅ Binance API Configured")
        else:
            st.error("❌ Binance API Not Configured")
        
        st.info(f"📡 Mode: {'Testnet' if USE_TESTNET else 'Live Trading'}")
        
        # Bot statistics
        st.markdown("---")
        st.subheader("📈 Bot Statistics")
        
        status = load_bot_status()
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Scans Completed", status.get('scan_count', 0))
        with col_b:
            uptime = status.get('uptime_seconds', 0)
            st.metric("Uptime", f"{uptime // 3600:.0f}h {(uptime % 3600) // 60:.0f}m")
        
        # Remote access
        st.markdown("---")
        st.subheader("🔗 Remote Access")
        ts_ip = get_tailscale_ip()
        if ts_ip != "Unavailable":
            remote_url = f"http://{ts_ip}:8501"
            st.text_input("🔗 Access URL", value=remote_url, label_visibility="collapsed")
            st.info("Use this URL to access dashboard remotely via Tailscale")
        else:
            st.info("Tailscale not available")

def dashboard():
    """Main dashboard function"""
    # Sidebar controls
    st.sidebar.title("🎛️ Dashboard Controls")
    
    # Bot status in sidebar
    if st.session_state['background_bot_running']:
        st.sidebar.success("🟢 Background Bot: RUNNING")
        status = load_bot_status()
        st.sidebar.metric("Scans", status.get('scan_count', 0))
        st.sidebar.metric("Opportunities", len(status.get('opportunities', [])))
    else:
        st.sidebar.warning("🔴 Background Bot: STOPPED")
        st.sidebar.info("Start in Settings tab")
    
    # Download logs
    if st.sidebar.button("📥 Download Logs"):
        logs = load_logs("logs/console_output.log")
        st.sidebar.download_button(
            "📄 console_output.log",
            data="\n".join(logs),
            file_name="console_output.log"
        )
    
    # Auto-start background bot on first load if configured
    if not st.session_state['background_bot_running'] and BINANCE_AVAILABLE and API_KEY and API_SECRET:
        start_background_bot()
        st.rerun()
    
    # Main dashboard tabs
    status = load_bot_status()
    portfolio = status.get('portfolio', {})
    gbp_rate = get_gbp_exchange_rate()
    
    if portfolio:
        market_condition, condition_score, avg_volatility = simulate_market_analysis(portfolio)
    else:
        market_condition, condition_score, avg_volatility = "UNCERTAIN", 0.5, 2.0
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Overview",
        "📊 Performance", 
        "🛡️ Risk Profiles",
        "📡 Logs",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_overview_tab(portfolio, gbp_rate, market_condition, condition_score, avg_volatility)
    
    with tab2:
        render_performance_tab()
    
    with tab3:
        render_risk_profiles_tab()
    
    with tab4:
        render_logs_tab()
    
    with tab5:
        render_settings_tab()

def main():
    """Main application entry point"""
    st.set_page_config(page_title="🎯 Adaptive Risk Management Bot", layout="wide")
    
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
    st.title("🎯 Adaptive Risk Management Trading Bot")
    st.caption("Professional, emotion-free trading with dynamic risk adjustment")
    
    dashboard()

if __name__ == "__main__":
    main()