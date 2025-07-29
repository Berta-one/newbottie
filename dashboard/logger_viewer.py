import streamlit as st
import os

def show_logs(log_path="logs/bot.log"):
    st.subheader("📜 Bot Logs")
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            lines = f.readlines()[-100:]  # Last 100 lines
            for line in lines:
                st.text(line.strip())
    else:
        st.warning("Log file not found.")
