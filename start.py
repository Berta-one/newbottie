 -*- coding: utf-8 -*-
import os
import subprocess
import sys

# Railway provides PORT environment variable
port = os.environ.get("PORT")
if not port:
    port = "8080"
    print("Warning: PORT not set, using default 8080")
else:
    print(f"Railway PORT detected: {port}")

# Remove any problematic streamlit environment variables
env = os.environ.copy()
env.pop("STREAMLIT_SERVER_PORT", None)

# Start Streamlit with Railway's PORT
cmd = [
    sys.executable,
    "-m",
    "streamlit",
    "run",
    "app_minimal.py",
    "--server.address",
    "0.0.0.0",
    "--server.port",
    str(port),
    "--server.headless",
    "true",
    "--server.enableCORS",
    "false",
    "--server.enableXsrfProtection",
    "false",
]

print(f"Starting Streamlit with command: {' '.join(cmd)}")
print(f"Environment PORT: {port}")

try:
    subprocess.run(cmd, env=env, check=True)
except Exception as e:
    print(f"Error starting Streamlit: {e}")
    sys.exit(1)

