import pandas as pd
import numpy as np
from binance.client import Client
from typing import List, Dict

class MarketAnalyzer:
    def __init__(self, client: Client):
        self.client = client

    def get_trading_pairs(self) -> List[str]:
        return [s["symbol"] for s in self.client.get_exchange_info()["symbols"] if s["quoteAsset"] == "USDT"]

    def get_price(self, symbol: str) -> float:
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

    def get_klines(self, symbol: str, interval="1h", limit=100):
        return self.client.get_klines(symbol=symbol, interval=interval, limit=limit)

    def compute_indicators(self, symbol: str) -> Dict[str, float]:
        klines = self.get_klines(symbol)
        df = pd.DataFrame(klines, columns=["time","open","high","low","close","volume","ct","qv","t","tb","tq","i"])
        df["close"] = df["close"].astype(float)

        close = df["close"]
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1])) if loss.iloc[-1] != 0 else 100

        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12.iloc[-1] - ema26.iloc[-1]

        # Bollinger Bands
        sma20 = close.rolling(20).mean().iloc[-1]
        std20 = close.rolling(20).std().iloc[-1]
        upper = sma20 + (2 * std20)
        lower = sma20 - (2 * std20)

        return {"rsi": rsi, "macd": macd, "bollinger_upper": upper, "bollinger_lower": lower}