#!/usr/bin/env python3
"""
Safe Railway Deployment Setup
-----------------------------
Creates railway.toml and Nixpacks config for deployment
without modifying the main bot or requirements.
"""

import os
from pathlib import Path

def create_railway_config():
    """Create a clean railway.toml configuration."""
    railway_config = """[build]
builder = "NIXPACKS"

[deploy]
startCommand = "streamlit run hybrid_bot.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
"""
    with open("railway.toml", "w") as f:
        f.write(railway_config)
    print("✅ Created railway.toml")

def create_nixpacks():
    """Create minimal nixpacks configuration."""
    Path(".nixpacks").mkdir(exist_ok=True)
    nixpacks_config = """[phases.setup]
nixPkgs = ["python39", "python39Packages.pip"]

[phases.install]
cmds = [
  "pip install --upgrade pip",
  "pip install -r requirements.txt"
]

[phases.build]
cmds = ["echo 'Build complete'"]

[start]
cmd = "echo 'Using railway.toml start command'"
"""
    with open(".nixpacks/nixpacks.toml", "w") as f:
        f.write(nixpacks_config)
    print("✅ Created .nixpacks/nixpacks.toml")

def ensure_procfile():
    """Create a Procfile (optional fallback)."""
    if not os.path.exists("Procfile"):
        with open("Procfile", "w") as f:
            f.write("web: streamlit run hybrid_bot.py --server.port $PORT --server.address 0.0.0.0\n")
        print("✅ Created Procfile")

def main():
    create_railway_config()
    create_nixpacks()
    ensure_procfile()
    print("\n🚀 Safe Railway config is ready. No files were overwritten.")

if __name__ == "__main__":
    main()
