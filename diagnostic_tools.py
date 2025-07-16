# diagnostic_tools.py
# Place your BotDiagnostic class here (from Claude's code or your own)

# Example placeholder:
class BotDiagnostic:
    def run_full_diagnostic(self):
        print("(Full diagnostic would run here)")

import time
import random
import pandas as pd

class MockBinanceClient:
    def __init__(self):
        self.base_price = 65000
    def get_klines(self, symbol, interval, limit):
        klines = []
        current_price = self.base_price
        for i in range(limit):
            change = random.uniform(-0.01, 0.01)
            current_price *= (1 + change)
            klines.append([
                int(time.time()) * 1000,
                str(current_price),
                str(current_price * 1.001),
                str(current_price * 0.999),
                str(current_price),
                str(random.uniform(100, 1000)),
                0, 0, 0, 0, 0, 0
            ])
        return klines

def analyze_market(klines, threshold=2.0):
    if len(klines) < 120:
        return False, 0.0, "Not enough data"
    start_price = float(klines[0][4])
    current_price = float(klines[-1][4])
    change_pct = ((current_price - start_price) / start_price) * 100
    if abs(change_pct) >= threshold:
        return True, change_pct, "Breakout detected"
    else:
        return False, change_pct, "No breakout"

def run_diagnostic(symbols=None, threshold=2.0):
    if symbols is None:
        symbols = [
            "BTCUSDT", "ETHUSDT", "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT",
            "SOLUSDT", "AVAXUSDT", "LTCUSDT", "XRPUSDT", "BNBUSDT", "ADAUSDT",
            "MATICUSDT", "ARBUSDT", "OPUSDT", "SUIUSDT", "INJUSDT", "JUPUSDT"
        ]
    client = MockBinanceClient()
    print("\n=== Crypto Bot Diagnostic (Relaxed) ===\n")
    trade_count = 0
    for symbol in symbols:
        klines = client.get_klines(symbol, "1m", 120)
        signal, change_pct, reason = analyze_market(klines, threshold)
        print(f"Symbol: {symbol}")
        print(f"  2h Change: {change_pct:+.2f}%")
        print(f"  Signal: {'TRADE' if signal else 'NO TRADE'}")
        print(f"  Reason: {reason}\n")
        if signal:
            trade_count += 1
    print(f"Total trade opportunities: {trade_count} out of {len(symbols)} symbols.")
    print("Diagnostic complete. Adjust your strategy or thresholds for more trades.")
