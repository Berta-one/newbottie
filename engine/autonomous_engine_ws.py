# engine/autonomous_engine_ws.py

import asyncio
import json
from engine.decision_engine import DecisionEngine
from engine.executor import TradeExecutor
from engine.risk_manager import RiskManager
from ccxt.async_support import binance

class AutonomousEngine:
    def __init__(self, api_key, secret, symbol="BTC/USDT"):
        self.exchange = binance({
            "apiKey": api_key,
            "secret": secret,
            "enableRateLimit": True
        })
        self.symbol = symbol
        self.engine = DecisionEngine()
        self.executor = TradeExecutor()
        self.risk_manager = RiskManager()

    async def fetch_data(self):
        ohlcv = await self.exchange.fetch_ohlcv(self.symbol, timeframe="1m", limit=100)
        closes = [x[4] for x in ohlcv]
        return closes

    async def run(self):
        while True:
            data = await self.fetch_data()
            market_data = {
                "price": data[-1],
                "return_1h": (data[-1] - data[-60]) / data[-60],
                "return_24h": (data[-1] - data[0]) / data[0],
                "volatility": max(data[-10:]) - min(data[-10:]),
                "rsi": 50,  # TODO: plug real RSI
                "sentiment": 0.1  # TODO: plug real sentiment
            }

            signal = self.engine.generate_signal(market_data)
            if self.risk_manager.should_trade():
                self.executor.execute(signal, self.symbol, market_data["price"])
            await asyncio.sleep(60)