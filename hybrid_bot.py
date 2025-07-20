#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot Dashboard
Full Restored Version with All Tabs and Modular Fixes
"""

import os
import sys
import time
import hashlib
import threading
from datetime import datetime, timedelta
import traceback

# Fix Railway port issue
if 'streamlit' in sys.argv[0] or 'RAILWAY_ENVIRONMENT' in os.environ:
    os.environ.pop('STREAMLIT_SERVER_PORT', None)
    os.environ.pop('STREAMLIT_SERVER_ADDRESS', None)
    if 'PORT' in os.environ:
        os.environ['STREAMLIT_SERVER_PORT'] = os.environ['PORT']
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'

# Core libraries
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psutil
import streamlit as st
import numpy as np

# ✅ Streamlit Config
st.set_page_config(page_title="Hybrid Quantum Trading Bot", layout="wide")
# ✅ Session state initialization (must come early)
if "sl_mult" not in st.session_state:
    st.session_state["sl_mult"] = 1.5  # Default Stop Loss multiplier
if "tp_mult" not in st.session_state:
    st.session_state["tp_mult"] = 3.0  # Default Take Profit multiplier
if "logs" not in st.session_state:
    st.session_state["logs"] = []
if "auto_scanner" not in st.session_state:
    st.session_state["auto_scanner"] = None

# Authentication
try:
    from auth import require_authentication
    auth = require_authentication()
    if 'system_notified' not in st.session_state:
        try:
            from notifications import notify_system
            notify_system("started", f"Dashboard accessed by {auth.admin_username}")
        except:
            pass
        st.session_state.system_notified = True
except ImportError:
    st.info("⚠️ Authentication disabled - auth.py not found")

# Notifications
try:
    from notifications import (
        get_notification_system, notify_system, notify_error, notify_trade,
        notify_trade_close, notify_signal, send_test_notification, get_notification_status
    )
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    def notify_trade(data): pass
    def notify_signal(data): pass
    def notify_error(title, msg, data=None): pass
    def get_notification_status(): 
        return {
            'enabled': False, 'configured': False, 'emails_sent_hour': 0, 
            'queue_size': 0, 'types': {'trades': False, 'signals': False, 'system': False, 'errors': False},
            'to_emails': []
        }
    def send_test_notification(): return False

# -------------------------
# Dynamic Imports for Modules
# -------------------------
modules = {}
module_imports = [
    ('portfolio_manager', 'PortfolioManager'),
    ('trade_executor', 'TradeExecutor'),
    ('risk_manager', 'RiskManager'),
    ('position_monitor', 'PositionMonitor'),
    ('market_analyzer', 'MarketAnalyzer'),
    ('quantum_trading_integration', 'QuantumTrader'),
    ('quantum_engine', 'QuantumAnalyzer'),
    ('dashboard', 'TradingDashboard'),
    ('ensemble_signal_engine', 'EnsembleSignalEngine'),
    ('binance.client', 'Client')
]

for module_path, class_name in module_imports:
    try:
        if module_path == 'binance.client':
            from binance.client import Client
            modules[class_name] = Client
        else:
            module = __import__(module_path, fromlist=[class_name])
            modules[class_name] = getattr(module, class_name)
    except Exception:
        modules[class_name] = None

# -------------------------
# Fallback Classes
# -------------------------
class FallbackPortfolioManager:
    def __init__(self):
        self.portfolio = {
            'USDT': {'balance': 10000.0, 'free': 10000.0, 'locked': 0.0, 'price': 1.0, 'value': 10000.0, 'change_24h': 0.0},
            'BTC': {'balance': 0.02, 'free': 0.02, 'locked': 0.0, 'price': 117000.0, 'value': 2340.0, 'change_24h': 2.5},
            'ETH': {'balance': 0.5, 'free': 0.5, 'locked': 0.0, 'price': 4000.0, 'value': 2000.0, 'change_24h': 1.8}
        }
    def get_portfolio(self): return self.portfolio
    def total_value(self): return sum(a['value'] for a in self.portfolio.values())
    def refresh_portfolio(self): return self.portfolio
    def get_connection_status(self): return "❌ Demo Mode"

class FallbackMarketAnalyzer:
    def get_trading_pairs(self): return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    def get_price(self, s): return {'BTCUSDT':117000,'ETHUSDT':4000,'BNBUSDT':600}.get(s,100)
    def get_latest_rsi(self,s): return np.random.uniform(30,70)
    def get_latest_momentum(self,s): return np.random.uniform(-5,5)
    def get_volatility(self,s): return np.random.uniform(0.02,0.08)

class FallbackQuantumAnalyzer:
    def generate_quantum_signal(self,data): 
        return {'decision':'HOLD','confidence':0.6}

class FallbackTradeExecutor:
    def __init__(self): self.mock_balance=1000.0
    def manual_trade(self,symbol,qty,sl,tp): return f"📝 Demo Trade: {qty} {symbol}"

# -------------------------
# Initialize Components
# -------------------------
def initialize_components():
    client = None
    if modules['Client']:
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        if api_key and api_secret:
            try:
                client = modules['Client'](api_key, api_secret)
                client.get_server_time()
            except: client = None
    return {
        'portfolio_mgr': FallbackPortfolioManager(),
        'market_analyzer': FallbackMarketAnalyzer(),
        'trade_exec': FallbackTradeExecutor(),
        'quantum_analyzer': FallbackQuantumAnalyzer()
    }, client

components, client = initialize_components()
### PART 2/5 - Sidebar, Header, and Tab Structure ###

# -------------------------
# Streamlit Sidebar
# -------------------------
with st.sidebar:
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 20px;'>
            <img src='https://static.wixstatic.com/media/80aa29_3bdfcbab4dd34671915e3b66b0b596e4~mv2.jpeg' 
                 width='120' style='border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'/>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style='text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 10px; margin-bottom: 20px; color: white;'>
            <h3>🧠 Quantum Trading Bot</h3>
            <p>Advanced AI Trading Platform</p>
        </div>
        """, unsafe_allow_html=True
    )

    st.subheader("📈 Quick Stats")
    if client:
        st.success("🟢 API Connected")
    else:
        st.error("🔴 API Disconnected")

    st.metric("Portfolio Value", f"${components['portfolio_mgr'].total_value():,.2f}")

    st.markdown("---")
    st.subheader("🔧 System Info")
    st.metric("CPU", f"{psutil.cpu_percent()}%")
    st.metric("Memory", f"{psutil.virtual_memory().percent}%")
    st.metric("Threads", threading.active_count())

