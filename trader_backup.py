# 📁 main.py
import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv

from strategy import check_breakout_enhanced, get_strategy_confidence
from binance.client import Client

# ─── Load .env and Init ─────────────────────────────────────────────
load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
SIMULATED_TRADING = os.getenv("SIMULATED_TRADING", "False").lower() == "true"
TESTNET_URL = os.getenv("BINANCE_TESTNET_URL", "https://testnet.binance.vision/api")

TRADE_SYMBOL = "BTCUSDT"
BASE_TRADE_QTY = 0.001
RISK_PERCENTAGE = float(os.getenv("RISK_PERCENTAGE", "0.015"))

client = None
in_position = False
entry_price = None
trade_count = 0
total_pnl = 0.0
performance_log = []

# ─── Logger Setup ───────────────────────────────────────────────────
def setup_logger():
    os.makedirs("logs", exist_ok=True)
    try:
        sys.stdout = open("logs/console_output.log", "a", buffering=1, encoding="utf-8")
        sys.stderr = sys.stdout  # Optional: redirect stderr too
    except Exception as e:
        print(f"[Logging error] {e}")

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception as e:
        print(f"[Logging error] {e}")

# ─── Binance Init ───────────────────────────────────────────────────
def initialize_bot():
    global client
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = TESTNET_URL
        client.get_server_time()
        return True
    except Exception as e:
        safe_print("Error connecting to Binance:", e)
        return False

# ─── Main Bot Loop ──────────────────────────────────────────────────
def run_bot_loop(is_running_check):
    global in_position, entry_price
    while is_running_check():
        try:
            now = datetime.now()
            safe_print(f"[INFO] Running bot at {now}")

            # Simulated log entry (replace with real trade logic)
            log_entry = {
                "timestamp": now.isoformat(),
                "symbol": TRADE_SYMBOL,
                "pnl_percent": 1.5,
                "reason": "Breakout",
                "confidence": 0.92
            }

            with open("logs/single_pair_performance.json", "a", encoding="utf-8") as f:
                json.dump(log_entry, f)
                f.write("\n")

            time.sleep(10)

        except Exception as e:
            safe_print("[ERROR] Bot exception:", e)
            time.sleep(60)

def get_account_balance():
    """Return the current account balance. Placeholder implementation."""
    # TODO: Replace with actual API call to Binance or paper trading logic
    return {'BTC': 1.0, 'USDT': 1000.0}

# Calculate dynamic position size based on risk and balance
def calculate_dynamic_position_size(symbol=None, risk_percentage=None, balance=None):
    """
    Calculate position size based on risk percentage and account balance.
    Args:
        symbol (str): Trading symbol (e.g., 'BTCUSDT').
        risk_percentage (float): Fraction of account to risk per trade.
        balance (float): Account balance in USDT.
    Returns:
        float: Position size in base currency.
    """
    # Use .env or defaults if not provided
    if risk_percentage is None:
        import os
        risk_percentage = float(os.getenv("RISK_PERCENTAGE", "0.015"))
    if balance is None:
        balance = get_account_balance().get('USDT', 1000.0)
    # Example: risk USDT amount
    risk_amount = balance * risk_percentage
    # Placeholder: assume price is $30,000 for BTC
    price = 30000.0
    if symbol and symbol.upper().startswith('ETH'):
        price = 2000.0
    position_size = risk_amount / price
    return round(position_size, 6)
# ✅ Example usage (only run if script directly called)
# if __name__ == "__main__":
#     setup_logger()
#     if initialize_bot():
#         run_bot_loop(lambda: True)
def monitor_position_enhanced(client, symbol, entry_price):
    # Dummy exit condition for example purposes
    # In a real bot, this would include your exit logic
    current_price = float(client.get_symbol_ticker(symbol=symbol)["price"])
    threshold = 0.01 * entry_price  # Example: 1% threshold
    if abs(current_price - entry_price) > threshold:
        return True, "1% move from entry"
    return False, "Hold"

