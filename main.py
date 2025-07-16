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
    import random
    start_time = time.time()
    log_console('Bot started.')
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT']
    while True:
        scan_count += 1
        # Heartbeat
        log_console(f'💓 Heartbeat {scan_count}')
        # Simulate price swings and opportunities
        scan_results = []
        for symbol in random.sample(symbols, k=4):
            price_change = round(random.uniform(-5, 7), 2)
            volume = round(random.uniform(1.0, 3.5), 2)
            confidence = round(random.uniform(0.5, 0.95), 2)
            signal = 'BUY_LONG' if price_change > 2 and confidence > 0.7 else 'HOLD'
            scan_results.append({
                'symbol': symbol,
                'change_pct': price_change,
                'volume': volume,
                'confidence': confidence,
                'signal': signal
            })
            # Log each opportunity
            if signal != 'HOLD':
                log_console(f"🚀 Opportunity: {symbol} {price_change:+.2f}% vol {volume}x conf {confidence:.2f} signal {signal}")
        # Log scan summary
        top_moves = ', '.join([f"{r['symbol']} {r['change_pct']:+.2f}%" for r in scan_results])
        log_scan(f"Scan {scan_count}: Top moves: {top_moves}")
        # Log all opportunities to scan log
        for r in scan_results:
            log_scan(f"{r['symbol']} | Δ%: {r['change_pct']:+.2f} | Vol: {r['volume']}x | Conf: {r['confidence']:.2f} | Signal: {r['signal']}")
        # Update status file
        update_status()
        time.sleep(SCAN_INTERVAL)
