#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot Dashboard
===========================================
Streamlit UI for:
- Portfolio Overview
- Manual Trading
- Auto-Trader Control
- Quantum Analysis & Trading
- Settings
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
import streamlit as st
import psutil

# ✅ MUST be first Streamlit command
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

# Binance client
from binance.client import Client
from binance.exceptions import BinanceAPIException

# ----------------------------------------
# Environment & Config
# ----------------------------------------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    st.error("❌ Binance API keys missing. Configure BINANCE_API_KEY and BINANCE_API_SECRET.")
    st.stop()

client = Client(API_KEY, API_SECRET)

# Initialize core objects
portfolio_mgr = PortfolioManager(API_KEY, API_SECRET)
risk_mgr = RiskManager()
trade_exec = TradeExecutor(client, risk_mgr)
position_monitor = PositionMonitor()
market_analyzer = MarketAnalyzer(client)
quantum_trader = QuantumTrader(client)
quantum_analyzer = QuantumAnalyzer()
analytics_dashboard = TradingDashboard()

# Auto-Trader state
AUTO_TRADING = False
AUTO_THREAD = None
STOP_FLAG = threading.Event()

# ----------------------------------------
# Auto-Trader Logic
# ----------------------------------------
def start_auto_trader():
    global AUTO_TRADING, AUTO_THREAD
    AUTO_TRADING = True
    STOP_FLAG.clear()
    AUTO_THREAD = threading.Thread(target=auto_trading_loop, daemon=True)
    AUTO_THREAD.start()

def stop_auto_trader():
    global AUTO_TRADING
    AUTO_TRADING = False
    STOP_FLAG.set()

def auto_trading_loop():
    while not STOP_FLAG.is_set():
        try:
            signals = market_analyzer.scan_markets()
            for sig in signals:
                result = trade_exec.auto_execute(sig)
                st.session_state["logs"].append(f"[AUTO] {datetime.now().isoformat()} {result}")
        except Exception as e:
            st.session_state["logs"].append(f"[AUTO ERROR] {e}")
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

if "logs" not in st.session_state:
    st.session_state["logs"] = []

# ----------------------------------------
# Streamlit UI
# ----------------------------------------
st.title("🧠 Hybrid Quantum Crypto Trading Bot")
st.caption("Advanced Crypto Trading with Technical, ML & Quantum Strategies")

tabs = st.tabs([
    "📊 Portfolio", "✋ Manual Trading", "🤖 Auto-Trader",
    "⚛ Quantum Analysis", "🛠 Settings", "🩺 Health", "📜 Logs", "📈 Analytics"
])

# ----------------------------------------
# Portfolio Tab
# ----------------------------------------
with tabs[0]:
    st.header("📊 Portfolio Overview")
    try:
        portfolio_data = portfolio_mgr.get_portfolio()
        if isinstance(portfolio_data, dict):
            total_usd = sum(v["value"] for v in portfolio_data.values())
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
                    "24h Change": f"{data['change']}%"
                }
                for asset, data in portfolio_data.items()
            ])
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                fig = px.pie(df, names='Asset', values='Value (USD)', title="Portfolio Allocation")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Unable to fetch portfolio data.")
    except Exception as e:
        st.error(f"Portfolio fetch error: {e}")

# ----------------------------------------
# Manual Trading Tab
# ----------------------------------------
with tabs[1]:
    st.header("✋ Manual Trading")
    pairs = market_analyzer.get_trading_pairs()
    symbol = st.selectbox("Select Pair", pairs)
    qty = st.number_input("Quantity", min_value=0.0001, step=0.0001)
    side = st.radio("Side", ["BUY", "SELL"])
    if st.button("Execute Trade"):
        result = trade_exec.manual_trade(symbol, qty, side)
        st.session_state["logs"].append(f"[Manual] {result}")
        st.success(result)

# ----------------------------------------
# Auto-Trader Tab
# ----------------------------------------
with tabs[2]:
    st.header("🤖 Auto-Trader")
    if AUTO_TRADING:
        if st.button("🛑 Stop Auto-Trader"):
            stop_auto_trader()
            st.success("Auto-Trader stopped.")
    else:
        if st.button("▶️ Start Auto-Trader"):
            start_auto_trader()
            st.success("Auto-Trader started.")
    st.subheader("Active Positions")
    st.write(position_monitor.get_active_positions())

# ----------------------------------------
# Quantum Analysis Tab (ALL Portfolio Pairs)
# ----------------------------------------
with tabs[3]:
    st.header("⚛ Quantum Analysis & Trading (All Portfolio Pairs)")
    try:
        portfolio_data = portfolio_mgr.get_portfolio()
        assets = list(portfolio_data.keys())
        if len(assets) < 2:
            st.warning("⚠️ Need at least 2 assets in portfolio for pair analysis.")
        else:
            for i in range(len(assets)):
                for j in range(i + 1, len(assets)):
                    pair = f"{assets[i]}{assets[j]}"
                    st.subheader(f"Quantum Analysis for {pair}")
                    market_data = {
                        "rsi": market_analyzer.get_latest_rsi(pair),
                        "momentum": market_analyzer.get_latest_momentum(pair),
                        "price_volatility": market_analyzer.get_volatility(pair)
                    }
                    signal = quantum_trader.evaluate_signal(market_data)
                    st.json(signal["distribution"])
                    st.write(f"Decision: **{signal['decision']}** (Confidence: {signal['confidence']})")
                    qty = st.number_input(f"Trade Qty for {pair}", min_value=0.0001, step=0.0001, key=f"quantum_qty_{pair}")
                    if st.button(f"Execute Quantum Trade for {pair}"):
                        result = quantum_trader.execute_quantum_trade(pair, market_data, qty)
                        st.session_state["logs"].append(f"[Quantum {pair}] {result}")
                        st.success(result)
    except Exception as e:
        st.error(f"Quantum analysis error: {e}")

# ----------------------------------------
# Settings Tab
# ----------------------------------------
with tabs[4]:
    st.header("🛠 Bot Settings")
    st.caption("Configure risk and strategy parameters")
    risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, st.session_state.get("risk_pct", 1.5), 0.1)
    max_positions = st.slider("Max Open Positions", 1, 10, st.session_state.get("max_positions", 3))
    min_confidence = st.slider("Minimum Signal Confidence", 0.5, 1.0, st.session_state.get("min_confidence", 0.65), 0.01)
    st.session_state.update({"risk_pct": risk_pct, "max_positions": max_positions, "min_confidence": min_confidence})
    st.subheader("📈 Strategy Weights")
    col1, col2, col3 = st.columns(3)
    quantum_weight = col1.number_input("Quantum (%)", 0.0, 100.0, st.session_state.get("quantum_weight", 30.0), 1.0)
    ml_weight = col2.number_input("ML (%)", 0.0, 100.0, st.session_state.get("ml_weight", 30.0), 1.0)
    tech_weight = col3.number_input("Technical (%)", 0.0, 100.0, st.session_state.get("tech_weight", 40.0), 1.0)
    st.session_state["strategy_weights"] = {"quantum": quantum_weight, "ml": ml_weight, "technical": tech_weight}
    st.success("✅ Settings updated!")

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