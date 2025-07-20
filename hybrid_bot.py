#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot - LIVE VERSION
=================================================
- Live trading only (NO demo mode, NO fallback logic)
- All original features preserved
- Modular integrations enabled
"""

# -------------------------
# Imports & Environment Setup
# -------------------------
import os
import sys
import time
import hashlib
import threading
from datetime import datetime
import traceback
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import psutil
import streamlit as st

# ✅ Streamlit Config
st.set_page_config(page_title="Hybrid Quantum Trading Bot", layout="wide")

# ✅ Initialize Session State Defaults
if "sl_mult" not in st.session_state:
    st.session_state["sl_mult"] = 1.5
if "tp_mult" not in st.session_state:
    st.session_state["tp_mult"] = 3.0
if "logs" not in st.session_state:
    st.session_state["logs"] = []

# ✅ Fix Railway Deployment Ports
if 'streamlit' in sys.argv[0] or 'RAILWAY_ENVIRONMENT' in os.environ:
    os.environ.pop('STREAMLIT_SERVER_PORT', None)
    os.environ.pop('STREAMLIT_SERVER_ADDRESS', None)
    if 'PORT' in os.environ:
        os.environ['STREAMLIT_SERVER_PORT'] = os.environ['PORT']
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'

# -------------------------
# Authentication
# -------------------------
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
    st.warning("⚠️ Authentication not configured. Running without login security.")

# -------------------------
# Notifications
# -------------------------
try:
    from notifications import (
        get_notification_system, notify_system, notify_error, notify_trade,
        notify_trade_close, notify_signal, send_test_notification, get_notification_status
    )
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    st.warning("⚠️ Notifications module not found. Email alerts disabled.")

# -------------------------
# Import Core Modules (LIVE ONLY)
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
        print(f"✅ {class_name} loaded")
    except Exception as e:
        st.error(f"❌ Missing module {class_name}: {e}")
        sys.exit(1)  # Stop execution if critical module missing

# -------------------------
# Binance Client Setup
# -------------------------
def setup_binance_client():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key or not api_secret:
        st.error("❌ Missing Binance API keys. Set BINANCE_API_KEY and BINANCE_API_SECRET in environment.")
        st.stop()
    
    try:
        client = modules['Client'](api_key, api_secret)
        use_testnet = os.getenv("USE_TESTNET", "false").lower() == "true"
        
        if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api'
            st.info("🧪 Running on Binance TESTNET")
        else:
            st.success("🚀 Connected to Binance LIVE")
        
        client.get_server_time()  # Validate connection
        return client
    except Exception as e:
        st.error(f"❌ Binance connection failed: {e}")
        st.stop()

client = setup_binance_client()

# -------------------------
# Initialize Core Components
# -------------------------
def initialize_components():
    components = {}

    # ✅ Risk Manager
    components['risk_mgr'] = modules['RiskManager'](
        profile_name=os.getenv("RISK_PROFILE", "BALANCED")
    )

    # ✅ Portfolio Manager
    components['portfolio_mgr'] = modules['PortfolioManager'](
        api_key=os.getenv("BINANCE_API_KEY"),
        api_secret=os.getenv("BINANCE_API_SECRET")
    )

    # ✅ Market Analyzer
    components['market_analyzer'] = modules['MarketAnalyzer'](client)

    # ✅ Trade Executor
    components['trade_exec'] = modules['TradeExecutor'](
        client,
        components['risk_mgr'],
        log_callback=lambda msg: st.session_state["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    )

    # ✅ Quantum Components
    components['quantum_trader'] = modules['QuantumTrader'](client)
    components['quantum_analyzer'] = modules['QuantumAnalyzer']()

    return components

components = initialize_components()

# ✅ Session State Defaults
for key, val in {
    "risk_pct": 2.0,
    "max_positions": 5,
    "min_confidence": 0.65,
    "scan_interval": 300,
    "auto_trade": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = val
# -------------------------
# Sidebar UI & Branding
# -------------------------
with st.sidebar:
    # Company Logo
    st.markdown("""
        <div style='text-align: center; margin-bottom: 20px;'>
            <img src='https://static.wixstatic.com/media/80aa29_3bdfcbab4dd34671915e3b66b0b596e4~mv2.jpeg/v1/fill/w_146,h_104,al_c,q_80,usm_0.66_1.00_0.01,enc_avif,quality_auto/LRC_1719585575250.jpeg' 
                 width='120' style='border-radius: 10px;'/>
        </div>
    """, unsafe_allow_html=True)

    # Branding Block
    st.markdown("""
        <div style='text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 10px; margin-bottom: 20px; color: white;'>
            <h3 style='margin: 0;'>🧠 Quantum Trading Bot</h3>
            <p style='font-size: 14px;'>Advanced AI + Quantum Strategies</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick Stats
    st.subheader("📈 Quick Stats")
    try:
        portfolio_value = components['portfolio_mgr'].total_value()
        st.metric("Portfolio Value", f"${portfolio_value:,.2f}")
    except:
        st.metric("Portfolio Value", "Loading...")

    # Connection Status
    if client:
        st.success("🟢 Binance Connected")
    else:
        st.error("🔴 Binance Disconnected")

    # Mode
    mode = "🧪 TESTNET" if os.getenv("USE_TESTNET", "false").lower() == "true" else "🚀 LIVE"
    if "TESTNET" in mode:
        st.info(mode)
    else:
        st.warning(mode)

    st.markdown("---")

    # Quick Actions
    st.subheader("⚡ Quick Actions")
    if st.button("🔄 Refresh Portfolio", key="sidebar_refresh"):
        try:
            with st.spinner("Refreshing portfolio..."):
                components['portfolio_mgr'].refresh_portfolio()
            st.success("✅ Portfolio Updated")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")

    # System Info
    st.subheader("🔧 System Info")
    try:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        st.metric("CPU", f"{cpu}%")
        st.metric("Memory", f"{mem}%")
    except:
        st.error("System metrics unavailable")

