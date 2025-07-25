# -*- coding: utf-8 -*-
"""
bot_dashboard.py
================
Simple PoC: Streamlit Dashboard with UTF-8 Emojis + Basic Sections
"""

import streamlit as st
import psutil
import os

# =========================
# CONFIGURATION
# =========================
st.set_page_config(page_title="Trading Bot Dashboard", layout="wide")

# Authentication
PASSWORD = os.getenv("BOT_DASH_PASS", "admin123")

# =========================
# AUTHENTICATION GATE
# =========================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Secure Login")
    pwd = st.text_input("Enter Dashboard Password", type="password")
    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Access granted!")
            st.experimental_rerun()
        else:
            st.error("❌ Wrong password!")
    st.stop()

# =========================
# MAIN DASHBOARD
# =========================
st.title("📊 Trading Bot Dashboard")

# Quick Stats
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💰 Portfolio Value (USD)", "$12,450")
with col2:
    st.metric("📈 Today's PnL", "+$230")
with col3:
    st.metric("🪙 Total Assets", "14")

st.divider()

# System Health
st.subheader("🖥️ System Health")
health = {
    "CPU": f"{psutil.cpu_percent()}%",
    "Memory": f"{psutil.virtual_memory().percent}%",
}
col1, col2 = st.columns(2)
col1.metric("CPU Usage", health["CPU"])
col2.metric("Memory Usage", health["Memory"])

st.divider()
st.info("✅ Basic PoC Loaded Successfully. Next: Add features (Auto-Trader, Analytics, Logs).")
