import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from dashboard.metrics import compute_metrics, calculate_drawdown

st.set_page_config(page_title="Live Performance Analytics", layout="wide")
st.title("🚀 Live Performance Analytics Dashboard")

# Sidebar controls
st.sidebar.header("Configuration")
data_source = st.sidebar.selectbox("Data Source", [
    "Walk-Forward Optimization", "Quantum Backtest"], index=0)

if data_source == "Walk-Forward Optimization":
    default_path = "results/wfo_equity.csv"
else:
    default_path = "backtest_results/latest_quantum_report.csv"

file_path = st.sidebar.text_input("CSV Path", value=default_path)
refresh = st.sidebar.button("🔄 Refresh Data")

@st.cache_data(ttl=15)
def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=[0], infer_datetime_format=True)
    # Ensure column naming consistency
    if "capital" in df.columns and "equity" not in df.columns:
        df = df.rename(columns={"capital": "equity"})
    return df

if refresh:
    st.cache_data.clear()

df = load_data(file_path)

if df.empty:
    st.warning("No performance data found. Run a backtest or WFO routine first.")
    st.stop()

# MAIN LAYOUT -------------------------------------------------------------
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Equity Curve")
    st.line_chart(df.set_index(df.columns[0])["equity"], height=300)

    # Drawdown Plot
    st.subheader("Drawdown")
    equity_series = df["equity"].astype(float)
    drawdown = (equity_series - equity_series.cummax()) / equity_series.cummax()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[df.columns[0]], y=drawdown, fill='tozeroy', name="Drawdown"))
    fig.update_layout(height=250, yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Key Metrics")
    # Compute metrics based on per-trade pnl; approximate pnl from equity diff
    pnl_series = df["equity"].diff().fillna(0)
    metrics = compute_metrics(pd.DataFrame({"pnl": pnl_series}))
    st.metric("Total Return", f"${metrics['Total Return']:,.2f}")
    st.metric("Max Drawdown", f"{metrics['Max Drawdown']:.1%}")
    st.metric("Sharpe Ratio", f"{metrics['Sharpe Ratio']:.2f}")

st.divider()

# Heat-map of returns per Walk-Forward step if available
if "walk_forward_step" in df.columns:
    st.subheader("Walk-Forward Step Heat-map")
    pivot = df.pivot_table(index="walk_forward_step", values="equity", aggfunc="last")
    if not pivot.empty:
        st.dataframe(pivot.style.background_gradient(cmap="RdYlGn"), height=200)
    else:
        st.info("Heat-map unavailable (no walk-forward labels present).")