 -*- coding: utf-8 -*-
"""
dashboard.py
============
Trading Analytics + Bot Control Panel + Live Logs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
import subprocess
import psutil

BOT_SCRIPT = "bot_service.py"
LOG_FILE = "bot_service.log"


# =========================
# BOT STATUS & CONTROL
# =========================
def is_bot_running():
    for proc in psutil.process_iter(["cmdline"]):
        if BOT_SCRIPT in " ".join(proc.info["cmdline"]):
            return True
    return False


# =========================
# DATA UTILITIES
# =========================
def safe_get_column_sum(df, column_name, default=0.0):
    if df.empty or column_name not in df.columns:
        return default
    return df[column_name].sum()


def safe_get_column_mean(df, column_name, default=0.0):
    if df.empty or column_name not in df.columns:
        return default
    return df[column_name].mean()


def load_trade_data():
    data_sources = [
        "logs/trades.csv",
        "logs/trade_history.csv",
        "logs/portfolio_trades.csv",
        "logs/trading_log.csv",
    ]
    for source in data_sources:
        if os.path.exists(source):
            try:
                df = pd.read_csv(source)
                if not df.empty:
                    return df
            except:
                continue
    return pd.DataFrame(
        columns=[
            "timestamp",
            "symbol",
            "pnl",
            "pnl_percent",
            "quantity",
            "entry_price",
            "exit_price",
        ]
    )


def calculate_pnl_if_missing(df):
    if df.empty:
        return df
    if "pnl" not in df.columns:
        if (
            "entry_price" in df.columns
            and "exit_price" in df.columns
            and "quantity" in df.columns
        ):
            df["pnl"] = (df["exit_price"] - df["entry_price"]) * df["quantity"]
        else:
            df["pnl"] = 0.0
    if "pnl_percent" not in df.columns:
        if "entry_price" in df.columns and "exit_price" in df.columns:
            df["pnl_percent"] = (
                (df["exit_price"] - df["entry_price"]) / df["entry_price"]
            ) * 100
        else:
            df["pnl_percent"] = 0.0
    return df


# =========================
# MAIN DASHBOARD
# =========================
def render_analytics_dashboard():
    st.title("ðŸ“Š Trading Analytics Dashboard")

    # ✔️ Bot Status & Control
    bot_running = is_bot_running()
    status_text = "ðŸŸ¢ Bot is Running" if bot_running else "ðŸ”´ Bot is Stopped"
    status_color = "green" if bot_running else "red"
    st.markdown(
        f"### **Bot Status:** <span style='color:{status_color};'>{status_text}</span>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("â–¶ Start Bot"):
            if not bot_running:
                subprocess.Popen(["python", BOT_SCRIPT])
                st.success("✔️ Bot started!")
            else:
                st.info("Bot is already running")
    with col2:
        if st.button("â¹ Stop Bot"):
            if bot_running:
                os.system(f"pkill -f {BOT_SCRIPT}")
                st.warning("ðŸ›‘ Bot stopped!")
            else:
                st.info("Bot is not running")

    st.divider()

    # ✔️ Live Logs
    st.subheader("ðŸ“œ Live Bot Logs")
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                logs = f.readlines()[-30:]  # Last 30 log lines
                st.text("".join(logs))
        except:
            st.info("Unable to read logs.")
    else:
        st.info("No log file found yet.")

    st.divider()

    # ✔️ Load trade data
    df = load_trade_data()
    df = calculate_pnl_if_missing(df)

    if df.empty:
        st.warning("📝 No trade data available yet. Start trading to see analytics!")
        return

    # Convert timestamp
    if "timestamp" in df.columns:
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        except:
            pass

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    total_trades = len(df)
    total_pnl = safe_get_column_sum(df, "pnl", 0.0)
    best_trade = df["pnl"].max() if "pnl" in df.columns and not df.empty else 0
    wins = len(df[df["pnl"] > 0]) if "pnl" in df.columns else 0
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

    with col1:
        st.metric("Total Trades", total_trades)
    with col2:
        st.metric("PnL (USD)", f"${total_pnl:,.2f}")
    with col3:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col4:
        st.metric("Best Trade", f"${best_trade:,.2f}")

    # Performance chart
    st.subheader("ðŸ“ˆ Portfolio Performance")
    if "timestamp" in df.columns and "pnl" in df.columns and len(df) > 0:
        df_sorted = df.sort_values("timestamp")
        df_sorted["cumulative_pnl"] = df_sorted["pnl"].cumsum()
        fig = px.line(
            df_sorted,
            x="timestamp",
            y="cumulative_pnl",
            title="Cumulative P&L Over Time",
        )
        fig.update_layout(xaxis_title="Time", yaxis_title="Cumulative P&L (USD)")
        st.plotly_chart(fig, use_container_width=True)

    # Recent trades
    st.subheader("ðŸ“‹ Recent Trades")
    if len(df) > 0:
        display_columns = [
            col
            for col in ["timestamp", "symbol", "pnl", "pnl_percent"]
            if col in df.columns
        ]
        st.dataframe(df.tail(10)[display_columns], use_container_width=True)


# Run app
if __name__ == "__main__":
    render_analytics_dashboard()

