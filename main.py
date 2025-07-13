# 📁 main.py

import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from binance.client import Client

from strategy import check_breakout_enhanced, get_strategy_confidence
from trader import monitor_position_enhanced

# ─── Load Environment Variables ─────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
TESTNET_URL = os.getenv("BINANCE_TESTNET_URL", "https://testnet.binance.vision/api")
RISK_PERCENTAGE = float(os.getenv("RISK_PERCENTAGE", "0.015"))

# ─── Trading Parameters ─────────────────────────────────────────────
TRADE_SYMBOL = "BTCUSDT"
BASE_TRADE_QTY = 0.001

# ─── Log Setup ──────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
sys.stdout = open("logs/console_output.log", "a", buffering=1, encoding="utf-8")

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception as e:
        print(f"[Logging Error] {e}")

# ─── Binance Client Initialization ──────────────────────────────────
client = None

def initialize_bot():
    global client
    try:
        client = Client(API_KEY, API_SECRET)
        if USE_TESTNET:
            client.API_URL = TESTNET_URL
        # Test connection
        client.get_server_time()
        return True
    except Exception as e:
        safe_print("❌ Error connecting to Binance:", e)
        return False

# ─── Trade State ────────────────────────────────────────────────────
in_position = False
entry_price = None

# ─── Bot Loop ───────────────────────────────────────────────────────
def run_bot_loop(is_running_check):
    global in_position, entry_price

    while is_running_check():
        try:
            now = datetime.now()
            safe_print(f"\n🔄 Running bot at {now.strftime('%Y-%m-%d %H:%M:%S')}")

            # Fetch market data
            klines = client.get_klines(symbol=TRADE_SYMBOL, interval="5m", limit=120)
            if not klines:
                safe_print("⚠️ No kline data retrieved. Retrying...")
                time.sleep(30)
                continue

            # Apply strategy
            signal = check_breakout_enhanced(klines)
            confidence = get_strategy_confidence(klines)
            current_price = float(klines[-1][4])

            # Entry logic
            if not in_position and signal in ["BUY_LONG", "BUY_SHORT"]:
                entry_price = current_price
                in_position = True
                safe_print(f"📈 Entered simulated {signal} at {entry_price:.2f}")

            # Exit logic
            elif in_position:
                should_exit, reason = monitor_position_enhanced(client, TRADE_SYMBOL, entry_price)
                if should_exit:
                    exit_price = current_price
                    pnl_percent = ((exit_price - entry_price) / entry_price) * 100

                    safe_print(f"💰 Exiting trade at {exit_price:.2f}")
                    safe_print(f"📊 PnL: {pnl_percent:.2f}% | Reason: {reason}")

                    # Log trade
                    log_entry = {
                        "timestamp": now.isoformat(),
                        "symbol": TRADE_SYMBOL,
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "pnl_percent": round(pnl_percent, 2),
                        "reason": reason,
                        "confidence": round(confidence, 2),
                        "strategy_signal": signal
                    }
                    with open("logs/single_pair_performance.json", "a", encoding="utf-8") as f:
                        json.dump(log_entry, f)
                        f.write("\n")

                    # Reset
                    in_position = False
                    entry_price = None

            time.sleep(10)

        except Exception as e:
            safe_print("🚨 Bot error:", e)
            time.sleep(60)

# ─── Launch Bot ─────────────────────────────────────────────────────
if __name__ == "__main__":
    if initialize_bot():
        safe_print(f"✅ Bot initialized successfully (Testnet: {USE_TESTNET})")
        try:
            run_bot_loop(lambda: True)
        except KeyboardInterrupt:
            safe_print("🛑 Bot stopped manually.")
    else:
        safe_print("❌ Initialization failed. Check API credentials or network.")
