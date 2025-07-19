#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot Dashboard
===========================================
Streamlit UI for:
- Portfolio Overview
- Manual Trading
- Auto-Trader Control
- Multi-Strategy Analysis
- Settings
- System Health
- Logs
- Analytics
"""

import os
import time
import threading
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
import psutil

# ✅ Streamlit must configure page first
st.set_page_config(page_title="Hybrid Quantum Trading Bot", layout="wide")

# Core Modules
from portfolio_manager import PortfolioManager
from trade_executor import TradeExecutor
from risk_manager import RiskManager
from position_monitor import PositionMonitor
from market_analyzer import MarketAnalyzer
from quantum_trading_integration import QuantumTrader
from quantum_engine import QuantumAnalyzer
from dashboard import TradingDashboard
from ensemble_signal_engine import EnsembleSignalEngine
from order_websocket import OrderWebSocket

from binance.client import Client

# ----------------------------------------
# ENV & CLIENT
# ----------------------------------------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    st.error("❌ Binance API keys missing.")
    st.stop()

client = Client(API_KEY, API_SECRET)

# ----------------------------------------
# Initialize Core Objects
# ----------------------------------------
portfolio_mgr = PortfolioManager(API_KEY, API_SECRET)
risk_mgr = RiskManager(max_risk_percent=0.02, max_positions=5)
position_monitor = PositionMonitor()
trade_exec = TradeExecutor(client, risk_mgr, log_callback=lambda msg: st.session_state["logs"].append(msg))
market_analyzer = MarketAnalyzer(client)
quantum_trader = QuantumTrader(client)
quantum_analyzer = QuantumAnalyzer()
analytics_dashboard = TradingDashboard()
ensemble_engine = EnsembleSignalEngine(client, quantum_trader, market_analyzer)

# WebSocket Listener
ws_listener = OrderWebSocket(client, trade_exec, position_monitor, portfolio_mgr,
                             ui_refresh=lambda: st.experimental_rerun(),
                             log_callback=lambda msg: st.session_state["logs"].append(msg))

# ----------------------------------------
# Session State
# ----------------------------------------
if "logs" not in st.session_state:
    st.session_state["logs"] = []

# Default SL/TP multipliers
if "sl_mult" not in st.session_state:
    st.session_state["sl_mult"] = 1.5
if "tp_mult" not in st.session_state:
    st.session_state["tp_mult"] = 3.0

# Auto-Trader State
AUTO_TRADING = False
STOP_FLAG = threading.Event()

# ----------------------------------------
# Auto-Trader Logic
# ----------------------------------------
def start_auto_trader():
    global AUTO_TRADING
    AUTO_TRADING = True
    STOP_FLAG.clear()

    def loop():
        while not STOP_FLAG.is_set():
            try:
                signals = market_analyzer.scan_markets()
                total_balance = portfolio_mgr.total_value()
                open_pos = len(position_monitor.get_active_positions())
                for sig in signals:
                    trade_exec.auto_execute(sig, total_balance, open_pos,
                                            st.session_state["sl_mult"], st.session_state["tp_mult"])
            except Exception as e:
                st.session_state["logs"].append(f"[AutoTrader ERROR] {e}")
            time.sleep(30)

    threading.Thread(target=loop, daemon=True).start()

def stop_auto_trader():
    global AUTO_TRADING
    AUTO_TRADING = False
    STOP_FLAG.set()

# ----------------------------------------
# System Health
# ----------------------------------------
def get_system_health():
    return {
        "CPU": f"{psutil.cpu_percent()}%",
        "Memory": f"{psutil.virtual_memory().percent}%",
        "Threads": threading.active_count()
    }

# ----------------------------------------
# Streamlit UI
# ----------------------------------------
st.title("🧠 Hybrid Quantum Crypto Trading Bot")
st.caption("Advanced Crypto Trading with Technical, ML & Quantum Strategies")

tabs = st.tabs(["📊 Portfolio", "✋ Manual Trading", "🤖 Auto-Trader",
                "⚛ Multi-Strategy", "🛠 Settings", "🩺 Health", "📜 Logs", "📈 Analytics"])

# ----------------------------------------
# 1. Portfolio Tab
# ----------------------------------------
with tabs[0]:
    st.header("📊 Portfolio Overview")
    try:
        portfolio = portfolio_mgr.get_portfolio()
        total_usd = sum(v["value"] for v in portfolio.values())
        col1, col2 = st.columns(2)
        col1.metric("Total Value (USD)", f"${total_usd:,.2f}")
        col2.metric("Realized PnL", f"${position_monitor.get_realized_pnl():,.2f}")

        df = pd.DataFrame([{"Asset": a, **d} for a, d in portfolio.items()])
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            fig = px.pie(df, names="Asset", values="value", title="Portfolio Allocation")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Portfolio fetch error: {e}")

# ----------------------------------------
# 2. Manual Trading
# ----------------------------------------
with tabs[1]:
    st.header("✋ Manual Trading")
    pairs = market_analyzer.get_trading_pairs()
    symbol = st.selectbox("Select Pair", pairs)
    qty = st.number_input("Quantity", min_value=0.0001)
    if st.button("Execute Trade"):
        total_balance = portfolio_mgr.total_value()
        open_pos = len(position_monitor.get_active_positions())
        price = market_analyzer.get_price(symbol)
        validation = risk_mgr.validate_trade(symbol, qty, price, total_balance, open_pos)
        if validation["status"]:
            atr = market_analyzer.get_atr(symbol)  # Dynamic ATR
            result = trade_exec.manual_trade(symbol, qty, st.session_state["sl_mult"], st.session_state["tp_mult"], atr)
            st.success(result)
        else:
            st.error(validation["reason"])

# ----------------------------------------
# 3. Auto-Trader
# ----------------------------------------
with tabs[2]:
    st.header("🤖 Auto-Trader")
    col1, col2 = st.columns(2)
    if AUTO_TRADING:
        if col1.button("🛑 Stop Auto-Trader"):
            stop_auto_trader()
            st.success("Auto-Trader stopped.")
    else:
        if col1.button("▶️ Start Auto-Trader"):
            start_auto_trader()
            st.success("Auto-Trader started.")
    if col2.button("Start WebSocket Listener"):
        ws_listener.start()
        st.success("WebSocket Listener Started")
    st.subheader("Active OCO Orders")
    st.write(trade_exec.active_orders)
    st.subheader("Active Positions")
    st.write(position_monitor.get_active_positions())

# ----------------------------------------
# 4. Multi-Strategy
# ----------------------------------------
with tabs[3]:
    st.header("⚛ Multi-Strategy Analysis")
    st.write("Quantum + ML + Technical combined signals will be shown here.")
    st.warning("Feature coming in next integration.")

# ----------------------------------------
# 5. Settings
# ----------------------------------------
with tabs[4]:
    st.header("🛠 Settings")
    st.session_state["sl_mult"] = st.slider("Stop Loss Multiplier (ATR)", 0.5, 5.0, st.session_state["sl_mult"], 0.1)
    st.session_state["tp_mult"] = st.slider("Take Profit Multiplier (ATR)", 1.0, 10.0, st.session_state["tp_mult"], 0.5)
    st.success("✅ Settings updated")

# ----------------------------------------
# 6. System Health
# ----------------------------------------
with tabs[5]:
    st.header("🩺 System Health")
    health = get_system_health()
    st.metric("CPU", health["CPU"])
    st.metric("Memory", health["Memory"])
    st.write("Threads:", health["Threads"])
    try:
        st.write("API Status: ✅" if client.ping() == {} else "❌ Failed")
    except Exception:
        st.write("❌ API Check Failed")

# ----------------------------------------
# 7. Logs
# ----------------------------------------
with tabs[6]:
    st.header("📜 Activity Logs")
    for log in st.session_state["logs"][-50:]:
        st.text(log)

# ----------------------------------------
# 8. Analytics
# ----------------------------------------
with tabs[7]:
    st.header("📈 Advanced Analytics")
    analytics_dashboard.render_analytics_dashboard()