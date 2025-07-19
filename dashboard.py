import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import json

class TradingDashboard:
    def __init__(self):
        self.trade_data_file = 'logs/trades.csv'

    def load_trade_data(self):
        if os.path.exists(self.trade_data_file):
            return pd.read_csv(self.trade_data_file)
        return pd.DataFrame()

    def render_analytics_dashboard(self):
        df = self.load_trade_data()
        if df.empty:
            st.warning("No trade data yet.")
            return

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['cumulative_pnl'] = df['pnl_percent'].cumsum()

        st.subheader("📈 Cumulative PnL")
        fig = px.line(df, x='timestamp', y='cumulative_pnl', title="Cumulative PnL")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Win Rate")
        wins = len(df[df['pnl_percent'] > 0])
        losses = len(df[df['pnl_percent'] < 0])
        st.write(f"Win Rate: {wins / max(1, (wins + losses)) * 100:.2f}%")

        st.subheader("💡 Best Trade")
        st.write(df.loc[df['pnl_percent'].idxmax()])