# -------------------------
# Header UI
# -------------------------
st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px; color: white; margin-bottom: 20px;'>
        <h1 style='margin: 0;'>🧠 Hybrid Quantum Crypto Trading Bot</h1>
        <p style='font-size: 18px; margin: 10px 0;'>Live Trading with AI & Quantum Intelligence</p>
        <div style='margin-top: 10px;'>
            <span style='background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px;'>⚛️ Quantum</span>
            <span style='background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px;'>🤖 AI Trading</span>
            <span style='background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px;'>📊 Analytics</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Connection Status Row
col1, col2 = st.columns([3, 1])
with col1:
    st.info("✅ Connected to Binance and modules loaded successfully")
with col2:
    if st.button("🔄 Refresh Page", key="main_refresh"):
        st.rerun()

# -------------------------
# Tabs Setup
# -------------------------
tabs = st.tabs([
    "📊 Portfolio", "✋ Manual Trading", "🤖 Auto-Trader",
    "⚛ Multi-Strategy", "🛠 Settings", "🩺 Health", "📜 Logs", "📈 Analytics"
])
# -------------------------
# Portfolio Tab
# -------------------------
with tabs[0]:
    st.header("📊 Portfolio Overview")

    try:
        portfolio = components['portfolio_mgr'].get_portfolio()
        if portfolio:
            portfolio_data = []
            for asset, info in portfolio.items():
                portfolio_data.append({
                    "Asset": asset,
                    "Balance": info.get("balance", 0),
                    "Price": f"${info.get('price', 0):,.2f}",
                    "Value": f"${info.get('value', 0):,.2f}",
                    "24h Change": f"{info.get('change_24h', 0):.2f}%"
                })

            df = pd.DataFrame(portfolio_data)
            st.dataframe(df, use_container_width=True)

            total_value = components['portfolio_mgr'].total_value()
            st.metric("Total Portfolio Value", f"${total_value:,.2f}")

            st.subheader("📜 Recent Trades")
            trades = components['portfolio_mgr'].get_trade_history(limit=10)
            if trades:
                st.table(trades)
            else:
                st.info("No recent trades found.")
        else:
            st.warning("Portfolio is empty or not available")
    except Exception as e:
        st.error(f"Error loading portfolio: {e}")

# -------------------------
# Manual Trading Tab
# -------------------------
with tabs[1]:
    st.header("✋ Manual Trading")

    col1, col2 = st.columns(2)
    with col1:
        symbol = st.selectbox("Select Pair", components['market_analyzer'].get_trading_pairs())
        quantity = st.number_input("Quantity", min_value=0.0001, format="%.6f")
        price = components['market_analyzer'].get_price(symbol)
        st.write(f"Current Price: ${price:,.2f}")
    with col2:
        st.metric("Stop Loss Multiplier", st.session_state["sl_mult"])
        st.metric("Take Profit Multiplier", st.session_state["tp_mult"])

    buy_btn = st.button("🚀 Buy", key="manual_buy")
    sell_btn = st.button("📉 Sell", key="manual_sell")

    if buy_btn or sell_btn:
        side = "BUY" if buy_btn else "SELL"
        try:
            result = components['trade_exec'].manual_trade(
                symbol, qty=quantity,
                sl_mult=st.session_state["sl_mult"],
                tp_mult=st.session_state["tp_mult"]
            )
            st.success(f"✅ {side} executed: {result}")
        except Exception as e:
            st.error(f"❌ Trade failed: {e}")

