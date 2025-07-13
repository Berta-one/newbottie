# dashboard.py - Upgraded Crypto Bot Dashboard with PIN, Logs, and P&L
import streamlit as st
import pandas as pd
import plotly.express as px
import os, json, time, socket, subprocess
from datetime import datetime
from dotenv import load_dotenv
from bot_controller import BotController

load_dotenv()
PIN_REQUIRED = os.getenv("DASHBOARD_PIN", "1234")

# Session state controller
if "controller" not in st.session_state:
    st.session_state.controller = BotController()
controller = st.session_state.controller

# PIN protection
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def get_tailscale_ip():
    try:
        output = subprocess.check_output("tailscale ip -4", shell=True, text=True).strip()
        return output.splitlines()[0]
    except:
        return "Unavailable"

def load_logs(log_file, max_lines=200):
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.readlines()[-max_lines:]
    return ["No logs found."]

def color_line(line):
    if "error" in line.lower():
        return f":red[{line.strip()}]"
    elif any(x in line.lower() for x in ["profit", "+"]):
        return f":green[{line.strip()}]"
    return f"{line.strip()}"

def show_logs():
    st.header("📡 Live Bot Logs")
    refresh = st.slider("🔁 Refresh every", 2, 10, 5)
    lines = load_logs("logs/console_output.log")
    log_output = "\n".join([color_line(l) for l in lines])
    st.markdown(log_output)
    time.sleep(refresh)
    st.rerun()

def show_performance():
    st.header("📊 Performance Overview")
    log_path = "logs/single_pair_performance.json"

    try:
        df = pd.read_json(log_path, lines=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
    except:
        st.warning("No trade data found.")
        return

    if df.empty:
        st.info("No trades yet.")
    else:
        df['cumulative_pnl'] = df['pnl_percent'].cumsum()
        fig = px.line(df, x='timestamp', y='cumulative_pnl', title="Cumulative P&L")
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Trades", len(df))
        win_rate = (df['pnl_percent'] > 0).mean() * 100
        col2.metric("Win Rate", f"{win_rate:.1f}%")
        col3.metric("Total P&L", f"{df['pnl_percent'].sum():+.2f}%")

        with st.expander("📋 Recent Trades"):
            recent_df = df[['timestamp', 'symbol', 'pnl_percent', 'reason', 'confidence']].tail(20).copy()
            recent_df['timestamp'] = recent_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(recent_df, use_container_width=True)

def dashboard():
    # Sidebar Controls
    st.sidebar.header("🎛️ Controls")

    ts_ip = get_tailscale_ip()
    remote_url = f"http://{ts_ip}:8501" if ts_ip != "Unavailable" else "Unavailable"
    st.sidebar.markdown(f"**Tailscale IP:** `{ts_ip}`")
    st.sidebar.text_input("🔗 Access URL", value=remote_url, key="url", label_visibility="collapsed")
    st.sidebar.download_button("📥 Download Logs", data="\n".join(load_logs("logs/console_output.log")), file_name="console_output.log")

    st.sidebar.subheader("🤖 Bot Status")
    if controller.is_running():
        st.sidebar.success("🟢 Bot is running")
        if st.sidebar.button("🛑 Stop Bot"):
            controller.stop()
            st.sidebar.info("Bot stopped.")
    else:
        st.sidebar.warning("🔴 Bot is stopped")
        if st.sidebar.button("▶️ Start Bot"):
            if controller.start():
                st.sidebar.success("Bot started.")
            else:
                st.sidebar.error("Failed to start bot.")

    if st.sidebar.button("🔄 Refresh Dashboard"):
        st.rerun()

    st.title("🤖 Crypto Trading Bot Dashboard")
    tab1, tab2 = st.tabs(["📊 Performance", "📡 Logs"])
    with tab1:
        show_performance()
    with tab2:
        show_logs()

# ── Main ─────────────────────────────
if __name__ == "__main__":
    st.set_page_config(page_title="Bot Dashboard", layout="wide")

    if not st.session_state.authenticated:
        st.title("🔐 Enter Dashboard PIN")
        user_pin = st.text_input("PIN", type="password")

        if user_pin == PIN_REQUIRED:
            st.session_state.authenticated = True
            st.success("Access granted")
            st.rerun()  # 🟢 rerun inside the correct block

        elif user_pin:
            st.error("Incorrect PIN")

    else:
        dashboard()
