"""
dashboard.py
====================
Provides performance analytics for Streamlit UI.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import os

class TradingDashboard:
    def render_analytics_dashboard(self):
        st.subheader("Performance Overview")
        log_file = "logs/trades.csv"
        if not os.path.exists(log_file):
            st.warning("No trade history found.")
            return

        df = pd.read_csv(log_file)
        st.metric("Total Trades", len(df))
        st.metric("PnL (USD)", f"${df['pnl'].sum():,.2f}")

        fig = px.line(df, x="timestamp", y="pnl", title="Cumulative PnL Over Time")
        st.plotly_chart(fig, use_container_width=True)