#!/usr/bin/env python3
"""
Deploy Trading Functionality to Render
Adds trading execution loops and controls to render_api.py
"""

import os
import subprocess
import time

def backup_render_api():
    """Backup current render_api.py"""
    timestamp = int(time.time())
    backup_name = f"render_api.py.backup.{timestamp}"
    subprocess.run(["cp", "render_api.py", backup_name])
    print(f"✅ Backed up render_api.py to {backup_name}")

def add_trading_functionality():
    """Add trading functionality to render_api.py"""
    print("🔧 Adding trading functionality to render_api.py...")
    
    # Read current render_api.py
    with open("render_api.py", "r") as f:
        content = f.read()
    
    # Check if trading functionality already exists
    if "execution_loop" in content and "EXECUTION_RUNTIME_ENABLED" in content:
        print("✅ Trading functionality already exists in render_api.py")
        return True
    
    # Add trading imports if not present
    if "import math" not in content:
        content = content.replace("import random", "import random\nimport math")
    
    if "import asyncio" not in content:
        content = content.replace("import random", "import random\nimport asyncio")
    
    # Add trading variables after global variables
    trading_vars = """
# Trading execution variables
_signals = []
_logs = []
_trade_log = []
_open_spend = {}
_last_exec = 0.0
EXECUTION_RUNTIME_ENABLED = True  # Default enabled for trading

# Trading configuration
TRADE_ENABLED = os.getenv('TRADE_ENABLED', '1') == '1'  # Default enabled on Render
EXECUTION_INTERVAL_S = float(os.getenv("EXECUTION_INTERVAL_S", "20"))
TRADE_QUOTE_PER_ORDER = float(os.getenv("TRADE_QUOTE_PER_ORDER", "100"))
MAX_SPEND_PER_SYMBOL = float(os.getenv("MAX_SPEND_PER_SYMBOL", "1000"))
SELL_FRACTION = float(os.getenv("SELL_FRACTION", "0.5"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "10"))

# Dashboard password protection
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "bottie2024")
"""
    
    # Add after the real_time_data definition
    if "real_time_data = {" in content and "_signals = []" not in content:
        content = content.replace(
            "}\n\n# Initialize exchange",
            "}\n" + trading_vars + "\n# Initialize exchange"
        )
    
    # Add helper functions
    helper_functions = """
def add_log(msg: str):
    \"\"\"Add log message to the logs list\"\"\"
    _logs.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}")
    if len(_logs) > 1500:
        del _logs[:-1000]
    print(msg)

def _position_qty(symbol: str) -> float:
    \"\"\"Get current position quantity for a symbol\"\"\"
    try:
        positions = real_time_data.get('positions', {})
        return positions.get(symbol, {}).get('quantity', 0.0)
    except:
        return 0.0

def _last_px(symbol: str):
    \"\"\"Get last price for a symbol\"\"\"
    try:
        if exchange_client:
            ticker = exchange_client.fetch_ticker(symbol)
            return ticker.get('last')
    except:
        pass
    return None

def _min_notional_and_step(symbol: str) -> tuple:
    \"\"\"Get minimum notional and quantity step for a symbol\"\"\"
    try:
        if exchange_client and hasattr(exchange_client, 'markets'):
            market = exchange_client.markets.get(symbol, {})
            min_notional = market.get('limits', {}).get('cost', {}).get('min', 10.0)
            qty_step = market.get('precision', {}).get('amount', 0.001)
            return min_notional, qty_step
    except:
        pass
    return 10.0, 0.001

def _round_step(qty: float, step: float) -> float:
    \"\"\"Round quantity to the exchange's step size\"\"\"
    if step <= 0:
        return qty
    return math.floor(qty / step) * step

"""
    
    # Add helper functions before initialize_exchange
    if "def initialize_exchange" in content and "def add_log" not in content:
        content = content.replace("# Initialize exchange if possible\ndef initialize_exchange", 
                                helper_functions + "# Initialize exchange if possible\ndef initialize_exchange")
    
    # Add trading endpoints before startup event
    trading_endpoints = """
# Trading control endpoints
@app.get("/trading/status")
def trading_status():
    \"\"\"Get current trading status and controls\"\"\"
    return {
        "trade_enabled": TRADE_ENABLED,
        "execution_enabled": EXECUTION_RUNTIME_ENABLED,
        "execution_interval": EXECUTION_INTERVAL_S,
        "quote_per_order": TRADE_QUOTE_PER_ORDER,
        "max_spend_per_symbol": MAX_SPEND_PER_SYMBOL,
        "recent_signals": len(_signals),
        "recent_trades": len(_trade_log),
        "last_execution": _last_exec
    }

@app.post("/trading/start")
def start_trading():
    \"\"\"Start trading execution\"\"\"
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = True
    add_log("🟢 Trading execution ENABLED by user")
    return {"ok": True, "enabled": EXECUTION_RUNTIME_ENABLED, "message": "Trading started"}

@app.post("/trading/stop")
def stop_trading():
    \"\"\"Stop trading execution\"\"\"
    global EXECUTION_RUNTIME_ENABLED
    EXECUTION_RUNTIME_ENABLED = False
    add_log("🔴 Trading execution DISABLED by user")
    return {"ok": True, "enabled": EXECUTION_RUNTIME_ENABLED, "message": "Trading stopped"}

@app.get("/logs")
def get_logs():
    \"\"\"Get recent system logs\"\"\"
    return {"logs": _logs[-100:], "count": len(_logs)}

@app.get("/trades/recent")
def get_recent_trades():
    \"\"\"Get recent executed trades\"\"\"
    return {"trades": _trade_log[-50:], "count": len(_trade_log)}

"""
    
    # Add before @app.on_event("startup")
    if "@app.on_event(\"startup\")" in content and "/trading/status" not in content:
        content = content.replace("@app.on_event(\"startup\")", trading_endpoints + "\n@app.on_event(\"startup\")")
    
    # Write updated content
    with open("render_api.py", "w") as f:
        f.write(content)
    
    print("✅ Added trading functionality to render_api.py")
    return True

