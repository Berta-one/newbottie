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
    """
    PortfolioManager fetches live portfolio from Binance and provides
    USD and GBP valuations. Falls back to mock data if API fails.
    """

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, use_testnet: bool = False) -> None:
        self._live = BINANCE_AVAILABLE and api_key and api_secret
        self._client = None
        if self._live:
            self._client = Client(api_key, api_secret)
            if use_testnet:
                self._client.API_URL = "https://testnet.binance.vision/api"

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def get_portfolio(self) -> tuple[Dict[str, Dict[str, Any]], float, float]:
        """
        Returns:
            (portfolio_dict, total_usd_value, total_gbp_value)
        """
        if self._live and self._client:
            try:
                return self._fetch_live_portfolio()
            except Exception as e:
                print(f"[WARN] Live portfolio fetch failed: {e}")
        return self._mock_portfolio()

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------
    def _fetch_live_portfolio(self) -> tuple[Dict[str, Dict[str, Any]], float, float]:
        account = self._client.get_account()
        tickers = {t["symbol"]: float(t["price"]) for t in self._client.get_all_tickers()}

        # Get FX rates for USDGBP conversion
        gbp_usdt_price = tickers.get("GBPUSDT", 1.25)  # Approx fallback

        portfolio: Dict[str, Dict[str, Any]] = {}
        total_usd = 0.0

        for balance in account["balances"]:
            asset = balance["asset"]
            free = float(balance["free"] or 0)
            locked = float(balance["locked"] or 0)
            total = free + locked
            if total <= 0:
                continue

            # Get asset price in USD
            price = 1.0 if asset == "USDT" else None
            for variant in [f"{asset}USDT", f"{asset}BUSD", f"{asset}USDC"]:
                if variant in tickers:
                    price = tickers[variant]
                    break
            if price is None:
                continue

            usd_value = total * price
            total_usd += usd_value

            portfolio[asset] = {
                "balance": total,
                "price": price,
                "value": usd_value,
                "change": self._get_24h_change(f"{asset}USDT", tickers)
            }

        total_gbp = total_usd / gbp_usdt_price
        return portfolio, total_usd, total_gbp

    def _get_24h_change(self, symbol: str, tickers: dict) -> float:
        """Fetch 24h price change for a symbol (default 0.0 if not available)."""
        try:
            ticker_24h = self._client.get_ticker(symbol=symbol)
            return float(ticker_24h.get("priceChangePercent", 0.0))
        except:
            return 0.0

    def _mock_portfolio(self) -> tuple[Dict[str, Dict[str, Any]], float, float]:
        mock = {
            "USDT": {"balance": 1000.0, "price": 1.0, "value": 1000.0, "change": 0.0},
            "BTC": {"balance": 0.01, "price": 45000.0, "value": 450.0, "change": 2.5},
            "ETH": {"balance": 0.2, "price": 3000.0, "value": 600.0, "change": -1.2},
            "BNB": {"balance": 1.5, "price": 300.0, "value": 450.0, "change": 0.8},
        }
        total_usd = sum(v["value"] for v in mock.values())
        total_gbp = total_usd / 1.25  # approx
        return mock, total_usd, total_gbp

    def total_value(self) -> float:
        """Returns total portfolio USD value."""
        portfolio, total_usd, _ = self.get_portfolio()
        return total_usd

    def last_updated(self) -> str:
        return datetime.now().isoformat()