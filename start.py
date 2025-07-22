#!/usr/bin/env python3
import os
import subprocess
import sys

# Get PORT from environment
port = os.environ.get('PORT', '8080')
print(f"Starting Streamlit on port {port}")

# Clear problematic environment variables
if 'STREAMLIT_SERVER_PORT' in os.environ:
   del os.environ['STREAMLIT_SERVER_PORT']

# Start streamlit with explicit port
cmd = [
   sys.executable, '-m', 'streamlit', 'run', 'app_minimal.py',
   '--server.address', '0.0.0.0',
   '--server.port', port,
   '--server.headless', 'true'
]

subprocess.run(cmd)
