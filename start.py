import os
import subprocess
import sys

# Get PORT from Railway environment
port = os.environ.get('PORT', '8080')
print(f"Railway PORT detected: {port}")

# Remove problematic environment variables
env = os.environ.copy()
env.pop('STREAMLIT_SERVER_PORT', None)

# Start Streamlit with correct port
cmd = [
   sys.executable, '-m', 'streamlit', 'run', 'app_minimal.py',
   '--server.address', '0.0.0.0',
   '--server.port', str(port),
   '--server.headless', 'true',
   '--server.enableCORS', 'false'
]

print(f"Executing: {' '.join(cmd)}")
subprocess.run(cmd, env=env)
