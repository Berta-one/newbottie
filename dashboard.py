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

        # Live wallet display
        st.subheader("💰 Live Wallet (Binance)")
        try:
            from binance.client import Client
            import os
            binance_api_key = os.getenv("BINANCE_API_KEY")
            binance_api_secret = os.getenv("BINANCE_API_SECRET")
            if binance_api_key and binance_api_secret:
                client = Client(binance_api_key, binance_api_secret)
                account_info = client.get_account()
                balances = account_info['balances']
                df_wallet = pd.DataFrame(balances)
                df_wallet = df_wallet[df_wallet['free'].astype(float) > 0]
                df_wallet['free'] = df_wallet['free'].astype(float)
                df_wallet['locked'] = df_wallet['locked'].astype(float)
                st.dataframe(df_wallet[['asset', 'free', 'locked']], use_container_width=True)
                # Show total USDT and PnL if available
                usdt_row = df_wallet[df_wallet['asset'] == 'USDT']
                if not usdt_row.empty:
                    st.metric("USDT Balance", usdt_row['free'].values[0])
                else:
                    st.info("No USDT balance found.")
            else:
                st.warning("Binance API keys not found in environment variables.")
        except Exception as e:
            st.error(f"Error fetching wallet: {e}")
        st.info("If you see no wallet, check your API keys and Binance account.")

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
        st.subheader("💰 Live Wallet (Binance)")
        try:
            from binance.client import Client
            import os
            binance_api_key = os.getenv("BINANCE_API_KEY")
            binance_api_secret = os.getenv("BINANCE_API_SECRET")
            if binance_api_key and binance_api_secret:
                client = Client(binance_api_key, binance_api_secret)
                account_info = client.get_account()
                balances = account_info['balances']
                df_wallet = pd.DataFrame(balances)
                df_wallet['free'] = df_wallet['free'].astype(float)
                df_wallet['locked'] = df_wallet['locked'].astype(float)
                df_wallet = df_wallet[df_wallet['free'] > 0]
                st.dataframe(df_wallet[['asset', 'free', 'locked']], use_container_width=True)
                # Show total USDT and PnL if available
                usdt_row = df_wallet[df_wallet['asset'] == 'USDT']
                if not usdt_row.empty:
                    st.metric("USDT Balance", usdt_row['free'].values[0])
                else:
                    st.info("No USDT balance found.")
            else:
                st.warning("Binance API keys not found in environment variables.")
        except Exception as e:
            st.error(f"Error fetching wallet: {e}")
        st.info("If you see no wallet, check your API keys and Binance account.")

    with tabs[1]:
        show_logs()
        st.info("Live logs from your bot will appear here. If empty, check your log file path and bot status.")

    with tabs[2]:
        st.header("⚙️ Settings")
        trading_mode = st.radio("Trading Mode", ["Automated", "Manual"], key="settings_trading_mode")
        risk_level = st.selectbox("Risk Level", ["Conservative", "Balanced", "Aggressive"], key="settings_risk_level")
        log_retention = st.slider("Log Retention (days)", 1, 30, 7, key="settings_log_retention")
        notification = st.multiselect("Notification Channels", ["Email", "Telegram"], key="settings_notification")
        st.write(f"Current mode: {trading_mode}, Risk: {risk_level}, Log retention: {log_retention} days, Notification: {', '.join(notification) if notification else 'None'}")
        st.info("Settings are for display only. To make changes, edit your config or .env file.")

    with tabs[3]:
        st.header("🧠 Strategy Selection & ML Status")
        try:
            from enhanced_ml_strategy import ml_strategy, get_ml_enhanced_signal
            st.write("Current ML Model Path:", ml_strategy.model_path)
            if ml_strategy.model:
                st.success("ML model loaded and active.")
            else:
                st.warning("No ML model loaded. Using traditional strategy only.")
            if st.button("Retrain ML Model"):
                st.info("Retraining not implemented in dashboard. Use CLI or script.")
            st.write("---")
            st.write("Current ML-enhanced signal preview:")
            klines_json = st.text_area("Paste klines JSON (list of lists, 120+ entries)", "", key="ml_klines_json")
            import json
            if klines_json:
                try:
                    user_klines = json.loads(klines_json)
                    signal, confidence = get_ml_enhanced_signal(user_klines)
                    st.metric("Signal", signal)
                    st.metric("Confidence", f"{confidence:.2f}")
                except Exception as e:
                    st.error(f"Error parsing klines: {e}")
            else:
                st.info("Paste klines data above to preview ML signal.")
        except Exception as e:
            st.error(f"ML strategy not available: {e}")

    with tabs[4]:
        st.header("💓 Bot Health & Connection")
        st.write("- Bot running status: ", "🟢 Running" if controller.is_running() else "🔴 Stopped")
        if os.path.exists("logs/console_output.log"):
            with open("logs/console_output.log", "r", encoding="utf-8") as f:
                last_lines = f.readlines()[-10:]
            heartbeat_found = any("heartbeat" in l.lower() for l in last_lines)
            st.write("Last 10 log lines:")
            st.code("\n".join(last_lines))
            if heartbeat_found:
                st.success("Bot heartbeat detected ✅")
            else:
                st.warning("No recent heartbeat detected ⚠️")
        else:
            st.warning("Log file not found.")
        st.info("If health info is missing, check your bot and log file paths.")

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
