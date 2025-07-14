# hybrid_bot.py - Dashboard + Never-Stop Background Bot
import streamlit as st
import threading
import time
import os
import json
import signal
import sys
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
    st.session_state['dashboard_password'] = 'bottie'
if 'password_authenticated' not in st.session_state:
    st.session_state['password_authenticated'] = False
if 'background_bot_running' not in st.session_state:
    st.session_state['background_bot_running'] = False
if 'background_bot_thread' not in st.session_state:
    st.session_state['background_bot_thread'] = None

class BackgroundTradingBot:
    def __init__(self):
        self.running = False
        self.scan_count = 0
        self.client = None
        self.start_time = datetime.now()
        self.create_log_directories()
        self.initialize_client()
    
    def create_log_directories(self):
        """Create log directories"""
        os.makedirs('logs', exist_ok=True)
    
    def initialize_client(self):
        """Initialize Binance client"""
        if not BINANCE_AVAILABLE or not API_KEY or not API_SECRET:
            return False
        
        try:
            self.client = Client(API_KEY, API_SECRET)
            if USE_TESTNET:
                self.client.API_URL = "https://testnet.binance.vision/api"
            return True
        except Exception as e:
            print(f"❌ Error connecting to Binance: {e}")
            return False
    
    def get_portfolio(self):
        """Get portfolio from Binance API"""
        if not self.client:
            return {}
        
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
            return {}
    
    def analyze_opportunity(self, symbol):
        """Analyze trading opportunity for symbol"""
        if not self.client:
            return None
        
        try:
            klines = self.client.get_klines(symbol=symbol, interval='1m', limit=120)
            
            if len(klines) < 120:
                return None
            
            open_price = float(klines[0][1])
            close_price = float(klines[-1][4])
            change_pct = ((close_price - open_price) / open_price) * 100
            
            volumes = [float(kline[5]) for kline in klines[-20:]]
            avg_volume = sum(volumes) / len(volumes)
            current_volume = float(klines[-1][5])
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
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
            return None
    
    def scan_portfolio(self):
        """Scan portfolio for opportunities"""
        portfolio = self.get_portfolio()
        opportunities = []
        
        if not portfolio:
            return opportunities, portfolio
        
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
        
        return opportunities, portfolio
    
    def save_status(self, opportunities, portfolio):
        """Save current status to file for dashboard"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'running': self.running,
            'scan_count': self.scan_count,
            'opportunities': opportunities,
            'portfolio': portfolio,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
        }
        
        try:
            with open('logs/bot_status.json', 'w') as f:
                json.dump(status, f)
        except:
            pass
    
    def log_scan_result(self, opportunities, portfolio):
        """Log scan results"""
        scan_result = {
            'timestamp': datetime.now().isoformat(),
            'scan_count': self.scan_count,
            'opportunities_found': len(opportunities),
            'opportunities': opportunities,
            'portfolio_assets': len(portfolio)
        }
        
        try:
            with open('logs/hybrid_bot_scans.log', 'a') as f:
                f.write(f"{json.dumps(scan_result)}\n")
        except:
            pass
    
    def run_continuous(self):
        """Run continuous scanning loop"""
        self.running = True
        print(f"🚀 Background bot started at {datetime.now()}")
        
        while self.running:
            try:
                self.scan_count += 1
                
                # Perform scan
                opportunities, portfolio = self.scan_portfolio()
                
                # Save status for dashboard
                self.save_status(opportunities, portfolio)
                
                # Log results
                self.log_scan_result(opportunities, portfolio)
                
                print(f"🔄 Scan #{self.scan_count} - Found {len(opportunities)} opportunities")
                
                # Wait for next scan
                time.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                print(f"❌ Scan error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def stop(self):
        """Stop the background bot"""
        self.running = False

# Global bot instance
if 'background_bot' not in st.session_state:
    st.session_state['background_bot'] = BackgroundTradingBot()

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
        'uptime_seconds': 0
    }

def get_gbp_exchange_rate():
    """Get USD to GBP exchange rate"""
    try:
        import requests
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return response.json()['rates']['GBP']
    except:
        return 0.79

def render_portfolio_overview():
    """Render portfolio overview"""
    st.subheader("💼 Portfolio Overview")
    
    status = load_bot_status()
    portfolio = status.get('portfolio', {})
    
    if not portfolio:
        st.warning("No portfolio data available. Start the background bot to begin scanning.")
        return
    
    # Calculate totals
    gbp_rate = get_gbp_exchange_rate()
    total_usd = sum(coin['usd_value'] for coin in portfolio.values())
    total_gbp = total_usd * gbp_rate
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Total Value (USD)", f"${total_usd:,.2f}")
    
    with col2:
        st.metric("💷 Total Value (GBP)", f"£{total_gbp:,.2f}")
    
    with col3:
        st.metric("🪙 Total Assets", len(portfolio))
    
    with col4:
        mode = "🧪 Testnet" if USE_TESTNET else "🚀 Live Trading"
        st.metric("🔗 Trading Mode", mode)
    
    st.divider()
    
    # Bot status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.session_state['background_bot_running']:
            st.metric("🤖 Background Bot", "🟢 Running", "24/7 Active")
        else:
            st.metric("🤖 Background Bot", "🔴 Stopped", "Start in Settings")
    
    with col2:
        st.metric("🔍 Total Scans", status.get('scan_count', 0))
    
    with col3:
        if status.get('timestamp'):
            scan_time = datetime.fromisoformat(status['timestamp'])
            time_diff = (datetime.now() - scan_time).seconds
            st.metric("⏰ Last Scan", f"{time_diff}s ago")
        else:
            st.metric("⏰ Last Scan", "Never")
    
    with col4:
        opportunities = len(status.get('opportunities', []))
        st.metric("🎯 Opportunities", opportunities)
    
    st.divider()
    
    # Portfolio table
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

def render_market_indicators():
    """Render market indicators"""
    st.subheader("📊 Market Indicators & Signals")
    
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
                    st.metric("2h Change", f"{opp['change_pct']:+.2f}%")
                
                with col2:
                    st.metric("Your Balance", f"{opp['balance']:.6f} {opp['asset']}")
                    st.metric("USD Value", f"${opp['usd_value']:.2f}")
                
                with col3:
                    st.metric("Volume Ratio", f"{opp['volume_ratio']:.2f}x")
                    st.metric("Signal Strength", opp['signal'])
    else:
        st.info("🔍 No trading opportunities found at this time.")

def render_settings():
    """Render settings tab"""
    st.subheader("⚙️ Bot Control & Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 Background Bot Control")
        
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
        
        # Bot status
        status = load_bot_status()
        
        if BINANCE_AVAILABLE and API_KEY and API_SECRET:
            st.success("✅ Binance API Configured")
        else:
            st.error("❌ Binance API Not Configured")
        
        st.info(f"📡 Mode: {'Testnet' if USE_TESTNET else 'Live Trading'}")
        
        # Bot statistics
        st.markdown("---")
        st.subheader("📈 Bot Statistics")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Scans Completed", status.get('scan_count', 0))
        with col_b:
            uptime = status.get('uptime_seconds', 0)
            st.metric("Uptime", f"{uptime // 3600:.0f}h {(uptime % 3600) // 60:.0f}m")

def main():
    """Main dashboard function"""
    st.set_page_config(page_title="🎯 Multi-Coin Portfolio Bot", layout="wide")
    
    st.title("🎯 Multi-Coin Portfolio Trading Bot")
    st.caption("24/7 background scanning with real-time dashboard")
    
    # Password protection
    if not st.session_state['password_authenticated']:
        st.subheader("🔒 Enter Dashboard Password")
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
    
    # Auto-start background bot on first load
    if not st.session_state['background_bot_running'] and BINANCE_AVAILABLE and API_KEY and API_SECRET:
        start_background_bot()
    
    # Sidebar
    st.sidebar.title("🎛️ Dashboard Controls")
    
    if st.session_state['background_bot_running']:
        st.sidebar.success("🟢 Background Bot: RUNNING")
        status = load_bot_status()
        st.sidebar.metric("Scans", status.get('scan_count', 0))
        st.sidebar.metric("Opportunities", len(status.get('opportunities', [])))
    else:
        st.sidebar.warning("🔴 Background Bot: STOPPED")
        st.sidebar.info("Start in Settings tab")
    
    # Navigation
    selected_tab = st.sidebar.radio(
        "Select Tab",
        ["Portfolio Overview", "Market Indicators", "Settings"]
    )
    
    # Render selected tab
    if selected_tab == "Portfolio Overview":
        render_portfolio_overview()
    elif selected_tab == "Market Indicators":
        render_market_indicators()
    elif selected_tab == "Settings":
        render_settings()
    
    # Auto-refresh every 30 seconds
    time.sleep(30)
    st.rerun()

if __name__ == "__main__":
    main()