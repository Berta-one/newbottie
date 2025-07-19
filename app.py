"""
app.py
========================
Legacy entry point for the bot.
Redirects to hybrid_bot.py (Streamlit dashboard) for UI.
Quantum-related initialization uses BasicAer for compatibility.
"""

import os
import subprocess

# Ensure environment variables for Streamlit
os.environ["STREAMLIT_SERVER_PORT"] = os.getenv("PORT", "8080")
os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"

def run_dashboard():
    """Start the main Streamlit dashboard."""
    subprocess.run(["streamlit", "run", "hybrid_bot.py"])

if __name__ == "__main__":
    run_dashboard()