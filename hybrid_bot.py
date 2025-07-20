#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot Dashboard
-------------------------------------------
Streamlit App for:
- Portfolio Overview
- Manual Trading
- Auto-Trader Control
- Multi-Strategy Analysis
- Risk Management Settings
- System Health
- Logs
- Advanced Analytics
"""

import os
import time
import threading
from datetime import datetime

import pandas as pd
import plotly.express as px
import psutil
import streamlit as st

# ✅ Detect PORT for Railway/Render/Heroku deployment
PORT = int(os.environ.get("PORT", 8501))

# ✅ Streamlit Config
st.set_page_config(page_title="Hybrid Quantum Trading Bot", layout="wide")

# -------------------------
# Core Module Imports
# -------------------------
from portfolio_manager import PortfolioManager
from trade_executor import TradeExecutor
from risk_manager import RiskManager
from position_monitor import PositionMonitor
from market_analyzer import MarketAnalyzer
from quantum_trading_integration import QuantumTrader
from quantum_engine import QuantumAnalyzer
from dashboard import TradingDashboard
from ensemble_signal_engine import EnsembleSignalEngine

# Binance API
from binance.client import Client

# -------------------------
# Load Environment Config
# -------------------------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    st.error("❌ Binance API keys missing. Please set BINANCE_API_KEY and BINANCE_API_SECRET.")
    st.stop()

client = Client(API_KEY, API_SECRET)

# -------------------------
# Initialize Core Objects
# -------------------------
portfolio_mgr = PortfolioManager(API_KEY, API_SECRET)
risk_mgr = RiskManager(max_risk_percent=0.02, max_positions=5)
position_monitor = PositionMonitor()
market_analyzer = MarketAnalyzer(client)
quantum_trader = QuantumTrader(client)
quantum_analyzer = QuantumAnalyzer()
analytics_dashboard = TradingDashboard()
ensemble_engine = EnsembleSignalEngine(client, quantum_trader, market_analyzer)

# ✅ Trade Executor with logging callback
if "logs" not in st.session_state:
    st.session_state["logs"] = []
trade_exec = TradeExecutor(client, risk_mgr, log_callback=lambda msg: st.session_state["logs"].append(msg))

# -------------------------
# State Management
# -------------------------
AUTO_TRADING = False
STOP_FLAG = threading.Event()

# Default SL/TP multipliers
if "sl_mult" not in st.session_state:
    st.session_state["sl_mult"] = 1.5
if "tp_mult" not in st.session_state:
    st.session_state["tp_mult"] = 3.0

# -------------------------
# Functions
# -------------------------
def auto_trader_loop():
    """Run Auto-Trading with signal scanning."""
    while not STOP_FLAG.is_set():
        try:
            signals = market_analyzer.scan_markets()
            total_balance = portfolio_mgr.total_value()
            open_positions = len(position_monitor.get_active_positions())
            for sig in signals:
                trade_exec.auto_execute(sig, total_balance, open_positions, st.session_state["sl_mult"], st.session_state["tp_mult"])
        except Exception as e:
            st.session_state["logs"].append(f"[AUTO ERROR] {e}")
        time.sleep(30)

def get_system_health():
    return {
        "CPU": f"{psutil.cpu_percent()}%",
        "Memory": f"{psutil.virtual_memory().percent}%",
        "Threads": threading.active_count()
    }

# -------------------------
# UI Layout
# -------------------------
st.title("🧠 Hybrid Quantum Crypto Trading Bot")
st.caption("Advanced Crypto Trading with Technical, ML & Quantum Strategies")

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
        portfolio = portfolio_mgr.get_portfolio()
        if portfolio:
            total_usd = sum(v["value"] for v in portfolio.values())
            col1, col2 = st.columns(2)
            col1.metric("Total Value (USD)", f"${total_usd:,.2f}")
            col2.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))

            df = pd.DataFrame([{"Asset": a, "Balance": d["balance"], "Price": d["price"], "Value": d["value"], "Change%": d["change"]} for a, d in portfolio.items()])
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                fig = px.pie(df, names="Asset", values="Value", title="Portfolio Allocation")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠ No portfolio data available.")
    except Exception as e:
        st.error(f"Portfolio fetch error: {e}")

# -------------------------
# Manual Trading Tab
# -------------------------
with tabs[1]:
    st.header("✋ Manual Trading")
    pairs = market_analyzer.get_trading_pairs()
    symbol = st.selectbox("Select Pair", pairs)
    qty = st.number_input("Quantity", min_value=0.0001, step=0.0001)
    if st.button("Execute Trade"):
        total_balance = portfolio_mgr.total_value()
        open_positions = len(position_monitor.get_active_positions())
        price = market_analyzer.get_price(symbol)
        validation = risk_mgr.validate_trade(symbol, qty, price, total_balance, open_positions)
        if validation["status"]:
            result = trade_exec.manual_trade(symbol, qty, st.session_state["sl_mult"], st.session_state["tp_mult"])
            st.success(result)
        else:
            st.error(f"❌ Trade blocked: {validation['reason']}")

# -------------------------
# Auto-Trader Tab
# -------------------------
with tabs[2]:
    st.header("🤖 Auto-Trader")
    if st.button("▶️ Start Auto-Trader") and not AUTO_TRADING:
        AUTO_TRADING = True
        STOP_FLAG.clear()
        threading.Thread(target=auto_trader_loop, daemon=True).start()
        st.success("✅ Auto-Trader started.")
    if st.button("🛑 Stop Auto-Trader") and AUTO_TRADING:
        STOP_FLAG.set()
        AUTO_TRADING = False
        st.warning("⏹ Auto-Trader stopped.")
    st.subheader("Active Orders")
    st.write(trade_exec.active_orders)

# -------------------------
# Multi-Strategy Tab
# -------------------------
with tabs[3]:
    st.header("⚛ Multi-Strategy Analysis (Quantum + ML + Technical)")
    weights = st.session_state.get("strategy_weights", {"quantum": 30, "ml": 30, "technical": 40})
    min_conf = st.session_state.get("min_confidence", 0.65)
    st.info(f"Weights: {weights}, Min Confidence: {min_conf}")

    try:
        portfolio_pairs = [f"{asset}USDT" for asset in portfolio.keys()]
    except:
        portfolio_pairs = ["BTCUSDT", "ETHUSDT"]

    signals_data = []
    for symbol in portfolio_pairs:
        try:
            signal = ensemble_engine.get_signals(symbol, weights, min_conf)
            signals_data.append(signal)
        except Exception as e:
            st.error(f"Signal error for {symbol}: {e}")

    if signals_data:
        df = pd.DataFrame([
            {
                "Symbol": s["symbol"],
                "Quantum": f"{s['quantum']['decision']} ({s['quantum']['confidence']:.2f})",
                "ML": f"{s['ml']['decision']} ({s['ml']['confidence']:.2f})",
                "Technical": f"{s['technical']['decision']} ({s['technical']['confidence']:.2f})",
                "Final": f"{s['final']['decision']} ({s['final']['confidence']:.2f})"
            }
            for s in signals_data
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No signals generated yet.")

# -------------------------
# Settings Tab
# -------------------------
with tabs[4]:
    st.header("🛠 Bot Settings")
    st.session_state["sl_mult"] = st.slider("Stop Loss Multiplier (ATR)", 0.5, 5.0, st.session_state["sl_mult"], 0.1)
    st.session_state["tp_mult"] = st.slider("Take Profit Multiplier (ATR)", 1.0, 10.0, st.session_state["tp_mult"], 0.5)
    risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, st.session_state.get("risk_pct", 2.0), 0.1)
    max_positions = st.slider("Max Positions", 1, 10, st.session_state.get("max_positions", 5))
    min_conf = st.slider("Min Confidence", 0.5, 1.0, st.session_state.get("min_confidence", 0.65), 0.01)
    st.session_state.update({"risk_pct": risk_pct, "max_positions": max_positions, "min_confidence": min_conf})
    st.success("✅ Settings updated!")

# -------------------------
# Health Tab
# -------------------------
with tabs[5]:
    st.header("🩺 System Health")
    health = get_system_health()
    st.metric("CPU", health["CPU"])
    st.metric("Memory", health["Memory"])
    st.write(f"Threads: {health['Threads']}")

# -------------------------
# Logs Tab
# -------------------------
with tabs[6]:
    st.header("📜 Activity Logs")
    for log in st.session_state["logs"][-50:]:
        st.text(log)

# -------------------------
# Analytics Tab
# -------------------------
with tabs[7]:
    st.header("📈 Advanced Analytics")
    analytics_dashboard.render_analytics_dashboard()