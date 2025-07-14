import streamlit as st
import pandas as pd
import plotly.express as px
import os, time
from dotenv import load_dotenv
from bot_controller import BotController

st.set_page_config(page_title="Bottie", layout="wide", initial_sidebar_state="expanded")

PIN_REQUIRED = "1234"  # Set your dashboard PIN here

def load_logs(log_file, max_lines=200):
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            return f.readlines()[-max_lines:]
    return ["No logs found."]

def get_tailscale_ip():
    import subprocess
    try:
        output = subprocess.check_output("tailscale ip -4", shell=True, text=True).strip()
        return output.splitlines()[0]
    except:
        return "Unavailable"

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
    # Heartbeat check
    if os.path.exists("logs/console_output.log"):
        with open("logs/console_output.log", "r", encoding="utf-8") as f:
            last_lines = f.readlines()[-10:]
        heartbeat_found = any("heartbeat" in l.lower() for l in last_lines)
        if heartbeat_found:
            st.success("Bot heartbeat detected ✅")
        else:
            st.warning("No recent heartbeat detected ⚠️")
    else:
        st.warning("Log file not found.")
    time.sleep(refresh)
    st.rerun()

def show_performance():
    st.header("📊 Performance Overview")
    log_path = "logs/single_pair_performance.json"

    try:
        df = pd.read_json(log_path, lines=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
    except Exception as e:
        st.warning(f"No trade data found. {e}")
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
    ts_ip = get_tailscale_ip()
    remote_url = f"http://{ts_ip}:8501" if ts_ip != "Unavailable" else "Unavailable"
    controller = BotController()
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
    tabs = st.tabs(["📊 Performance", "📡 Logs", "⚙️ Settings", "🧠 Strategy", "💓 Health"])

    with tabs[0]:
        show_performance()
    with tabs[1]:
        show_logs()
    with tabs[2]:
        st.header("⚙️ Settings")
        st.write("Configure your bot settings here.")
        # Add more settings as needed
    with tabs[3]:
        st.header("🧠 Strategy Selection")
        strategy_mode = st.radio("Select Strategy Mode", ["Automated", "Manual"], key="strategy_mode")
        if strategy_mode == "Automated":
            st.success("Automated strategy enabled.")
            # Add automated strategy controls/info here
        else:
            st.info("Manual strategy enabled. You can place trades manually.")
            # Add manual trading controls here
    with tabs[4]:
        st.header("💓 Bot Health & Connection")
        # Heartbeat status is also shown in logs, but summarize here
        if os.path.exists("logs/console_output.log"):
            with open("logs/console_output.log", "r", encoding="utf-8") as f:
                last_lines = f.readlines()[-10:]
            heartbeat_found = any("heartbeat" in l.lower() for l in last_lines)
            if heartbeat_found:
                st.success("Bot heartbeat detected ✅")
            else:
                st.warning("No recent heartbeat detected ⚠️")
        else:
            st.warning("Log file not found.")

if __name__ == "__main__":
    st.set_page_config(page_title="Bot Dashboard", layout="wide")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Enter Dashboard PIN")
        user_pin = st.text_input("PIN", type="password")

        if user_pin == PIN_REQUIRED:
            st.session_state.authenticated = True
            st.success("Access granted")
            st.rerun()
        elif user_pin:
            st.error("Incorrect PIN")
    else:
        dashboard()
