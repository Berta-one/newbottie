# -*- coding: utf-8 -*-
"""
hybrid_bot_fixed.py
A clean, UTF-8 Streamlit dashboard for portfolio + system stats.
"""

import streamlit as st
import psutil
import random

# =========================
# Helper Functions
# =========================
def get_system_health():
    """Returns CPU and Memory usage."""
    return {
        "CPU": f"{psutil.cpu_percent()}%",
        "Memory": f"{psutil.virtual_memory().percent}%",
    }

def get_portfolio_mock():
    """Mock portfolio values for PoC."""
    total_usd = random.uniform(1000, 5000)
    total_gbp = total_usd * 0.79
    asset_count = random.randint(5, 15)
    return total_usd, total_gbp, asset_count

# =========================
# Streamlit App
# =========================
st.set_page_config(page_title="📊 Bot Dashboard", layout="wide")
st.title("🤖 Trading Bot Dashboard (PoC)")

# Quick Stats row
col1, col2, col3, col4 = st.columns(4)
total_usd, total_gbp, asset_count = get_portfolio_mock()
health = get_system_health()

with col1:
    st.metric("💵 Portfolio Value (USD)", f"${total_usd:,.2f}")
with col2:
    st.metric("💷 Portfolio Value (GBP)", f"£{total_gbp:,.2f}")
with col3:
    st.metric("🪙 Total Assets", asset_count)
with col4:
    st.metric("🖥️ CPU Usage", health["CPU"])

st.divider()
st.subheader("✅ System Health")
st.write(f"**Memory Usage:** {health['Memory']}")
st.success("Dashboard running smoothly!")