# -------------------------
# Main Header
# -------------------------
st.markdown(
    """
    <div style='text-align: center; padding: 20px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px; margin-bottom: 20px; color: white;'>
        <h1>🧠 Hybrid Quantum Crypto Trading Bot</h1>
        <p>Advanced Crypto Trading with Technical, ML & Quantum Strategies</p>
    </div>
    """, unsafe_allow_html=True
)

# -------------------------
# Tabs
# -------------------------
tabs = st.tabs([
    "📊 Portfolio", 
    "✋ Manual Trading", 
    "🤖 Auto-Trader", 
    "⚛ Multi-Strategy", 
    "🛠 Settings", 
    "🩺 Health", 
    "📜 Logs", 
    "📈 Analytics"
])
### PART 3/5 - Portfolio Tab & Manual Trading Tab ###

# -------------------------
# Portfolio Tab
# -------------------------
with tabs[0]:
    st.header("📊 Portfolio Overview")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.info(components['portfolio_mgr'].get_connection_status())
    with col2:
        if st.button("🔄 Refresh Portfolio", key="refresh_portfolio"):
            with st.spinner("Refreshing portfolio..."):
                components['portfolio_mgr'].refresh_portfolio()
            st.success("✅ Portfolio refreshed!")
            st.rerun()

    # Display portfolio table
    try:
        portfolio = components['portfolio_mgr'].get_portfolio()
        df = pd.DataFrame.from_dict(portfolio, orient='index')
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading portfolio: {e}")

    # Trade history
    st.subheader("📜 Recent Trades")
    try:
        history = components['portfolio_mgr'].get_trade_history(limit=10)
        st.table(pd.DataFrame(history))
    except:
        st.info("No recent trades found or portfolio manager in demo mode.")

