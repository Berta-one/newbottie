#!/usr/bin/env python3
import os
import time
import threading
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
import psutil

st.set_page_config(page_title="Hybrid Quantum Trading Bot", layout="wide")

from portfolio_manager import PortfolioManager
from trade_executor import TradeExecutor
from risk_manager import RiskManager
from position_monitor import PositionMonitor
from market_analyzer import MarketAnalyzer
from quantum_trading_integration import QuantumTrader
from quantum_engine import QuantumAnalyzer
from dashboard import TradingDashboard
from ensemble_signal_engine import EnsembleSignalEngine

from binance.client import Client

# Config
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    st.error("❌ Binance API keys missing.")
    st.stop()

client = Client(API_KEY, API_SECRET)

portfolio_mgr = PortfolioManager(API_KEY, API_SECRET)
risk_mgr = RiskManager()
trade_exec = TradeExecutor(client, risk_mgr, log_callback=lambda msg: st.session_state["logs"].append(msg))
position_monitor = PositionMonitor()
market_analyzer = MarketAnalyzer(client)
quantum_trader = QuantumTrader(client)
quantum_analyzer = QuantumAnalyzer()
analytics_dashboard = TradingDashboard()
ensemble_engine = EnsembleSignalEngine(client, quantum_trader, market_analyzer)

AUTO_TRADING = False
AUTO_THREAD = None
STOP_FLAG = threading.Event()

if "logs" not in st.session_state:
    st.session_state["logs"] = []

# Settings defaults
if "sl_mult" not in st.session_state:
    st.session_state["sl_mult"] = 1.5
if "tp_mult" not in st.session_state:
    st.session_state["tp_mult"] = 3.0

tabs = st.tabs(["📊 Portfolio", "✋ Manual Trading", "🤖 Auto-Trader", "⚛ Multi-Strategy", "🛠 Settings", "🩺 Health", "📜 Logs", "📈 Analytics"])

# Portfolio
with tabs[0]:
    st.header("📊 Portfolio Overview")
    try:
        portfolio = portfolio_mgr.get_portfolio()
        total_usd = sum(v["value"] for v in portfolio.values())
        st.metric("Total Value (USD)", f"${total_usd:,.2f}")
        df = pd.DataFrame([{"Asset": a, **d} for a, d in portfolio.items()])
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            fig = px.pie(df, names="Asset", values="value", title="Portfolio Allocation")
            st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Portfolio fetch error: {e}")

# Manual Trade
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
            result = trade_exec.manual_trade(symbol, qty, st.session_state["sl_mult"], st.session_state["tp_mult"])
            st.success(result)
        else:
            st.error(validation["reason"])

# Auto-Trader
with tabs[2]:
    st.header("🤖 Auto-Trader")
    if AUTO_TRADING:
        if st.button("🛑 Stop"):
            STOP_FLAG.set()
            AUTO_TRADING = False
    else:
        if st.button("▶️ Start"):
            AUTO_TRADING = True
            STOP_FLAG.clear()
            def loop():
                while not STOP_FLAG.is_set():
                    signals = market_analyzer.scan_markets()
                    total_balance = portfolio_mgr.total_value()
                    open_pos = len(position_monitor.get_active_positions())
                    for sig in signals:
                        trade_exec.auto_execute(sig, total_balance, open_pos, st.session_state["sl_mult"], st.session_state["tp_mult"])
                    time.sleep(30)
            threading.Thread(target=loop, daemon=True).start()
    st.subheader("Active OCO Orders")
    st.write(trade_exec.active_orders)

# Settings
with tabs[4]:
    st.header("🛠 Settings")
    st.session_state["sl_mult"] = st.slider("Stop Loss Multiplier (ATR)", 0.5, 5.0, st.session_state["sl_mult"], 0.1)
    st.session_state["tp_mult"] = st.slider("Take Profit Multiplier (ATR)", 1.0, 10.0, st.session_state["tp_mult"], 0.5)
    st.success("✅ Settings updated")

# Logs
with tabs[6]:
    st.header("📜 Activity Logs")
    for log in st.session_state["logs"][-50:]:
        st.text(log)