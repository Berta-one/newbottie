#!/usr/bin/env python3
"""
Headless runner for Bottie.
- No UI, no exchange needed to start.
- Feeds synthetic bars into the engine so the bot wiring can be validated.
- When you’re ready, replace the synthetic loop with your real WS/market feed.
"""

import os
import time
import logging
from typing import Dict, Any, List

# Import your engine
from engine.integrated_portfolio_engine import IntegratedPortfolioEngine

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("HeadlessRunner")


def generate_synthetic_bars(symbols: List[str], px: Dict[str, float]) -> List[Dict[str, Any]]:
    """Create a tiny set of synthetic bars for each symbol."""
    bars = []
    for s in symbols:
        drift = 0.0005 if (time.time() % 9) < 4.5 else -0.0004
        px[s] *= (1.0 + drift)
        close = px[s]
        bars.append({
            "symbol": s,
            "close": close,
            "high": close * 1.001,
            "low": close * 0.999,
            "volume": 10_000
        })
    return bars


def main():
    # Symbols to run (comma-separated env, default two majors)
    symbols = os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT").split(",")
    symbols = [s.strip() for s in symbols if s.strip()]
    if not symbols:
        symbols = ["BTC/USDT", "ETH/USDT"]

    initial_capital = float(os.getenv("EQUITY_START", "10000"))
    loop_sleep_s = float(os.getenv("LOOP_SLEEP_S", "1.0"))

    # Seed synthetic prices
    px = {s: (50000.0 if "BTC" in s.upper() else 3000.0) for s in symbols}

    log.info("Starting headless Bottie | symbols=%s | capital=%.2f", symbols, initial_capital)
    engine = IntegratedPortfolioEngine(symbols=symbols, initial_capital=initial_capital)

    try:
        while True:
            bars = generate_synthetic_bars(symbols, px)
            for b in bars:
                engine.on_bar(b)
            time.sleep(loop_sleep_s)
    except KeyboardInterrupt:
        log.info("Stopped by user")
    except Exception as exc:
        log.exception("Headless bot crashed: %s", exc)
        raise


if __name__ == "__main__":
    main()