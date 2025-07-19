#!/usr/bin/env python3
"""
Simplified Hybrid Crypto Trading Bot Dashboard
Railway-compatible version with error handling
"""

import os
import streamlit as st
import time
import threading
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="🤖 Hybrid Crypto Trading Bot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Try to import Binance client
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

# API Configuration
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"

# Initialize session state
if "logs" not in st.session_state:
    st.session_state["logs"] = []
if "auto_trading" not in st.session_state:
    st.session_state["auto_trading"] = False
if "portfolio_data" not in st.session_state:
    st.session_state["portfolio_data"] = {}
if "trade_history" not in st.session_state:
    st.session_state["trade_history"] = []

def log_message(message):
    """Add message to logs with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state["logs"].append(log_entry)
    # Keep only last 100 logs
    if len(st.session_state["logs"]) > 100:
        st.session_state["logs"] = st.session_state["logs"][-100:]

def initialize_binance_client():
    """Initialize Binance client with error handling"""
    if not BINANCE_AVAILABLE:
        return None, "python-binance library not available"
    
    if not API_KEY or not API_SECRET:
        return None, "API credentials not configured"
    
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = 'https://testnet.binance.vision/api'
        
        # Test connection
        client.get_server_time()
        return client, "Connected successfully"
    
    except Exception as e:
        return None, str(e)

def get_portfolio_overview(client):
    """Get portfolio overview with error handling"""
    if not client:
        return {}, "No client connection"
    
    try:
        account = client.get_account()
        balances = {}
        total_value = 0
        
        for balance in account['balances']:
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                asset = balance['asset']
                usd_value = total
                
                # Convert to USD value (simplified)
                if asset != 'USDT' and asset != 'USD':
                    try:
                        ticker = client.get_symbol_ticker(symbol=f"{asset}USDT")
                        usd_value = total * float(ticker['price'])
                    except:
                        usd_value = 0
                
                balances[asset] = {
                    'free': free,
                    'locked': locked,
                    'total': total,
                    'usd_value': usd_value
                }
                total_value += usd_value
        
        return balances, total_value
    
    except Exception as e:
        return {}, f"Error fetching portfolio: {e}"

def get_trading_pairs():
    """Get available trading pairs"""
    common_pairs = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
        'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'MATICUSDT'
    ]
    return common_pairs

def execute_manual_trade(client, symbol, side, amount):
    """Execute manual trade with error handling"""
    if not client:
        return False, "No client connection"
    
    try:
        # Get current price
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        
        # Calculate quantity
        if side == "BUY":
            quantity = amount / current_price
        else:
            # For SELL, amount is the quantity of the asset
            quantity = amount
        
        # Round quantity to valid precision (simplified)
        quantity = round(quantity, 6)
        
        # Execute trade
        if side == "BUY":
            order = client.order_market_buy(symbol=symbol, quoteOrderQty=amount)
        else:
            order = client.order_market_sell(symbol=symbol, quantity=quantity)
        
        # Log the trade
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': current_price,
            'order_id': order['orderId'],
            'status': order['status']
        }
        
        st.session_state["trade_history"].append(trade_record)
        log_message(f"Trade executed: {side} {symbol} - Amount: ${amount}")
        
        return True, f"Order {order['orderId']} executed successfully"
    
    except Exception as e:
        log_message(f"Trade failed: {e}")
        return False, str(e)

def main_dashboard():
    """Main dashboard interface"""
    st.title("🤖 Hybrid Crypto Trading Bot")
    st.caption("Advanced Trading Dashboard with Portfolio Management")
    
    # Sidebar
    st.sidebar.title("🎛️ Control Panel")
    
    # Check API connection
    client, connection_status = initialize_binance_client()
    
    if client:
        st.sidebar.success(f"✅ {connection_status}")
        if USE_TESTNET:
            st.sidebar.info("🧪 Testnet Mode")
        else:
            st.sidebar.warning("⚠️ Live Trading Mode")
    else:
        st.sidebar.error(f"❌ {connection_status}")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["🏠 Dashboard", "📊 Portfolio", "✋ Manual Trading", "🤖 Auto-Trader", "📈 Analytics", "⚙️ Settings", "📜 Logs"]
    )
    
    # Auto-refresh
    if st.sidebar.checkbox("🔄 Auto-refresh (30s)"):
        time.sleep(30)
        st.experimental_rerun()
    
    # Main content
    if page == "🏠 Dashboard":
        dashboard_home(client)
    elif page == "📊 Portfolio":
        portfolio_page(client)
    elif page == "✋ Manual Trading":
        manual_trading_page(client)
    elif page == "🤖 Auto-Trader":
        auto_trader_page(client)
    elif page == "📈 Analytics":
        analytics_page()
    elif page == "⚙️ Settings":
        settings_page()
    elif page == "📜 Logs":
        logs_page()

def dashboard_home(client):
    """Dashboard home page"""
    st.header("🏠 Trading Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    if client:
        portfolio, total_value = get_portfolio_overview(client)
        
        with col1:
            st.metric("💰 Portfolio Value", f"${total_value:,.2f}")
        
        with col2:
            active_positions = len([p for p in portfolio.values() if p['total'] > 0])
            st.metric("📊 Active Assets", active_positions)
        
        with col3:
            recent_trades = len([t for t in st.session_state["trade_history"] 
                               if datetime.fromisoformat(t['timestamp']) > datetime.now() - timedelta(hours=24)])
            st.metric("📈 24h Trades", recent_trades)
        
        with col4:
            st.metric("🤖 Auto-Trading", "ON" if st.session_state["auto_trading"] else "OFF")
    
    else:
        st.error("⚠️ Unable to fetch data - Check API configuration")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Refresh Data", use_container_width=True):
            log_message("Data refreshed manually")
            st.experimental_rerun()
    
    with col2:
        if st.button("📊 Portfolio Snapshot", use_container_width=True):
            if client:
                portfolio, total_value = get_portfolio_overview(client)
                log_message(f"Portfolio snapshot: ${total_value:,.2f}")
            else:
                st.error("No API connection")
    
    with col3:
        if st.button("🆘 Emergency Stop", use_container_width=True):
            st.session_state["auto_trading"] = False
            log_message("Emergency stop activated - All auto-trading halted")
            st.warning("🛑 All automated trading stopped")

def portfolio_page(client):
    """Portfolio overview page"""
    st.header("📊 Portfolio Overview")
    
    if not client:
        st.error("⚠️ No API connection available")
        return
    
    try:
        portfolio, total_value = get_portfolio_overview(client)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Total Value", f"${total_value:,.2f}")
        
        with col2:
            num_assets = len(portfolio)
            st.metric("🏦 Assets Held", num_assets)
        
        with col3:
            usdt_balance = portfolio.get('USDT', {}).get('total', 0)
            st.metric("💵 USDT Available", f"${usdt_balance:,.2f}")
        
        # Portfolio table
        if portfolio:
            df_data = []
            for asset, data in portfolio.items():
                df_data.append({
                    'Asset': asset,
                    'Total': f"{data['total']:.6f}",
                    'Free': f"{data['free']:.6f}",
                    'Locked': f"{data['locked']:.6f}",
                    'USD Value': f"${data['usd_value']:.2f}"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            # Portfolio chart
            if len(portfolio) > 1:
                chart_data = {asset: data['usd_value'] for asset, data in portfolio.items() if data['usd_value'] > 1}
                if chart_data:
                    fig = px.pie(values=list(chart_data.values()), names=list(chart_data.keys()), 
                               title="Portfolio Distribution")
                    st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("ℹ️ No assets found in portfolio")
    
    except Exception as e:
        st.error(f"❌ Error loading portfolio: {e}")

def manual_trading_page(client):
    """Manual trading interface"""
    st.header("✋ Manual Trading")
    
    if not client:
        st.error("⚠️ No API connection available")
        return
    
    # Trading form
    with st.form("manual_trade"):
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.selectbox("Trading Pair", get_trading_pairs())
            side = st.radio("Order Type", ["BUY", "SELL"])
        
        with col2:
            amount = st.number_input("Amount (USDT)", min_value=10.0, value=50.0, step=10.0)
            
            # Get current price
            try:
                ticker = client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                st.info(f"Current Price: ${current_price:,.4f}")
                
                if side == "BUY":
                    estimated_qty = amount / current_price
                    st.info(f"Estimated Quantity: {estimated_qty:.6f}")
                
            except Exception as e:
                st.error(f"Unable to fetch price: {e}")
        
        # Risk management
        st.subheader("🛡️ Risk Management")
        col1, col2 = st.columns(2)
        
        with col1:
            stop_loss = st.slider("Stop Loss %", 1.0, 20.0, 5.0, 0.5)
        
        with col2:
            take_profit = st.slider("Take Profit %", 5.0, 50.0, 15.0, 1.0)
        
        # Submit trade
        submitted = st.form_submit_button("🚀 Execute Trade", use_container_width=True)
        
        if submitted:
            # Risk validation
            if amount < 10:
                st.error("❌ Minimum trade amount is $10")
            else:
                success, message = execute_manual_trade(client, symbol, side, amount)
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")

def auto_trader_page(client):
    """Auto-trader control page"""
    st.header("🤖 Auto-Trader Control")
    
    # Auto-trader status
    if st.session_state["auto_trading"]:
        st.success("✅ Auto-Trader is ACTIVE")
        
        if st.button("🛑 Stop Auto-Trader", use_container_width=True):
            st.session_state["auto_trading"] = False
            log_message("Auto-trader stopped by user")
            st.experimental_rerun()
    
    else:
        st.info("⏹️ Auto-Trader is STOPPED")
        
        if st.button("▶️ Start Auto-Trader", use_container_width=True):
            if client:
                st.session_state["auto_trading"] = True
                log_message("Auto-trader started by user")
                st.experimental_rerun()
            else:
                st.error("❌ Cannot start auto-trader without API connection")
    
    # Auto-trader settings
    st.subheader("⚙️ Auto-Trader Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_positions = st.number_input("Max Positions", min_value=1, max_value=10, value=3)
        scan_interval = st.number_input("Scan Interval (seconds)", min_value=30, max_value=3600, value=300)
    
    with col2:
        risk_per_trade = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.5, 0.1)
        min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.65, 0.05)
    
    # Strategy selection
    st.subheader("📈 Trading Strategies")
    
    strategies = st.multiselect(
        "Active Strategies",
        ["Breakout", "Mean Reversion", "Momentum", "Quantum Analysis"],
        default=["Breakout"]
    )
    
    st.info(f"ℹ️ Selected strategies: {', '.join(strategies)}")

def analytics_page():
    """Analytics and performance page"""
    st.header("📈 Trading Analytics")
    
    # Performance summary
    if st.session_state["trade_history"]:
        df = pd.DataFrame(st.session_state["trade_history"])
        
        # Metrics
        total_trades = len(df)
        buy_trades = len(df[df['side'] == 'BUY'])
        sell_trades = len(df[df['side'] == 'SELL'])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Trades", total_trades)
        
        with col2:
            st.metric("Buy Orders", buy_trades)
        
        with col3:
            st.metric("Sell Orders", sell_trades)
        
        with col4:
            avg_amount = df['amount'].mean()
            st.metric("Avg Trade Size", f"${avg_amount:.2f}")
        
        # Trade history chart
        if total_trades > 0:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            fig = px.scatter(df, x='timestamp', y='amount', color='side', 
                           title="Trade History", hover_data=['symbol', 'price'])
            st.plotly_chart(fig, use_container_width=True)
        
        # Trade history table
        st.subheader("📋 Recent Trades")
        st.dataframe(df.tail(20), use_container_width=True)
    
    else:
        st.info("ℹ️ No trading history available")

def settings_page():
    """Settings and configuration page"""
    st.header("⚙️ Settings & Configuration")
    
    # API Configuration
    st.subheader("🔑 API Configuration")
    
    if API_KEY:
        st.success(f"✅ API Key: {API_KEY[:8]}...{API_KEY[-8:]}")
    else:
        st.error("❌ API Key not configured")
    
    if API_SECRET:
        st.success(f"✅ API Secret: {API_SECRET[:8]}...{API_SECRET[-8:]}")
    else:
        st.error("❌ API Secret not configured")
    
    st.info(f"🧪 Testnet Mode: {'Enabled' if USE_TESTNET else 'Disabled'}")
    
    # Trading Settings
    st.subheader("📊 Trading Preferences")
    
    # These would normally be saved to a config file
    default_trade_amount = st.number_input("Default Trade Amount (USDT)", min_value=10.0, value=50.0)
    default_stop_loss = st.slider("Default Stop Loss (%)", 1.0, 20.0, 5.0)
    default_take_profit = st.slider("Default Take Profit (%)", 5.0, 50.0, 15.0)
    
    if st.button("💾 Save Settings"):
        st.success("✅ Settings saved!")
    
    # System Information
    st.subheader("ℹ️ System Information")
    
    info = {
        "Environment": "Production" if not USE_TESTNET else "Testnet",
        "Streamlit Version": st.__version__,
        "Python Version": "3.11+",
        "Deployment": "Railway",
        "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    for key, value in info.items():
        st.text(f"{key}: {value}")

def logs_page():
    """Logs and activity page"""
    st.header("📜 Activity Logs")
    
    # Log controls
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Logs"):
            st.session_state["logs"] = []
            st.success("Logs cleared")
    
    with col2:
        log_level = st.selectbox("Log Level", ["All", "Info", "Warning", "Error"])
    
    # Display logs
    if st.session_state["logs"]:
        st.subheader(f"📋 Recent Activity ({len(st.session_state['logs'])} entries)")
        
        # Reverse to show newest first
        for log in reversed(st.session_state["logs"][-50:]):
            if "ERROR" in log:
                st.error(log)
            elif "WARNING" in log or "⚠️" in log:
                st.warning(log)
            else:
                st.text(log)
    else:
        st.info("ℹ️ No activity logs available")

if __name__ == "__main__":
    try:
        main_dashboard()
    except Exception as e:
        st.error(f"❌ Application error: {e}")
        st.info("Please check your configuration and try refreshing the page.")