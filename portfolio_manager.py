import os
from datetime import datetime
from typing import Dict, Any

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None  # type: ignore

class PortfolioManager:
    def __init__(self, api_key: str | None = None, api_secret: str | None = None, use_testnet: bool = False):
        self._live = BINANCE_AVAILABLE and api_key and api_secret
        self._client = None
        if self._live:
            self._client = Client(api_key, api_secret)
            if use_testnet:
                self._client.API_URL = "https://testnet.binance.vision/api"

    def get_portfolio(self) -> Dict[str, Dict[str, Any]]:
        if self._live and self._client:
            try:
                return self._fetch_live_portfolio()
            except Exception:
                pass
        return self._mock_portfolio()

    def _fetch_live_portfolio(self) -> Dict[str, Dict[str, Any]]:
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

    def _mock_portfolio(self) -> Dict[str, Dict[str, Any]]:
        return {
            "USDT": {"balance": 1000.0, "price": 1.0, "value": 1000.0, "change": 0.0},
            "BTC": {"balance": 0.01, "price": 45000.0, "value": 450.0, "change": 2.5},
            "ETH": {"balance": 0.2, "price": 3000.0, "value": 600.0, "change": -1.2},
            "BNB": {"balance": 1.5, "price": 300.0, "value": 450.0, "change": 0.8},
        }

    def total_value(self) -> float:
        return sum(v["value"] for v in self.get_portfolio().values())

    def last_updated(self) -> str:
        return datetime.now().isoformat()