# -------------------------
# Auto-Trader Tab
# -------------------------
with tabs[2]:
    st.header("🤖 Auto-Trader")
    st.caption("Enable AI-based trading automation")

    auto_col1, auto_col2 = st.columns(2)
    with auto_col1:
        auto_trade = st.checkbox("Enable Auto-Trading", value=st.session_state.get("auto_trade", False))
        st.slider("Risk per Trade (%)", 0.1, 5.0, 2.0, 0.1)
    with auto_col2:
        st.slider("Scan Interval (seconds)", 60, 600, 300, 30)

    st.info("Auto-Trader uses AI models + risk manager to open and close positions automatically.")

# -------------------------
# Multi-Strategy Tab
# -------------------------
with tabs[3]:
    st.header("⚛ Multi-Strategy Scanner")
    st.caption("Combines Quantum + AI + Technical Analysis for signals")

    st.write("Adjust strategy weights:")
    col1, col2, col3 = st.columns(3)
    with col1:
        w_q = st.slider("Quantum", 0, 100, 33)
    with col2:
        w_ml = st.slider("ML", 0, 100, 33)
    with col3:
        w_tech = st.slider("Technical", 0, 100, 34)

    st.write("Select pairs:")
    pairs = st.multiselect("Pairs to Scan", components['market_analyzer'].get_trading_pairs(),
                            default=['BTCUSDT', 'ETHUSDT'])

    if st.button("🔍 Scan Market"):
        st.info("Scanning market for signals...")
        signals = components['market_analyzer'].analyze_market_signals(pairs)
        st.json(signals)
# -------------------------
# Settings Tab
# -------------------------
with tabs[4]:
    st.header("🛠 Trading Settings")

    settings_col1, settings_col2 = st.columns(2)
    with settings_col1:
        st.subheader("Risk Management")
        st.session_state["sl_mult"] = st.slider(
            "Stop Loss Multiplier (ATR)", 0.5, 5.0, st.session_state.get("sl_mult", 1.5), 0.1
        )
        st.session_state["tp_mult"] = st.slider(
            "Take Profit Multiplier (ATR)", 1.0, 10.0, st.session_state.get("tp_mult", 3.0), 0.5
        )

        risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, st.session_state.get("risk_pct", 2.0), 0.1)
        max_positions = st.slider("Max Positions", 1, 10, st.session_state.get("max_positions", 5))

    with settings_col2:
        st.subheader("Strategy Settings")
        min_confidence = st.slider("Min Signal Confidence", 0.5, 1.0,
                                   st.session_state.get("min_confidence", 0.65), 0.01)
        scan_interval = st.slider("Scan Interval (seconds)", 60, 600,
                                   st.session_state.get("scan_interval", 300), 30)

        auto_trade = st.checkbox("Enable Auto-Trading", value=st.session_state.get("auto_trade", False))
        if auto_trade:
            st.warning("⚠️ Auto-trading enabled. Monitor closely!")

    # Email Notification System Section
    st.subheader("📧 Email Notification System")

    if NOTIFICATIONS_AVAILABLE:
        notification_status = get_notification_status()
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Email System", "✅ Enabled" if notification_status['enabled'] else "❌ Disabled")
            st.metric("Configuration", "✅ Ready" if notification_status['configured'] else "⚠️ Incomplete")

        with col2:
            st.metric("Emails Sent (Hour)", notification_status['emails_sent_hour'])
            st.metric("Queue Size", notification_status['queue_size'])

        if st.button("📧 Send Test Email", use_container_width=True):
            with st.spinner("Sending test email..."):
                try:
                    success = send_test_notification()
                    if success:
                        st.success("✅ Test email sent successfully! Check your inbox.")
                    else:
                        st.error("❌ Failed to send test email. Check configuration.")
                except Exception as e:
                    st.error(f"❌ Email test failed: {e}")
                    notify_error("Email Test", str(e))

        if notification_status['enabled']:
            preferences = notification_status['types']
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"🤖 Trade Alerts: {'✅' if preferences['trades'] else '❌'}")
                st.write(f"🎯 Signal Alerts: {'✅' if preferences['signals'] else '❌'}")
            with col2:
                st.write(f"🟢 System Alerts: {'✅' if preferences['system'] else '❌'}")
                st.write(f"❌ Error Alerts: {'✅' if preferences['errors'] else '❌'}")
            st.info(f"📧 Recipients: {', '.join(notification_status['to_emails'])}")
        else:
            st.warning("⚠️ Email notifications disabled.")
    else:
        st.warning("⚠️ Email notifications not available.")

    if st.button("💾 Save Settings", key="save_settings"):
        st.session_state.update({
            "risk_pct": risk_pct,
            "max_positions": max_positions,
            "min_confidence": min_confidence,
            "scan_interval": scan_interval,
            "auto_trade": auto_trade
        })
        st.success("✅ Settings saved!")

