"""
market_analyzer.py
========================
Handles technical analysis and signal generation for multiple pairs.
"""

from __future__ import annotations
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from binance.client import Client


class MarketAnalyzer:
    def __init__(self, client: Client, interval="1h", lookback=100):
        self.client = client
        self.interval = interval
        self.lookback = lookback

    # -------------------------------
    # Data Fetch
    # -------------------------------
    def _fetch_klines(self, symbol: str) -> pd.DataFrame:
        """Fetch historical candles from Binance."""
        candles = self.client.get_klines(symbol=symbol, interval=self.interval, limit=self.lookback)
        df = pd.DataFrame(candles, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "trades", "taker_base", "taker_quote", "ignore"
        ])
        df["close"] = df["close"].astype(float)
        return df

    # -------------------------------
    # Indicators
    # -------------------------------
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def calculate_momentum(self, prices: pd.Series, period: int = 10) -> float:
        return ((prices.iloc[-1] - prices.iloc[-period]) / prices.iloc[-period]) * 100

    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
        return prices.pct_change().rolling(window=period).std().iloc[-1]

    # -------------------------------
    # Public Methods for Dashboard
    # -------------------------------
    def get_latest_rsi(self, symbol: str) -> float:
        df = self._fetch_klines(symbol)
        return self.calculate_rsi(df["close"])

    def get_latest_momentum(self, symbol: str) -> float:
        df = self._fetch_klines(symbol)
        return self.calculate_momentum(df["close"])

    def get_volatility(self, symbol: str) -> float:
        df = self._fetch_klines(symbol)
        return self.calculate_volatility(df["close"])

    # -------------------------------
    # Market Scan
    # -------------------------------
    def scan_markets(self, pairs: List[str] = None) -> List[Dict[str, Any]]:
        """Scan all pairs and return signals."""
        if not pairs:
            pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

        signals = []
        for symbol in pairs:
            try:
                df = self._fetch_klines(symbol)
                rsi = self.calculate_rsi(df["close"])
                momentum = self.calculate_momentum(df["close"])
                volatility = self.calculate_volatility(df["close"])

                decision = "HOLD"
                if rsi < 30 and momentum > 0:
                    decision = "BUY"
                elif rsi > 70 and momentum < 0:
                    decision = "SELL"

                signals.append({
                    "symbol": symbol,
                    "rsi": round(rsi, 2),
                    "momentum": round(momentum, 2),
                    "volatility": round(volatility, 4),
                    "decision": decision
                })
            except Exception as e:
                signals.append({"symbol": symbol, "error": str(e)})

        return signals