#!/usr/bin/env python3
"""
App starter to fix Railway port issues
"""

import os
import subprocess
import sys

def main():
    # Remove the problematic environment variable
    if 'STREAMLIT_SERVER_PORT' in os.environ:
        del os.environ['STREAMLIT_SERVER_PORT']
    
    # Get the port from Railway
    port = os.environ.get('PORT', '8501')
    
    # Start Streamlit
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'hybrid_bot.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true'
    ]
    
    print(f"Starting Streamlit on port {port}")
    subprocess.run(cmd)

if __name__ == "__main__":
    main()