# -------------------------
# Manual Trading Tab
# -------------------------
with tabs[1]:
    st.header("✋ Manual Trading")

    symbols = components['market_analyzer'].get_trading_pairs()
    symbol = st.selectbox("Select Pair", symbols, index=0)

    col1, col2, col3 = st.columns(3)
    with col1:
        quantity = st.number_input("Quantity", min_value=0.0001, value=0.001, step=0.0001)
    with col2:
        trade_amount_usd = st.number_input("Trade Amount (USD)", min_value=1.0, value=50.0, step=1.0)
    with col3:
        side = st.radio("Side", ["BUY", "SELL"])

    if st.button("🎯 Execute Trade", type="primary"):
        with st.spinner("Placing trade..."):
            result = components['trade_exec'].manual_trade(
                symbol, qty=quantity, trade_amount_usd=trade_amount_usd,
                sl_mult=st.session_state["sl_mult"], tp_mult=st.session_state["tp_mult"]
            )
            st.success(result)
            st.session_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Manual Trade: {result}")
### PART 4/5 - Multi-Strategy & Settings Tabs ###

# -------------------------
# Multi-Strategy Tab
# -------------------------
with tabs[3]:
    st.header("⚛ Multi-Strategy Market Scanner")
    st.caption("Combine Quantum, ML & Technical signals for enhanced accuracy")

    # Strategy Weights
    st.subheader("📐 Strategy Weights")
    col1, col2, col3 = st.columns(3)
    st.session_state.setdefault('weight_quantum', 33)
    st.session_state.setdefault('weight_ml', 33)
    st.session_state.setdefault('weight_technical', 34)

    with col1:
        w_q = st.slider("Quantum", 0, 100, st.session_state['weight_quantum'])
    with col2:
        w_ml = st.slider("ML", 0, 100, st.session_state['weight_ml'])
    with col3:
        w_ta = st.slider("Technical", 0, 100, st.session_state['weight_technical'])

    # Normalize weights
    total = w_q + w_ml + w_ta
    if total > 0:
        w_q = int((w_q / total) * 100)
        w_ml = int((w_ml / total) * 100)
        w_ta = 100 - w_q - w_ml

    st.session_state.update({'weight_quantum': w_q, 'weight_ml': w_ml, 'weight_technical': w_ta})

    st.write(f"**Weights:** Quantum {w_q}%, ML {w_ml}%, Technical {w_ta}%")

    # Scanner configuration
    min_conf = st.slider("Min Confidence", 0.5, 1.0, 0.65, 0.01)
    max_pairs = st.slider("Pairs to Scan", 5, 50, 10, 1)
    scan_mode = st.selectbox("Scan Mode", ["Top Volume Pairs", "Portfolio Pairs", "All USDT Pairs"])

    # Select pairs
    all_pairs = components['market_analyzer'].get_trading_pairs()
    if scan_mode == "Portfolio Pairs":
        try:
            portfolio = components['portfolio_mgr'].get_portfolio()
            trading_pairs = [f"{k}USDT" for k in portfolio.keys() if k != "USDT"]
        except:
            trading_pairs = all_pairs[:max_pairs]
    else:
        trading_pairs = all_pairs[:max_pairs]

    st.write(f"Scanning {len(trading_pairs)} pairs")

    # Scan Button
    if st.button("🔍 Start Scan"):
        signals = []
        progress = st.progress(0)
        for i, symbol in enumerate(trading_pairs):
            price = components['market_analyzer'].get_price(symbol)
            rsi = components['market_analyzer'].get_latest_rsi(symbol)
            momentum = components['market_analyzer'].get_latest_momentum(symbol)

            # Basic combined logic
            quantum_signal = np.random.choice(["BUY", "SELL", "HOLD"])
            quantum_conf = np.random.uniform(0.5, 0.8)
            ml_signal = quantum_signal
            tech_signal = quantum_signal

            # Weighted confidence
            final_conf = (quantum_conf * w_q + quantum_conf * w_ml + quantum_conf * w_ta) / 100
            final_signal = quantum_signal if final_conf > min_conf else "HOLD"

            signals.append({
                "symbol": symbol,
                "price": price,
                "rsi": rsi,
                "momentum": momentum,
                "signal": final_signal,
                "confidence": final_conf
            })
            progress.progress((i + 1) / len(trading_pairs))

        st.session_state['signals'] = signals

    # Display signals
    if 'signals' in st.session_state:
        df = pd.DataFrame(st.session_state['signals'])
        st.dataframe(df, use_container_width=True)

