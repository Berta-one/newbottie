#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot Dashboard
===========================================
Main Streamlit UI for:
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

# ✅ MUST be the very first Streamlit call
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
# Environment and Config
# ----------------------------------------
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    st.error("❌ Binance API keys are missing. Configure BINANCE_API_KEY and BINANCE_API_SECRET.")
    st.stop()

client = Client(API_KEY, API_SECRET)

# Initialize core objects
portfolio_mgr = PortfolioManager(client)
risk_mgr = RiskManager()
trade_exec = TradeExecutor(client, risk_mgr)
position_monitor = PositionMonitor()
market_analyzer = MarketAnalyzer(client)
quantum_trader = QuantumTrader(client)
quantum_analyzer = QuantumAnalyzer()
analytics_dashboard = TradingDashboard()

# Auto-trader state
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
        portfolio = portfolio_mgr.get_portfolio()
        total_value = portfolio_mgr.total_value()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Value (USD)", f"${total_value:,.2f}")
        with col2:
            st.metric("Last Updated", portfolio_mgr.last_updated())

        if portfolio:
            df = pd.DataFrame([
                {
                    "Asset": asset,
                    "Balance": data["balance"],
                    "Price (USD)": f"${data['price']:.2f}",
                    "Value (USD)": f"${data['value']:.2f}",
                    "24h Change": f"{data['change']}%"
                }
                for asset, data in portfolio.items()
            ])

            st.dataframe(df, use_container_width=True)

            # Pie chart
            fig = px.pie(df, names='Asset', values='Value (USD)', title="Portfolio Allocation")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ No assets found in your portfolio.")
    except Exception as e:
        st.error(f"Portfolio fetch error: {e}")

# ----------------------------------------
# Manual Trading Tab
# ----------------------------------------
with tabs[1]:
    st.header("✋ Manual Trading")
    pairs = market_analyzer.scan_markets()  # Ensure dynamic pair list
    symbol = st.selectbox("Select Pair", [p['symbol'] for p in pairs if 'symbol' in p])
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
# Quantum Analysis Tab
# ----------------------------------------
with tabs[3]:
    st.header("⚛ Quantum Analysis & Trading")

    # Dynamic pair selection (from available pairs)
    available_pairs = [p['symbol'] for p in market_analyzer.scan_markets() if 'symbol' in p]
    if not available_pairs:
        available_pairs = ["BTCUSDT"]  # Fallback default

    selected_pair = st.selectbox("Select Pair for Quantum Analysis", available_pairs)

    # Fetch market data for selected pair
    market_data = {
        "rsi": market_analyzer.get_latest_rsi(selected_pair),
        "momentum": market_analyzer.get_latest_momentum(selected_pair),
        "price_volatility": market_analyzer.get_volatility(selected_pair)
    }

    st.write(f"Performing Quantum Analysis for **{selected_pair}**")

    try:
        # Generate quantum signal
        signal = quantum_trader.evaluate_signal(market_data)

        st.subheader("Quantum Signal")
        st.json(signal["distribution"])
        st.write(f"**Decision:** {signal['decision']} (Confidence: {signal['confidence']})")

        # Display quantum circuit representation
        st.text(signal["circuit"])

        st.subheader("Quantum Diagnostics")
        st.json(quantum_analyzer.get_quantum_diagnostics())

        # Execute trade based on quantum signal
        qty = st.number_input("Trade Quantity", min_value=0.0001, step=0.0001, key="quantum_qty")
        if st.button("Execute Quantum Trade"):
            result = quantum_trader.execute_quantum_trade(selected_pair, market_data, qty)
            st.session_state["logs"].append(f"[Quantum] {result}")
            st.success(result)

    except Exception as e:
        st.error(f"Quantum analysis error: {e}")

# ----------------------------------------
# Settings Tab
# ----------------------------------------
with tabs[4]:
    st.header("🛠 Bot Settings")
    st.caption("Configure risk and strategy parameters")

    # Risk % slider
    risk_pct = st.slider("Risk per Trade (%)", min_value=0.1, max_value=5.0,
                         value=st.session_state.get("risk_pct", 1.5), step=0.1)
    st.session_state["risk_pct"] = risk_pct

    # Max Positions
    max_positions = st.slider("Max Open Positions", min_value=1, max_value=10,
                              value=st.session_state.get("max_positions", 3))
    st.session_state["max_positions"] = max_positions

    # Confidence threshold
    min_confidence = st.slider("Minimum Signal Confidence", min_value=0.5, max_value=1.0,
                                value=st.session_state.get("min_confidence", 0.65), step=0.01)
    st.session_state["min_confidence"] = min_confidence

    # Strategy Weights
    st.subheader("📈 Strategy Weights")
    col1, col2, col3 = st.columns(3)
    with col1:
        quantum_weight = st.number_input("Quantum (%)", min_value=0.0, max_value=100.0,
                                         value=st.session_state.get("quantum_weight", 30.0), step=1.0)
    with col2:
        ml_weight = st.number_input("ML (%)", min_value=0.0, max_value=100.0,
                                    value=st.session_state.get("ml_weight", 30.0), step=1.0)
    with col3:
        tech_weight = st.number_input("Technical (%)", min_value=0.0, max_value=100.0,
                                      value=st.session_state.get("tech_weight", 40.0), step=1.0)

    st.session_state["strategy_weights"] = {
        "quantum": quantum_weight,
        "ml": ml_weight,
        "technical": tech_weight
    }

    st.success("✅ Settings updated successfully!")

# ----------------------------------------
# Health Tab
# ----------------------------------------
with tabs[5]:
    st.header("🩺 System Health")
    health = get_system_health()
    st.metric("CPU", health["CPU"])
    st.metric("Memory", health["Memory"])
    st.write("**Threads:**", health["Threads"])
    try:
        st.write("**API Status:** ✅" if client.ping() == {} else "❌ Failed")
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