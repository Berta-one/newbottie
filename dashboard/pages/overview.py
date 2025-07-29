# # dashboard/pages/overview.py

import streamlit as st
import pandas as pd

def show_overview(data):
    st.title("📈 Trading Overview Dashboard")
    st.subheader("Portfolio Snapshot")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Capital", f"${data.get('capital', 0):,.2f}")
        st.metric("Exposure", f"{data.get('exposure', 0)*100:.1f}%")
    with col2:
        st.metric("PnL", f"${data.get('pnl', 0):,.2f}")
        st.metric("Win Rate", f"{data.get('win_rate', 0)*100:.1f}%")

    st.divider()
    st.subheader("Latest Trades")
    trades_df = pd.DataFrame(data.get("trades", []))
    if not trades_df.empty:
        st.dataframe(trades_df.tail(10), use_container_width=True)
    else:
        st.info("No trades executed yet.")