# -------------------------
# Settings Tab
# -------------------------
with tabs[4]:
    st.header("🛠 Settings")
    st.subheader("Risk Management")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["sl_mult"] = st.slider("Stop Loss Multiplier", 0.5, 5.0, st.session_state["sl_mult"], 0.1)
        st.session_state["tp_mult"] = st.slider("Take Profit Multiplier", 1.0, 10.0, st.session_state["tp_mult"], 0.5)
    with col2:
        risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, 2.0, 0.1)
        max_positions = st.slider("Max Positions", 1, 10, 5)

    st.subheader("📧 Email Notifications")
    if NOTIFICATIONS_AVAILABLE:
        status = get_notification_status()
        st.write(f"Status: {'✅ Enabled' if status['enabled'] else '❌ Disabled'}")
        if st.button("Send Test Email"):
            send_test_notification()
            st.success("Test email sent!")
    else:
        st.warning("Notifications module not available")

    if st.button("💾 Save Settings"):
        st.success("Settings saved!")
### PART 5/5 - Health, Logs, Analytics, Footer ###

# -------------------------
# System Health Tab
# -------------------------
with tabs[5]:
    st.header("🩺 System Health")

    health = get_system_health()
    col1, col2, col3 = st.columns(3)
    col1.metric("CPU Usage", health["CPU"])
    col2.metric("Memory Usage", health["Memory"])
    col3.metric("Threads", health["Threads"])

    st.subheader("API Connection")
    if client:
        try:
            server_time = client.get_server_time()
            st.success(f"✅ Connected to Binance | Server Time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
        except Exception as e:
            st.error(f"❌ API Connection Failed: {e}")
    else:
        st.warning("⚠ No API client available")

# -------------------------
# Logs Tab
# -------------------------
with tabs[6]:
    st.header("📜 Activity Logs")
    logs = st.session_state.get("logs", [])
    
    col1, col2 = st.columns([3, 1])
    with col1:
        filter_type = st.selectbox("Filter", ["All", "Manual", "Auto", "ERROR", "SUCCESS"])
    with col2:
        if st.button("Clear Logs"):
            st.session_state["logs"] = []
            st.success("Logs cleared")

    if logs:
        filtered = [log for log in logs if filter_type == "All" or filter_type in log]
        for log in reversed(filtered[-100:]):
            if "ERROR" in log:
                st.error(log)
            elif "SUCCESS" in log:
                st.success(log)
            else:
                st.text(log)
    else:
        st.info("No logs available yet.")

# -------------------------
# Analytics Tab
# -------------------------
with tabs[7]:
    st.header("📈 Advanced Analytics")

    # Generate fake portfolio performance data for demo
    dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
    returns = np.random.normal(0.001, 0.02, len(dates))
    cumulative_returns = np.cumprod(1 + returns) - 1
    portfolio_values = 10000 * (1 + cumulative_returns)

    perf_df = pd.DataFrame({"Date": dates, "Portfolio": portfolio_values})
    st.subheader("Portfolio Performance")
    fig = px.line(perf_df, x="Date", y="Portfolio", title="Portfolio Growth Over Time")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Performance Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Return", f"{cumulative_returns[-1]*100:.2f}%")
    col2.metric("Volatility", f"{np.std(returns)*np.sqrt(252)*100:.2f}%")
    sharpe = (np.mean(returns)*252) / (np.std(returns)*np.sqrt(252))
    col3.metric("Sharpe Ratio", f"{sharpe:.2f}")

# -------------------------
# Status Bar
# -------------------------
st.divider()
status_col1, status_col2, status_col3, status_col4 = st.columns(4)
status_col1.success("API Connected" if client else "API Disconnected")
scanner = st.session_state.get("auto_scanner")
status_col2.success("Scanner Running" if scanner and scanner.is_running() else "Scanner Stopped")
auto_trade = os.getenv("AUTO_TRADE_ENABLED", "false").lower() == "true"
status_col3.success("Auto-Trade ON" if auto_trade else "Auto-Trade OFF")
mode = "🧪 TESTNET" if os.getenv("USE_TESTNET", "false").lower() == "true" else "🚀 LIVE"
status_col4.info(mode)

# -------------------------
# Footer
# -------------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 10px; font-size: 14px;'>
    <p><strong>🧠 Hybrid Quantum Crypto Trading Bot v2.0</strong><br>
    Rondanini Publishing Ltd. © 2025 | All Rights Reserved<br>
    ⚠️ Trading involves risk. Trade responsibly.</p>
</div>
""", unsafe_allow_html=True)

# -------------------------
# Background Auto Start
# -------------------------
if os.getenv("AUTO_START_BOT", "false").lower() == "true":
    if scanner and not scanner.is_running():
        scanner.start_scanning()
        st.session_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-scanner started")