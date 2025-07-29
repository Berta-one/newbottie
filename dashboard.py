# Streamlit dashboard placeholder
# dashboard.py

import os
import subprocess

def launch_dashboard():
    port = os.getenv("DASHBOARD_PORT", "8501")
    subprocess.run([
        "streamlit", "run", "dashboard/app.py",
        "--server.port", port,
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false"
    ])

if __name__ == "__main__":
    launch_dashboard()