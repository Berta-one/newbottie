# scripts/verify_trades.py
"""
Verify live Binance trades and flag entries that appear to come from
the Binance testnet.

The script connects to the Binance REST API using `ccxt` and the API
credentials stored in the environment variables `BINANCE_API_KEY` and
`BINANCE_API_SECRET`.  It then fetches trade history for each symbol
listed in the `TRADE_SYMBOLS` environment variable.

For each trade returned by :func:`fetch_my_trades`, the ``id`` and the
``info.isIsolated`` fields are compared.  Real spot trades normally do
not include the ``isIsolated`` flag, whereas certain simulated/testnet
trades do.  The presence of that flag therefore acts as a heuristic to
identify testnet activity.

Usage::

    export BINANCE_API_KEY=...  # required
    export BINANCE_API_SECRET=...  # required
    export TRADE_SYMBOLS="BTC/USDT,ETH/USDT"  # comma separated
    python scripts/verify_trades.py
"""

from __future__ import annotations

import os
from typing import List

try:
    import ccxt  # type: ignore
except Exception as exc:  # pragma: no cover - import guard
    raise RuntimeError(f"ccxt required: {exc}")


API_KEY_ENV = "BINANCE_API_KEY"
API_SECRET_ENV = "BINANCE_API_SECRET"


def _get_symbols() -> List[str]:
    env = os.getenv("TRADE_SYMBOLS", "")
    return [s.strip().upper() for s in env.split(",") if s.strip()]


def main() -> int:
    api_key = os.getenv(API_KEY_ENV)
    api_secret = os.getenv(API_SECRET_ENV)
    if not api_key or not api_secret:
        print("[verify] BINANCE_API_KEY/BINANCE_API_SECRET must be set.")
        return 1

    symbols = _get_symbols()
    if not symbols:
        print("[verify] TRADE_SYMBOLS is empty; nothing to check.")
        return 0

    ex = ccxt.binance({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
    })
    try:
        ex.load_markets()
    except Exception as exc:
        print(f"[verify] Failed to load markets: {exc}")
        return 2

    testnet_found = False
    for sym in symbols:
        try:
            trades = ex.fetch_my_trades(sym)
        except Exception as exc:
            print(f"[verify] fetch_my_trades failed for {sym}: {exc}")
            continue

        for tr in trades:
            trade_id = tr.get("id")
            is_isolated = tr.get("info", {}).get("isIsolated")
            print(f"{sym} trade id={trade_id} isIsolated={is_isolated}")
            if is_isolated not in (None, "FALSE", False):
                testnet_found = True

    if testnet_found:
        print("[verify] Possible testnet trades detected.")
        return 3

    print("[verify] No testnet trade entries detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
