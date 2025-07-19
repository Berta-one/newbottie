#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot Dashboard
===========================================
Features:
- Real-time portfolio with PnL tracking
- Manual Trading (Spot Only)
- Auto-Trader with Risk Management & OCO
- Multi-Strategy Analysis (Quantum + ML + Technical)
- ATR-based SL/TP calculation
- Live WebSocket price updates
- Advanced Analytics
"""

import os
import time
import threading
import json
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
import psutil
from binance.client import Client
from binance.streams import ThreadedWebsocketManager

# ✅ Streamlit Config
st.set_page_config(page_title="Hybrid Quantum Trading Bot", layout="wide")

# ----------------------------
# Import Core Modules
# ----------------------------
from portfolio_manager import PortfolioManager
from trade_executor import TradeExecutor
from risk_manager import RiskManager
from position_monitor import PositionMonitor
from market_analyzer import MarketAnalyzer
from quantum_trading_integration import QuantumTrader
from quantum_engine import QuantumAnalyzer
from dashboard import TradingDashboard
from ensemble_signal_engine import EnsembleSignalEngine

# ----------------------------
# Binance API Setup
# ----------------------------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    st.error("❌ Binance API keys missing.")
    st.stop()

client = Client(API_KEY, API_SECRET)
ws_manager = ThreadedWebsocketManager(API_KEY, API_SECRET)

# ----------------------------
# Initialize Components
# ----------------------------
portfolio_mgr = PortfolioManager(API_KEY, API_SECRET)
risk_mgr = RiskManager(max_risk_percent=0.02, max_positions=5)
trade_exec = TradeExecutor(client, risk_mgr)
position_monitor = PositionMonitor()
market_analyzer = MarketAnalyzer(client)
quantum_trader = QuantumTrader(client)
quantum_analyzer = QuantumAnalyzer()
analytics_dashboard = TradingDashboard()
ensemble_engine = EnsembleSignalEngine(client, quantum_trader, market_analyzer)

# ----------------------------
# Global State
# ----------------------------
AUTO_TRADING = False
STOP_FLAG = threading.Event()
price_data = {}
if "logs" not in st.session_state:
    st.session_state["logs"] = []

# ----------------------------
# WebSocket for Live Prices
# ----------------------------
def start_price_stream():
    ws_manager.start()

    def handle_message(msg):
        if msg['e'] == '24hrTicker':
            symbol = msg['s']
            price_data[symbol] = float(msg['c'])

    ws_manager.start_symbol_ticker_socket(callback=handle_message)

start_price_stream()

# ----------------------------
# Utility Functions
# ----------------------------
def get_system_health():
    return {
        "CPU": f"{psutil.cpu_percent()}%",
        "Memory": f"{psutil.virtual_memory().percent}%",
        "Threads": threading.active_count()
    }

def get_price(symbol: str):
    return price_data.get(symbol, float(client.get_symbol_ticker(symbol=symbol)["price"]))

# ----------------------------
# Auto-Trader Logic
# ----------------------------
def auto_trading_loop():
    while not STOP_FLAG.is_set():
        try:
            signals = market_analyzer.scan_markets()
            total_balance = portfolio_mgr.total_value()
            open_pos = len(position_monitor.get_active_positions())

            for sig in signals:
                trade_exec.auto_execute(sig, total_balance, open_pos, st.session_state["sl_mult"], st.session_state["tp_mult"])
        except Exception as e:
            st.session_state["logs"].append(f"[AUTO ERROR] {e}")
        time.sleep(30)

# ----------------------------
# Streamlit Tabs
# ----------------------------
st.title("🧠 Hybrid Quantum Crypto Trading Bot")
st.caption("Advanced Crypto Trading with Quantum + ML + Technical Strategies")

tabs = st.tabs([
    "📊 Portfolio", "✋ Manual Trading", "🤖 Auto-Trader",
    "⚛ Multi-Strategy", "🛠 Settings", "🩺 Health", "📜 Logs", "📈 Analytics"
])

# ----------------------------------------
# Portfolio Tab
# ----------------------------------------
with tabs[0]:
    st.header("📊 Portfolio Overview")
    try:
        portfolio = portfolio_mgr.get_portfolio()
        total_usd = sum(v["value"] for v in portfolio.values())

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Value (USD)", f"${total_usd:,.2f}")
        with col2:
            st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))

        df = pd.DataFrame([
            {
                "Asset": asset,
                "Balance": data["balance"],
                "Price (USD)": data["price"],
                "Value (USD)": data["value"],
                "Unrealized PnL (%)": data.get("pnl_pct", 0),
                "Unrealized PnL ($)": data.get("pnl_usd", 0)
            }
            for asset, data in portfolio.items()
        ])

        st.dataframe(df, use_container_width=True)
        if not df.empty:
            fig = px.pie(df, names='Asset', values='Value (USD)', title="Portfolio Allocation")
            st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Portfolio fetch error: {e}")

# ----------------------------------------
# Manual Trading Tab
# ----------------------------------------
with tabs[1]:
    st.header("✋ Manual Trading")
    pairs = market_analyzer.get_trading_pairs()
    symbol = st.selectbox("Select Pair", pairs)
    qty = st.number_input("Quantity", min_value=0.0001)
    if st.button("Execute Trade"):
        price = get_price(symbol)
        total_balance = portfolio_mgr.total_value()
        open_pos = len(position_monitor.get_active_positions())

        validation = risk_mgr.validate_trade(symbol, qty, price, total_balance, open_pos)
        if validation["status"]:
            result = trade_exec.manual_trade(symbol, qty, st.session_state["sl_mult"], st.session_state["tp_mult"])
            st.success(result)
            st.session_state["logs"].append(f"[Manual] {result}")
        else:
            st.error(validation["reason"])

# ----------------------------------------
# Auto-Trader Tab
# ----------------------------------------
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
            threading.Thread(target=auto_trading_loop, daemon=True).start()
    st.subheader("Active Positions")
    st.write(position_monitor.get_active_positions())

# ----------------------------------------
# Multi-Strategy Tab
# ----------------------------------------
with tabs[3]:
    st.header("⚛ Multi-Strategy Analysis")
    weights = st.session_state.get("strategy_weights", {"quantum": 30, "ml": 30, "technical": 40})
    min_confidence = st.session_state.get("min_confidence", 0.65)
    st.info(f"Weights: {weights}, Min Confidence: {min_confidence}")

    portfolio_pairs = [f"{asset}USDT" for asset in portfolio.keys()]
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
        st.warning("No signals generated.")

# ----------------------------------------
# Settings Tab
# ----------------------------------------
with tabs[4]:
    st.header("🛠 Settings")
    st.session_state["sl_mult"] = st.slider("Stop Loss Multiplier (ATR)", 0.5, 5.0, st.session_state.get("sl_mult", 1.5), 0.1)
    st.session_state["tp_mult"] = st.slider("Take Profit Multiplier (ATR)", 1.0, 10.0, st.session_state.get("tp_mult", 3.0), 0.5)
    st.success("✅ Settings updated")

# ----------------------------------------
# Health Tab
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
# Logs Tab
# ----------------------------------------
with tabs[6]:
    st.header("📜 Activity Logs")
    for log in st.session_state["logs"][-50:]:
        st.text(log)

# ----------------------------------------
# Analytics Tab
# ----------------------------------------
with tabs[7]:
    st.header("📈 Advanced Analytics")
    analytics_dashboard.render_analytics_dashboard()