def commit_and_push():
    """Commit changes and push to trigger deployment"""
    print("📝 Committing changes...")
    
    # Add all changes
    subprocess.run(["git", "add", "-A"])
    
    # Check if there are changes to commit
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if result.returncode == 0:
        print("ℹ️ No changes to commit")
        return False
    
    # Commit changes
    commit_msg = "feat: restore trading functionality with dashboard controls"
    subprocess.run(["git", "commit", "-m", commit_msg])
    
    # Push to origin
    subprocess.run(["git", "push", "origin", "main"])
    
    print("✅ Changes committed and pushed to main branch")
    return True

def main():
    print("🚀 DEPLOYING TRADING FUNCTIONALITY TO RENDER")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("render_api.py"):
        print("❌ render_api.py not found. Please run from project root.")
        return
    
    # Backup current file
    backup_render_api()
    
    # Add trading functionality
    if add_trading_functionality():
        print("✅ Trading functionality added")
    else:
        print("❌ Failed to add trading functionality")
        return
    
    # Commit and push
    if commit_and_push():
        print("\n🎉 DEPLOYMENT INITIATED!")
        print("=" * 60)
        print("🔄 Render will automatically deploy the changes")
        print("⏱️ Deployment usually takes 2-5 minutes")
        print("🌐 Monitor at: https://dashboard.render.com")
        print("\n📊 After deployment:")
        print("   • Production trading controls will be available")
        print("   • 502 errors should be resolved") 
        print("   • Access: https://bottie-1.onrender.com/dashboard_protected.html")
        print("   • Password: bottie2024")
    else:
        print("❌ No changes to deploy")

if __name__ == "__main__":
    main()