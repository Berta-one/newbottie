# scripts/smoke.py
"""
Minimal end-to-end smoke test:
- uses in-memory bars (no CSV, no exchange)
- exercises ensemble -> signal generator -> execution manager -> portfolio
- runs in paper mode and exits 0 on success
"""

import logging
import time
from engine.integrated_portfolio_engine import IntegratedPortfolioEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("SMOKE")


def main():
    symbols = ["BTC/USDT", "ETH/USDT"]
    eng = IntegratedPortfolioEngine(symbols=symbols, initial_capital=10_000.0)

    # 20 synthetic bars alternating between symbols
    bars = []
    px_btc = 50000.0
    px_eth = 3000.0
    for i in range(20):
        if i % 2 == 0:
            px_btc *= (1.0 + (0.001 if i % 4 == 0 else -0.0005))
            bars.append({"symbol": "BTC/USDT", "close": px_btc, "high": px_btc * 1.001, "low": px_btc * 0.999, "volume": 10_000})
        else:
            px_eth *= (1.0 + (0.0012 if i % 3 == 0 else -0.0006))
            bars.append({"symbol": "ETH/USDT", "close": px_eth, "high": px_eth * 1.001, "low": px_eth * 0.999, "volume": 5_000})

    for b in bars:
        eng.on_bar(b)
        time.sleep(0.02)  # tiny delay so cooldown logic has a chance to run

    log.info("Smoke test completed without exceptions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())