"""
Bottie Background Service
Runs autoscanner and autotrading loops independently of Streamlit UI
Author: Rondanini Publishing Ltd
"""

import time
import logging
from datetime import datetime

# Import your existing logic
from hybrid_bot import AutoScanner, AutoTrader   # Adjust imports based on your repo structure
from config import TRADING_PAIRS, SCAN_INTERVAL, API_KEY, API_SECRET  # Example config

# ✅ Setup Logging
logging.basicConfig(
    filename="bot_service.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def main():
    logging.info("🚀 Bottie Background Service started.")
    
    # Initialize scanner and trader
    scanner = AutoScanner(pairs=TRADING_PAIRS)
    trader = AutoTrader(api_key=API_KEY, api_secret=API_SECRET)

    while True:
        try:
            # ✅ Scan markets
            logging.info("🔍 Running market scan...")
            signals = scanner.run_scan()
            logging.info(f"Signals detected: {signals}")

            # ✅ Execute trades
            for signal in signals:
                logging.info(f"📈 Processing trade signal: {signal}")
                result = trader.execute(signal)
                logging.info(f"✅ Trade executed: {result}")

        except Exception as e:
            logging.error(f"❌ Error in bot loop: {e}")

        # ✅ Sleep before next cycle
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("🛑 Bottie Background Service stopped by user.")