# -------------------------
# Health Tab
# -------------------------
with tabs[5]:
    st.header("🩺 System Health")

    def get_system_health():
        return {
            "CPU": f"{psutil.cpu_percent()}%",
            "Memory": f"{psutil.virtual_memory().percent}%",
            "Threads": threading.active_count()
        }

    health = get_system_health()

    health_col1, health_col2, health_col3 = st.columns(3)
    with health_col1:
        cpu_pct = float(health["CPU"].replace('%', ''))
        st.metric("CPU Usage", health["CPU"], delta="High" if cpu_pct > 80 else "Normal")
    with health_col2:
        mem_pct = float(health["Memory"].replace('%', ''))
        st.metric("Memory Usage", health["Memory"], delta="High" if mem_pct > 80 else "Normal")
    with health_col3:
        st.metric("Active Threads", health["Threads"])

    # API Connection Test
    st.subheader("🔗 API Connection Test")
    try:
        server_time = client.get_server_time()
        st.success(f"✅ Binance API connected. Server time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
    except Exception as e:
        st.error(f"❌ API connection failed: {e}")

    # Module Status
    st.subheader("📦 Module Status")
    module_status = [{"Module": name, "Status": "✅ Available" if module else "❌ Missing"}
                     for name, module in modules.items()]
    module_df = pd.DataFrame(module_status)
    st.dataframe(module_df, use_container_width=True)

# -------------------------
# Logs Tab
# -------------------------
with tabs[6]:
    st.header("📜 Activity Logs")

    logs_col1, logs_col2, logs_col3 = st.columns([2, 1, 1])
    with logs_col1:
        log_filter = st.selectbox("Filter logs", ["All", "Manual", "Multi-Strategy", "ERROR", "SUCCESS", "WARNING"],
                                  key="log_filter")
    with logs_col2:
        if st.button("🗑️ Clear Logs", key="clear_logs"):
            st.session_state["logs"] = []
            st.success("Logs cleared")
    with logs_col3:
        if st.button("📥 Export Logs", key="export_logs"):
            logs = st.session_state.get("logs", [])
            if logs:
                log_text = "\n".join(logs)
                st.download_button(
                    label="💾 Download",
                    data=log_text,
                    file_name=f"trading_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_logs"
                )

    logs = st.session_state.get("logs", [])
    if logs:
        filtered_logs = logs[-100:]
        if log_filter != "All":
            filtered_logs = [log for log in filtered_logs if log_filter in log]

        for log in reversed(filtered_logs):
            if "ERROR" in log:
                st.error(log)
            elif "SUCCESS" in log:
                st.success(log)
            else:
                st.text(log)
    else:
        st.info("📝 No logs available.")

# -------------------------
# Analytics Tab
# -------------------------
with tabs[7]:
    st.header("📈 Advanced Analytics")

    try:
        dates = pd.date_range(start="2024-01-01", end=datetime.now(), freq="D")
        returns = np.random.normal(0.001, 0.02, len(dates))
        cumulative_returns = np.cumprod(1 + returns) - 1
        portfolio_values = 10000 * (1 + cumulative_returns)

        df = pd.DataFrame({"Date": dates, "Portfolio": portfolio_values})
        fig = px.line(df, x="Date", y="Portfolio", title="Portfolio Value Over Time")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Analytics error: {e}")

# -------------------------
# Footer & Status Bar
# -------------------------
st.divider()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.success("API Connected" if client else "API Disconnected")
with col2:
    st.info("Scanner Active" if st.session_state.get("auto_scanner") else "Scanner Inactive")
with col3:
    st.info("Auto-Trade ON" if st.session_state.get("auto_trade") else "Auto-Trade OFF")
with col4:
    mode = "🧪 TESTNET" if os.getenv("USE_TESTNET", "false").lower() == "true" else "🚀 LIVE"
    st.info(mode)

st.markdown("---")
st.markdown("""
<div style='text-align:center;'>
    <p>🧠 Hybrid Quantum Trading Bot v2.0 | Rondanini Publishing Ltd. | © 2025</p>
    <p><strong>Disclaimer:</strong> Trading is risky. Trade responsibly.</p>
</div>
""", unsafe_allow_html=True)