import os
from datetime import datetime
from typing import Dict, Any

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None  # type: ignore

__all__ = ["PortfolioManager"]

class PortfolioManager:
    """Centralised portfolio tracking helper."""

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, use_testnet: bool = False) -> None:
        self._live = BINANCE_AVAILABLE and api_key and api_secret
        self._client = None
        if self._live:
            self._client = Client(api_key, api_secret)  # type: ignore[arg-type]
            if use_testnet:
                self._client.API_URL = "https://testnet.binance.vision/api"

    def get_portfolio(self):
        """Return (portfolio_dict, total_usd, total_gbp)."""
        if self._live and self._client:
            try:
                portfolio = self._fetch_live_portfolio()
            except Exception:
                portfolio = self._mock_portfolio()
        else:
            portfolio = self._mock_portfolio()

        total_usd = sum(float(v.get("value", 0)) for v in portfolio.values())
        total_gbp = total_usd * 0.79  # Approx conversion
        return portfolio, float(total_usd), float(total_gbp)

    def _fetch_live_portfolio(self):
        assert self._client is not None
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
            price = 1.0
            for sym in [f"{asset}USDT", f"{asset}BUSD", f"{asset}USDC"]:
                if sym in tickers:
                    price = tickers[sym]
                    break
            portfolio[asset] = {
                "balance": total,
                "price": price,
                "value": total * price,
                "change": 0.0
            }
        return portfolio

    def _mock_portfolio(self):
        return {
            "USDT": {"balance": 1000.0, "price": 1.0, "value": 1000.0, "change": 0.0},
            "BTC": {"balance": 0.01, "price": 45000.0, "value": 450.0, "change": 2.5},
            "ETH": {"balance": 0.2, "price": 3000.0, "value": 600.0, "change": -1.2},
            "BNB": {"balance": 1.5, "price": 300.0, "value": 450.0, "change": 0.8},
        }

    def total_value(self) -> float:
        return sum(v["value"] for v in self.get_portfolio()[0].values())

    def last_updated(self) -> str:
        return datetime.now().isoformat()