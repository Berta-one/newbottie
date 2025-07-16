import os
import time
import json
from datetime import datetime

LOG_DIR = 'logs'
CONSOLE_LOG = os.path.join(LOG_DIR, 'console_output.log')
SCAN_LOG = os.path.join(LOG_DIR, 'portfolio_scans.log')
STATUS_FILE = os.path.join(LOG_DIR, 'bot_status.json')

SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '60'))

os.makedirs(LOG_DIR, exist_ok=True)

scan_count = 0

def log_console(msg):
    with open(CONSOLE_LOG, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def log_scan(msg):
    with open(SCAN_LOG, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def update_status():
    status = {
        'timestamp': datetime.now().isoformat(),
        'running': True,
        'scan_count': scan_count,
        'opportunities': [],
        'portfolio': {},
        'uptime_seconds': int(time.time() - start_time),
        'heartbeat_count': scan_count,
        'last_heartbeat': datetime.now().isoformat(),
        'latest_strategy': os.getenv('DEFAULT_STRATEGY', 'Breakout'),
        'latest_risk_level': os.getenv('DEFAULT_RISK_PROFILE', 'Balanced')
    }
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

if __name__ == "__main__":
    start_time = time.time()
    log_console('Bot started.')
    while True:
        scan_count += 1
        # Heartbeat
        log_console(f'💓 Heartbeat {scan_count}')
        # Simulate a scan
        log_scan(f'Scan {scan_count}: No real scan logic implemented (heartbeat only)')
        # Update status file
        update_status()
        time.sleep(SCAN_INTERVAL)
