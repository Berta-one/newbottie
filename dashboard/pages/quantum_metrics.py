# dashboard/pages/quantum_metrics.py

import streamlit as st
import pandas as pd


def display_backtest_metrics(report_df: pd.DataFrame):
    st.subheader("📉 Quantum/Hybrid Backtest Results")
    st.line_chart(report_df.set_index("timestamp")["capital"])

    buy_count = (report_df["signal"] == "BUY").sum()
    sell_count = (report_df["signal"] == "SELL").sum()
    net_gain = report_df["capital"].iloc[-1] - report_df["capital"].iloc[0]

    st.metric("BUY Signals", buy_count)
    st.metric("SELL Signals", sell_count)
    st.metric("Net Gain", f"${net_gain:,.2f}")


def app():
    st.title("🔬 Quantum Metrics Dashboard")

    try:
        df = pd.read_csv("backtest_results/latest_quantum_report.csv", parse_dates=["timestamp"])
        display_backtest_metrics(df)
    except Exception as e:
        st.error("Error loading quantum report data.")
        st.exception(e)


if __name__ == "__main__":
    app()