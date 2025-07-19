#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot Dashboard
===========================================
Streamlit UI for:
- Portfolio Overview
- Manual Trading
- Auto-Trader Control
- Multi-Strategy Analysis (Quantum + ML + Technical)
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

# ✅ MUST be the first Streamlit call
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
risk_mgr = RiskManager(max_risk_percent=0.02, max_positions=5)
trade_exec = TradeExecutor(client, risk_mgr)
position_monitor = PositionMonitor()
market_analyzer = MarketAnalyzer(client)
quantum_trader = QuantumTrader(client)
quantum_analyzer = QuantumAnalyzer()
analytics_dashboard = TradingDashboard()
ensemble_engine = EnsembleSignalEngine(client, quantum_trader, market_analyzer)

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
            weights = st.session_state.get("strategy_weights", {"quantum": 30, "ml": 30, "technical": 40})
            min_confidence = st.session_state.get("min_confidence", 0.65)
            portfolio_pairs = [f"{asset}USDT" for asset in portfolio_mgr.get_portfolio().keys()]

            for symbol in portfolio_pairs:
                signal = ensemble_engine.get_signals(symbol, weights, min_confidence)
                if signal and signal["final"]["confidence"] >= min_confidence:
                    price = market_analyzer.get_price(symbol)
                    qty = 0.001  # TODO: dynamic qty via risk manager
                    open_positions = len(position_monitor.get_active_positions())
                    total_balance_usd = portfolio_mgr.total_value()

                    validation = risk_mgr.validate_trade(symbol, qty, price, total_balance_usd, open_positions)
                    if validation["status"]:
                        result = trade_exec.auto_execute(signal)
                        st.session_state["logs"].append(f"[AUTO] {datetime.now().isoformat()} {result}")
                    else:
                        st.session_state["logs"].append(f"[RISK BLOCKED] {symbol} - {validation['reason']}")
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
    "⚛ Multi-Strategy", "🛠 Settings", "🩺 Health", "📜 Logs", "📈 Analytics"
])

# 1. Portfolio Tab
with tabs[0]:
    st.header("📊 Portfolio Overview")
    try:
        portfolio = portfolio_mgr.get_portfolio()
        total_usd = sum(v["value"] for v in portfolio.values())
        col1, col2 = st.columns(2)
        col1.metric("Total Value (USD)", f"${total_usd:,.2f}")
        col2.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))

        df = pd.DataFrame([
            {"Asset": a, "Balance": d["balance"], "Price (USD)": d["price"], "Value (USD)": d["value"], "24h Change": f"{d['change']}%"}
            for a, d in portfolio.items()
        ])
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            fig = px.pie(df, names='Asset', values='Value (USD)', title="Portfolio Allocation")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Portfolio fetch error: {e}")

# 2. Manual Trading Tab
with tabs[1]:
    st.header("✋ Manual Trading")
    pairs = market_analyzer.get_trading_pairs()
    symbol = st.selectbox("Select Pair", pairs)
    qty = st.number_input("Quantity", min_value=0.0001, step=0.0001)
    side = st.radio("Side", ["BUY", "SELL"])
    if st.button("Execute Trade"):
        price = market_analyzer.get_price(symbol)
        validation = risk_mgr.validate_trade(symbol, qty, price, portfolio_mgr.total_value(), len(position_monitor.get_active_positions()))
        if validation["status"]:
            result = trade_exec.manual_trade(symbol, qty, side)
            st.success(result)
        else:
            st.error(f"❌ Trade blocked: {validation['reason']}")

# 3. Auto-Trader Tab
with tabs[2]:
    st.header("🤖 Auto-Trader")
    if AUTO_TRADING:
        if st.button("🛑 Stop Auto-Trader"): stop_auto_trader(); st.success("Stopped.")
    else:
        if st.button("▶️ Start Auto-Trader"): start_auto_trader(); st.success("Started.")
    st.subheader("Active Positions")
    st.write(position_monitor.get_active_positions())

# 4. Multi-Strategy Tab
with tabs[3]:
    st.header("⚛ Multi-Strategy Analysis")
    weights = st.session_state.get("strategy_weights", {"quantum": 30, "ml": 30, "technical": 40})
    min_confidence = st.session_state.get("min_confidence", 0.65)
    st.info(f"Weights: {weights}, Min Confidence: {min_confidence}")
    portfolio_pairs = [f"{asset}USDT" for asset in portfolio.keys()]
    signals_data = [ensemble_engine.get_signals(sym, weights, min_confidence) for sym in portfolio_pairs]
    df = pd.DataFrame([{
        "Symbol": s["symbol"], "Quantum": f"{s['quantum']['decision']} ({s['quantum']['confidence']:.2f})",
        "ML": f"{s['ml']['decision']} ({s['ml']['confidence']:.2f})",
        "Technical": f"{s['technical']['decision']} ({s['technical']['confidence']:.2f})",
        "Final": f"{s['final']['decision']} ({s['final']['confidence']:.2f})"
    } for s in signals_data if s])
    st.dataframe(df, use_container_width=True)

# 5. Settings Tab
with tabs[4]:
    st.header("🛠 Bot Settings")
    risk_pct = st.slider("Risk per Trade (%)", 0.1, 5.0, 2.0, 0.1)
    max_positions = st.slider("Max Positions", 1, 10, 5)
    min_confidence = st.slider("Min Confidence", 0.5, 1.0, 0.65, 0.01)
    col1, col2, col3 = st.columns(3)
    q = col1.number_input("Quantum (%)", 0.0, 100.0, 30.0, 1.0)
    m = col2.number_input("ML (%)", 0.0, 100.0, 30.0, 1.0)
    t = col3.number_input("Technical (%)", 0.0, 100.0, 40.0, 1.0)
    st.session_state.update({"risk_pct": risk_pct, "max_positions": max_positions, "min_confidence": min_confidence,
                             "strategy_weights": {"quantum": q, "ml": m, "technical": t}})
    st.success("✅ Settings saved")

# 6. Health Tab
with tabs[5]:
    st.header("🩺 System Health")
    health = get_system_health()
    st.metric("CPU", health["CPU"]); st.metric("Memory", health["Memory"])
    st.write("Threads:", health["Threads"])
    try: st.write("API Status: ✅" if client.ping() == {} else "❌ Failed")
    except: st.write("❌ API Check Failed")

# 7. Logs Tab
with tabs[6]:
    st.header("📜 Activity Logs")
    for log in st.session_state["logs"][-50:]:
        st.text(log)

# 8. Analytics Tab
with tabs[7]:
    st.header("📈 Advanced Analytics")
    analytics_dashboard.render_analytics_dashboard()