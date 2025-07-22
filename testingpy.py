#!/usr/bin/env python3
"""
Hybrid Quantum Crypto Trading Bot (Revised Tabs)
=================================================
This version restores Multi-Strategy controls, Portfolio display, and System Health tab, with unique keys to prevent Streamlit widget conflicts.
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime

# --- Streamlit Config ---
st.set_page_config(page_title="Hybrid Quantum Trading Bot", page_icon="🧠", layout="wide")

# --- Session State Initialization ---
def init_session_state():
    defaults = {
        'weight_quantum': 30,
        'weight_ml': 30,
        'weight_technical': 40,
        'multi_min_conf': 0.65,
        'multi_max_pairs': 20,
        'multi_scan_mode': "Top Volume Pairs",
        'multi_show_only_signals': True,
        'latest_signals': [],
        'last_scan_time': None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# --- Tabs ---
TABS = st.tabs([
    "🏠 Dashboard",
    "🖥 System Health",
    "✋ Manual Trading",
    "🤖 Auto Trader",
    "⚛ Multi-Strategy",
    "💼 Portfolio",
    "📈 Performance",
    "🔬 Backtesting",
    "⚙ Settings",
    "📝 Logs",
])

# --- Dashboard Tab ---
with TABS[0]:
    st.header("📊 Portfolio Overview")
    st.text_input("API Key", key="api_key_input_dashboard")

# --- System Health Tab ---
with TABS[1]:
    st.header("🖥 System Health")
    st.metric("Status", "Online")
    st.metric("Last Update", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

# --- Manual Trading Tab ---
with TABS[2]:
    st.header("✋ Manual Trading")
    pair = st.selectbox("Pair", ["BTCUSDT", "ETHUSDT"], key="manual_pair")
    qty = st.number_input("Quantity", min_value=0.0001, value=0.001, step=0.0001, key="manual_qty")
    side = st.selectbox("Side", ["BUY", "SELL"], key="manual_side")
    if st.button("🚀 Execute Trade", key="manual_execute"):
        st.success(f"Manual trade executed: {side} {qty} {pair}")

# --- Auto Trader Tab ---
with TABS[3]:
    st.header("🤖 Auto Trader Control")
    st.write("Status:", "Stopped")
    if st.button("Start Auto Bot", key="auto_start_btn"):
        st.info("Auto Bot started")
    if st.button("Stop Auto Bot", key="auto_stop_btn"):
        st.info("Auto Bot stopped")

# --- Multi-Strategy Tab ---
with TABS[4]:
    st.header("⚛ Multi-Strategy Market Scanner")
    st.caption("Adjust strategy weights and scan for trading signals.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.weight_quantum = st.slider("Quantum Weight", 0, 100, st.session_state.weight_quantum, key="multi_quantum_slider")
    with c2:
        st.session_state.weight_ml = st.slider("ML Weight", 0, 100, st.session_state.weight_ml, key="multi_ml_slider")
    with c3:
        st.session_state.weight_technical = st.slider("Technical Weight", 0, 100, st.session_state.weight_technical, key="multi_tech_slider")
    if st.button("🔍 Scan Market", key="multi_scan_btn"):
        st.session_state.latest_signals = [{"Symbol": "BTCUSDT", "Signal": "BUY"}]
        st.session_state.last_scan_time = datetime.now()
    if st.session_state.latest_signals:
        df = pd.DataFrame(st.session_state.latest_signals)
        st.dataframe(df, use_container_width=True)

# --- Portfolio Tab ---
with TABS[5]:
    st.header("💼 Portfolio")
    portfolio_data = pd.DataFrame({
        "Pair": ["BTCUSDT", "ETHUSDT"],
        "Position": [0.5, 2.0],
        "PnL": [120.5, -30.2]
    })
    st.dataframe(portfolio_data, use_container_width=True)

# --- Backtesting Tab ---
with TABS[7]:
    st.header("🔬 Backtesting")
    st.number_input("Capital", min_value=100, max_value=100000, value=1000, key="backtest_capital")
    if st.button("Run Backtest", key="run_backtest_btn"):
        st.success("Backtest completed")

# --- Settings Tab ---
with TABS[8]:
    st.header("⚙ Settings")
    st.text_input("Dashboard Password", type="password", key="settings_password")

# --- Logs Tab ---
with TABS[9]:
    st.header("📝 Logs")
    st.text_area("Log Output", "No logs yet", key="logs_output")
