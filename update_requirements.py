#!/usr/bin/env python3
"""
Update requirements.txt with missing dependencies
"""

import os
from pathlib import Path

def update_requirements():
    """Add missing dependencies to requirements.txt"""
    
    # Read current requirements
    req_file = Path("requirements.txt")
    if req_file.exists():
        with open(req_file, 'r') as f:
            current_requirements = f.read()
    else:
        current_requirements = ""
    
    # Missing dependencies found in your code
    missing_deps = [
        "psutil>=5.9.0",
        "streamlit>=1.28.0", 
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "python-binance>=1.0.19",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "pytest>=7.4.0",
        "plotly>=5.17.0",
        "pytz>=2024.1"
    ]
    
    # Check which dependencies are missing
    additions = []
    for dep in missing_deps:
        dep_name = dep.split(">=")[0].split("==")[0]
        if dep_name not in current_requirements:
            additions.append(dep)
    
    if additions:
        print(f"Adding {len(additions)} missing dependencies:")
        for dep in additions:
            print(f"  + {dep}")
        
        # Append missing dependencies
        with open(req_file, 'a') as f:
            f.write("\n# Auto-added missing dependencies\n")
            for dep in additions:
                f.write(f"{dep}\n")
        
        print(f"\n✅ Updated {req_file}")
    else:
        print("✅ All dependencies already present")
    
    # Show final requirements
    print(f"\n📋 Final requirements.txt:")
    with open(req_file, 'r') as f:
        print(f.read())

if __name__ == "__main__":
    update_requirements()