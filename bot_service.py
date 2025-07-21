"""
Bottie Background Service
Runs autoscanner and autotrading loops independently of Flask UI
Author: Rondanini Publishing Ltd
"""
from flask_socketio import SocketIO
import logging
import time
from datetime import datetime

# Import your existing logic
from hybrid_bot import AutoScanner, AutoTrader  # Adjust path if needed
from config import TRADING_PAIRS, SCAN_INTERVAL, API_KEY, API_SECRET  # Adjust path if needed

# ✅ Connect to SocketIO message queue (Flask app must run SocketIO with Redis)
socketio = SocketIO(message_queue='redis://')  # Redis must be running

# ✅ Setup Logging
logging.basicConfig(
    filename="bot_service.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def log_activity(message):
    """Write log to file and send via WebSocket"""
    logging.info(message)
    socketio.emit('log_update', {'log': message}, namespace='/logs')

def main():
    log_activity("🚀 Bottie Background Service started.")
    
    # Initialize scanner and trader
    scanner = AutoScanner(pairs=TRADING_PAIRS)
    trader = AutoTrader(api_key=API_KEY, api_secret=API_SECRET)

    while True:
        try:
            log_activity("🔍 Running market scan...")
            signals = scanner.run_scan()
            log_activity(f"Signals detected: {signals}")

            for signal in signals:
                log_activity(f"📈 Processing trade signal: {signal}")
                result = trader.execute(signal)
                log_activity(f"✅ Trade executed: {result}")

        except Exception as e:
            log_activity(f"❌ Error in bot loop: {e}")

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_activity("🛑 Bottie Background Service stopped by user.")