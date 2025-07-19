#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot Dashboard
===========================================
Features:
- Portfolio Overview
- Manual Trading
- Auto-Trader Control
- Multi-Strategy Analysis (Quantum + ML + Technical)
- Settings
- Real-Time Order WebSocket
- PnL Tracking (Realized & Unrealized)
- Logs
- Advanced Analytics
"""

import os
import time
import threading
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
import psutil

# ✅ First Streamlit command
st.set_page_config(page_title="Hybrid Quantum Trading Bot", layout="wide")

# Core imports
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

# Binance
from binance.client import Client

# ----------------------------------------
# Config
# ----------------------------------------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    st.error("❌ Binance API keys missing. Set BINANCE_API_KEY and BINANCE_API_SECRET.")
    st.stop()

client = Client(API_KEY, API_SECRET)

# Initialize objects
portfolio_mgr = PortfolioManager(API_KEY, API_SECRET)
risk_mgr = RiskManager(max_risk_percent=0.02, max_positions=5)
position_monitor = PositionMonitor()
trade_exec = TradeExecutor(client, risk_mgr, log_callback=lambda msg: st.session_state["logs"].append(msg))
market_analyzer = MarketAnalyzer(client)
quantum_trader = QuantumTrader(client)
quantum_analyzer = QuantumAnalyzer()
analytics_dashboard = TradingDashboard()
ensemble_engine = EnsembleSignalEngine(client, quantum_trader, market_analyzer)

# Auto-Trader
AUTO_TRADING = False
STOP_FLAG = threading.Event()

if "logs" not in st.session_state:
    st.session_state["logs"] = []

# SL/TP multipliers
if "sl_mult" not in st.session_state:
    st.session_state["sl_mult"] = 1.5
if "tp_mult" not in st.session_state:
    st.session_state["tp_mult"] = 3.0

# ----------------------------------------
# WebSocket for Orders & Positions
# ----------------------------------------
order_ws = OrderWebSocket(client, trade_exec, position_monitor, log_callback=lambda msg: st.session_state["logs"].append(msg))
order_ws.start()

# ----------------------------------------
# Auto-Trader Loop
# ----------------------------------------
def auto_trading_loop():
    while not STOP_FLAG.is_set():
        signals = market_analyzer.scan_markets()
        total_balance = portfolio_mgr.total_value()
        open_pos = len(position_monitor.get_active_positions())

        for sig in signals:
            trade_exec.auto_execute(sig, total_balance, open_pos, st.session_state["sl_mult"], st.session_state["tp_mult"])
        time.sleep(30)

# ----------------------------------------
# Utilities
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
st.caption("Spot-only bot with OCO SL/TP, Risk Control & Real-Time Tracking")

tabs = st.tabs([
    "📊 Portfolio", "✋ Manual Trading", "🤖 Auto-Trader",
    "⚛ Multi-Strategy", "🛠 Settings", "🩺 Health", "📜 Logs", "📈 Analytics"
])

# ----------------------------------------
# 1. Portfolio & PnL
# ----------------------------------------
with tabs[0]:
    st.header("📊 Portfolio Overview")
    try:
        portfolio = portfolio_mgr.get_portfolio()
        total_usd = sum(v["value"] for v in portfolio.values())
        st.metric("Total Value (USD)", f"${total_usd:,.2f}")

        # Realized PnL
        st.metric("Realized PnL (USD)", f"${position_monitor.get_realized_pnl():,.2f}")

        # Unrealized PnL
        unrealized = position_monitor.get_unrealized_pnl(lambda s: float(client.get_symbol_ticker(symbol=s)["price"]))
        if unrealized:
            st.write("Unrealized PnL:", unrealized)

        df = pd.DataFrame([{"Asset": a, **d} for a, d in portfolio.items()])
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            fig = px.pie(df, names="Asset", values="value", title="Portfolio Allocation")
            st.plotly_chart(fig)
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
            atr = market_analyzer.get_atr(symbol)
            result = trade_exec.manual_trade(symbol, qty, st.session_state["sl_mult"], st.session_state["tp_mult"], atr)
            st.success(result)
        else:
            st.error(validation["reason"])

# ----------------------------------------
# 3. Auto-Trader
# ----------------------------------------
with tabs[2]:
    st.header("🤖 Auto-Trader")
    if AUTO_TRADING:
        if st.button("🛑 Stop"):
            STOP_FLAG.set()
            AUTO_TRADING = False
            st.success("Auto-Trader stopped.")
    else:
        if st.button("▶️ Start"):
            STOP_FLAG.clear()
            AUTO_TRADING = True
            threading.Thread(target=auto_trading_loop, daemon=True).start()
            st.success("Auto-Trader started.")

    st.subheader("Active OCO Orders")
    st.write(trade_exec.active_orders)

# ----------------------------------------
# 4. Multi-Strategy Signals
# ----------------------------------------
with tabs[3]:
    st.header("⚛ Multi-Strategy Analysis")
    weights = st.session_state.get("strategy_weights", {"quantum": 30, "ml": 30, "technical": 40})
    min_confidence = st.session_state.get("min_confidence", 0.65)
    st.info(f"Weights: {weights}, Min Confidence: {min_confidence}")

    portfolio_pairs = [f"{a}USDT" for a in portfolio.keys()]
    signals_data = []
    for symbol in portfolio_pairs:
        try:
            signal = ensemble_engine.get_signals(symbol, weights, min_confidence)
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

# ----------------------------------------
# 5. Settings
# ----------------------------------------
with tabs[4]:
    st.header("🛠 Bot Settings")
    st.session_state["sl_mult"] = st.slider("Stop Loss Multiplier (ATR)", 0.5, 5.0, st.session_state["sl_mult"], 0.1)
    st.session_state["tp_mult"] = st.slider("Take Profit Multiplier (ATR)", 1.0, 10.0, st.session_state["tp_mult"], 0.5)
    st.success("✅ Settings updated")

# ----------------------------------------
# 6. Health
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