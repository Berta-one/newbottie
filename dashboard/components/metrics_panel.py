import streamlit as st
from monitoring.performance_metrics import sharpe_ratio, sortino_ratio, max_drawdown

def render_metrics_panel(returns, equity_curve):
    st.subheader("Performance Metrics")
    st.metric("Sharpe Ratio", f"{sharpe_ratio(returns):.2f}")
    st.metric("Sortino Ratio", f"{sortino_ratio(returns):.2f}")
    st.metric("Max Drawdown", f"{max_drawdown(equity_curve)*100:.2f}%")
