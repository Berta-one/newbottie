 -*- coding: utf-8 -*-
"""
Bottie Background Service (Railway Ready)
Author: Rondanini Publishing Ltd
"""

from flask_socketio import SocketIO
import logging
import os
import time
from hybrid_bot import AutoScanner, AutoTrader
from datetime import datetime

# âœ… Environment Variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 30))
TRADING_PAIRS = os.getenv("TRADING_PAIRS", "BTCUSDT,ETHUSDT").split(",")
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# âœ… Connect to SocketIO message queue
socketio = SocketIO(message_queue=REDIS_URL)

# âœ… Logging
logging.basicConfig(
    filename="bot_service.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def log_activity(message):
    logging.info(message)
    socketio.emit("log_update", {"log": message}, namespace="/logs")


def main():
    log_activity("ðŸš€ Bottie Background Service started.")
    scanner = AutoScanner(pairs=TRADING_PAIRS)
    trader = AutoTrader(api_key=API_KEY, api_secret=API_SECRET)

    while True:
        try:
            log_activity("ðŸ” Running market scan...")
            signals = scanner.run_scan()
            log_activity(f"Signals detected: {signals}")
            for signal in signals:
                log_activity(f"ðŸ“ˆ Processing trade signal: {signal}")
                result = trader.execute(signal)
                log_activity(f"âœ… Trade executed: {result}")
        except Exception as e:
            log_activity(f"âŒ Error in bot loop: {e}")
        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_activity("ðŸ›‘ Bottie Background Service stopped.")

