from __future__ import annotations

import random
from datetime import datetime
from typing import List, Dict, Any

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None  # type: ignore

# Local import only when Binance is present to avoid heavy dependencies during unit-tests
if BINANCE_AVAILABLE:
    from multi_pair_scanner import CryptoPairScanner  # pragma: no cover

__all__ = ["MarketAnalyzer"]


class MarketAnalyzer:
    """Thin abstraction over multi_pair_scanner.CryptoPairScanner.

    The class gracefully degrades to pseudo-random mock data when Binance
    credentials are missing. This keeps the dashboard functional in demo
    mode while still allowing full-featured scanning in production.
    """

    def __init__(self, client: Client | None = None):  # type: ignore[name-defined]
        self._live = BINANCE_AVAILABLE and client is not None
        self._scanner = CryptoPairScanner(client) if self._live else None  # pragma: no cover

    # ------------------------------------------------------------------
    # Public API consumed by the Streamlit dashboard
    # ------------------------------------------------------------------
    def scan_market(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return structured scan results ordered by confidence/score."""
        if self._live and self._scanner:
            # In live mode we offload heavy lifting to the scanner – this can be
            # extended to run in a background thread/pool for responsiveness.
            pairs = self._scanner.get_selected_pairs()
            opportunities = self._scanner.scan_multiple_pairs(pairs[:limit])
            return opportunities
        # Fallback to mock results
        return self._mock_scan_results()

    # Convenience alias utilised by the legacy code path
    get_mock_scan_results = _mock_scan_results = lambda self: self._generate_mock()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _generate_mock(self, n: int = 5) -> List[Dict[str, Any]]:
        symbols = [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "ADAUSDT",
            "SOLUSDT",
        ]
        results = []
        for _ in range(n):
            symbol = random.choice(symbols)
            results.append(
                {
                    "symbol": symbol,
                    "signal": random.choice(["BUY", "SELL", "HOLD"]),
                    "price": random.uniform(100, 50000),
                    "change_24h": random.uniform(-10, 10),
                    "confidence": random.uniform(0.5, 0.9),
                    "volume_ratio": random.uniform(0.8, 2.5),
                    "timestamp": datetime.now(),
                }
            )
        return sorted(results, key=lambda x: x["confidence"], reverse=True)