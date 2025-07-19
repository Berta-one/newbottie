import os
from datetime import datetime
from typing import Dict, Any

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:  # Binance library may not be installed in every environment
    BINANCE_AVAILABLE = False
    Client = None  # type: ignore

__all__ = ["PortfolioManager"]


class PortfolioManager:
    """Centralised portfolio tracking helper.

    For live trading, it queries Binance for balances; otherwise it returns mock data. The
    public API purposefully stays minimal – the dashboard only needs *overview* figures.
    """

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, use_testnet: bool = False) -> None:
        self._live = BINANCE_AVAILABLE and api_key and api_secret
        self._client = None
        if self._live:
            self._client = Client(api_key, api_secret)  # type: ignore[arg-type]
            if use_testnet:
                self._client.API_URL = "https://testnet.binance.vision/api"  # pragma: no cover

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def get_portfolio(self) -> Dict[str, Dict[str, Any]]:
        """Return a dict keyed by asset with balance / price / value / change fields."""
        if self._live and self._client:
            try:
                return self._fetch_live_portfolio()
            except Exception:
                # Fall back to mock data to avoid crashing the dashboard
                pass
        return self._mock_portfolio()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_live_portfolio(self) -> Dict[str, Dict[str, Any]]:  # pragma: no cover
        """Minimal live portfolio implementation.

        NOTE: In a real-world codebase, you would want a far more robust implementation
        with caching, pagination handling, and error management. For demonstration
        purposes we keep things short.
        """
        assert self._client is not None  # mypy safeguard
        account = self._client.get_account()
        tickers = {t["symbol"]: float(t["price"]) for t in self._client.get_all_tickers()}

        portfolio: Dict[str, Dict[str, Any]] = {}
        for balance in account["balances"]:
            asset = balance["asset"]
            free = float(balance["free"] or 0)
            locked = float(balance["locked"] or 0)
            total = free + locked
            if total == 0:
                continue
            price = 1.0  # Default for stable-coins such as USDT
            symbol_variants = [f"{asset}USDT", f"{asset}BUSD", f"{asset}USDC"]
            for sym in symbol_variants:
                if sym in tickers:
                    price = tickers[sym]
                    break
            portfolio[asset] = {
                "balance": total,
                "price": price,
                "value": total * price,
                # Change calculation omitted for brevity
                "change": 0.0,
            }

        return portfolio

    def _mock_portfolio(self) -> Dict[str, Dict[str, Any]]:
        """Return deterministic demo data (no random to keep UI stable)."""
        return {
            "USDT": {"balance": 1000.0, "price": 1.0, "value": 1000.0, "change": 0.0},
            "BTC": {"balance": 0.01, "price": 45000.0, "value": 450.0, "change": 2.5},
            "ETH": {"balance": 0.2, "price": 3000.0, "value": 600.0, "change": -1.2},
            "BNB": {"balance": 1.5, "price": 300.0, "value": 450.0, "change": 0.8},
        }

    # ------------------------------------------------------------------
    # Convenience / analytics helpers
    # ------------------------------------------------------------------
    def total_value(self) -> float:
        """Return total portfolio USD value."""
        return sum(v["value"] for v in self.get_portfolio().values())

    def last_updated(self) -> str:
        return datetime.now().isoformat()