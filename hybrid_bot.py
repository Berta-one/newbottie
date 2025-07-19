#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot Dashboard
===========================================
Features:
- Portfolio Overview
- Manual Trading
- Auto-Trader
- Multi-Strategy Analysis
- Settings
- Health
- Logs
- Performance Analytics (PnL, Equity Curve)
"""

import os
import time
import threading
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
import psutil

# ✅ Streamlit must be set first
st.set_page_config(page_title="Hybrid Quantum Trading Bot", layout="wide")

# Core modules
from portfolio_manager import PortfolioManager
from trade_executor import TradeExecutor
from risk_manager import RiskManager
from position_monitor import PositionMonitor
from market_analyzer import MarketAnalyzer
from quantum_trading_integration import QuantumTrader
from quantum_engine import QuantumAnalyzer
from dashboard import TradingDashboard
from ensemble_signal_engine import EnsembleSignalEngine

# Binance
from binance.client import Client

# ----------------------------------------
# Config
# ----------------------------------------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    st.error("❌ Binance API keys missing.")
    st.stop()

client = Client(API_KEY, API_SECRET)

# Initialize Components
portfolio_mgr = PortfolioManager(API_KEY, API_SECRET)
risk_mgr = RiskManager(max_risk_percent=0.02, max_positions=5)
trade_exec = TradeExecutor(client, risk_mgr, log_callback=lambda msg: st.session_state["logs"].append(msg))
position_monitor = PositionMonitor()
market_analyzer = MarketAnalyzer(client)
quantum_trader = QuantumTrader(client)
quantum_analyzer = QuantumAnalyzer()
analytics_dashboard = TradingDashboard()
ensemble_engine = EnsembleSignalEngine(client, quantum_trader, market_analyzer)

# Session State Defaults
if "logs" not in st.session_state:
    st.session_state["logs"] = []
if "sl_mult" not in st.session_state:
    st.session_state["sl_mult"] = 1.5
if "tp_mult" not in st.session_state:
    st.session_state["tp_mult"] = 3.0

AUTO_TRADING = False
STOP_FLAG = threading.Event()

# ----------------------------------------
# Tabs
# ----------------------------------------
tabs = st.tabs([
    "📊 Portfolio", "✋ Manual Trading", "🤖 Auto-Trader",
    "⚛ Multi-Strategy", "🛠 Settings", "🩺 Health", "📜 Logs", "📈 Performance"
])

# ----------------------------------------
# Portfolio Tab
# ----------------------------------------
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
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Portfolio fetch error: {e}")

# ----------------------------------------
# Manual Trade
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
            result = trade_exec.manual_trade(symbol, qty, st.session_state["sl_mult"], st.session_state["tp_mult"])
            st.success(result)
        else:
            st.error(validation["reason"])

# ----------------------------------------
# Auto-Trader
# ----------------------------------------
with tabs[2]:
    st.header("🤖 Auto-Trader")
    if st.button("▶️ Start Auto-Trader") and not AUTO_TRADING:
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
        st.success("Auto-Trader started.")
    elif st.button("🛑 Stop Auto-Trader") and AUTO_TRADING:
        STOP_FLAG.set()
        AUTO_TRADING = False
        st.warning("Auto-Trader stopped.")
    st.subheader("Active Orders")
    st.write(trade_exec.active_orders)

# ----------------------------------------
# Multi-Strategy Analysis
# ----------------------------------------
with tabs[3]:
    st.header("⚛ Multi-Strategy Analysis")
    weights = st.session_state.get("strategy_weights", {"quantum": 30, "ml": 30, "technical": 40})
    min_confidence = st.session_state.get("min_confidence", 0.65)
    st.info(f"Weights: {weights}, Min Confidence: {min_confidence}")
    try:
        portfolio_pairs = [f"{asset}USDT" for asset in portfolio.keys()]
    except:
        portfolio_pairs = ["BTCUSDT", "ETHUSDT"]

    signals_data = []
    for symbol in portfolio_pairs:
        try:
            signal = ensemble_engine.get_signals(symbol, weights, min_confidence)
            signals_data.append(signal)
        except Exception as e:
            st.error(f"Signal error for {symbol}: {e}")

    if signals_data:
        df_signals = pd.DataFrame([
            {
                "Symbol": s["symbol"],
                "Quantum": f"{s['quantum']['decision']} ({s['quantum']['confidence']:.2f})",
                "ML": f"{s['ml']['decision']} ({s['ml']['confidence']:.2f})",
                "Technical": f"{s['technical']['decision']} ({s['technical']['confidence']:.2f})",
                "Final": f"{s['final']['decision']} ({s['final']['confidence']:.2f})"
            }
            for s in signals_data
        ])
        st.dataframe(df_signals, use_container_width=True)
    else:
        st.warning("No signals available.")

# ----------------------------------------
# Settings
# ----------------------------------------
with tabs[4]:
    st.header("🛠 Settings")
    st.session_state["sl_mult"] = st.slider("Stop Loss Multiplier (ATR)", 0.5, 5.0, st.session_state["sl_mult"], 0.1)
    st.session_state["tp_mult"] = st.slider("Take Profit Multiplier (ATR)", 1.0, 10.0, st.session_state["tp_mult"], 0.5)
    risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, st.session_state.get("risk_pct", 2.0), 0.1)
    st.session_state["risk_pct"] = risk_pct
    st.success("✅ Settings updated")

# ----------------------------------------
# Health
# ----------------------------------------
with tabs[5]:
    st.header("🩺 System Health")
    st.metric("CPU", f"{psutil.cpu_percent()}%")
    st.metric("Memory", f"{psutil.virtual_memory().percent}%")
    st.write("Threads:", threading.active_count())

# ----------------------------------------
# Logs
# ----------------------------------------
with tabs[6]:
    st.header("📜 Activity Logs")
    for log in st.session_state["logs"][-50:]:
        st.text(log)

# ----------------------------------------
# Performance (PnL & Equity)
# ----------------------------------------
with tabs[7]:
    st.header("📈 Performance Analytics")
    equity = trade_exec.get_equity()
    st.metric("Total Realized PnL (USD)", f"${equity:.2f}")
    history = trade_exec.get_trade_history()
    if not history.empty:
        st.subheader("Trade History")
        st.dataframe(history, use_container_width=True)

        # Equity Curve
        history["cumulative_pnl"] = history["pnl"].cumsum().fillna(0)
        fig = px.line(history, x="timestamp", y="cumulative_pnl", title="Equity Curve")
        st.plotly_chart(fig, use_container_width=True)

        # Win Rate
        closed_trades = history[history["status"] == "CLOSED"]
        wins = len(closed_trades[closed_trades["pnl"] > 0])
        total = len(closed_trades)
        win_rate = (wins / total) * 100 if total > 0 else 0
        st.metric("Win Rate", f"{win_rate:.2f}%")
    else:
        st.warning("No closed trades yet.")