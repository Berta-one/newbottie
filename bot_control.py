import streamlit as st
import subprocess
import os
import time

st.title("🤖 Bottie Control Panel")

# Paths and commands
BOT_SCRIPT = "bot_service.py"  # Make sure this file is in your repo root

def is_bot_running():
    """Check if bot_service.py is running"""
    try:
        result = subprocess.run(["pgrep", "-f", BOT_SCRIPT], stdout=subprocess.PIPE)
        return bool(result.stdout)
    except:
        return False

# ✅ Status Indicator
if is_bot_running():
    st.success("✅ Bot is currently running in the background.")
else:
    st.warning("⚠️ Bot is not running.")

# ✅ Control Buttons
col1, col2 = st.columns(2)

with col1:
    if st.button("▶ Start Bot"):
        if not is_bot_running():
            os.system(f"nohup python {BOT_SCRIPT} &")
            st.success("✅ Bot started successfully!")
            time.sleep(2)
            st.experimental_rerun()
        else:
            st.info("Bot is already running.")

with col2:
    if st.button("⏹ Stop Bot"):
        if is_bot_running():
            os.system(f"pkill -f {BOT_SCRIPT}")
            st.warning("🛑 Bot stopped.")
            time.sleep(2)
            st.experimental_rerun()
        else:
            st.info("Bot is not running.")

# ✅ Show Recent Logs
st.subheader("📜 Recent Bot Logs")
try:
    with open("bot_service.log", "r") as log_file:
        logs = log_file.readlines()[-20:]  # Show last 20 lines
        st.text("".join(logs))
except FileNotFoundError:
    st.info("No logs available yet.")