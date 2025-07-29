# Autonomous engine full logic placeholder
# engine/autonomous_engine_ws.py

import asyncio
import json
import websockets
import time
import logging

from engine.decision_engine import DecisionEngine
from engine.executor import TradeExecutor
from engine.risk_manager import RiskManager
from ml.decision_engine import load_model_and_predict

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@miniTicker"

class AutonomousTradingEngine:
    def __init__(self, mode="paper"):
        self.executor = TradeExecutor(mode=mode)
        self.decision_engine = DecisionEngine()
        self.risk_manager = RiskManager(max_drawdown=0.1)
        self.price = None
        self.trade_cooldown = 60  # seconds between trades
        self.last_trade_time = 0

    async def listen(self):
        async with websockets.connect(BINANCE_WS_URL) as ws:
            print("[Live] Connected to Binance WebSocket")
            async for message in ws:
                await self.process_message(message)

    async def process_message(self, message):
        data = json.loads(message)
        self.price = float(data["c"])

        # Logging price for debugging
        logging.info(f"Price Update: {self.price}")

        if time.time() - self.last_trade_time < self.trade_cooldown:
            return  # Cooldown active

        market_features = {
            "price": self.price,
            "volatility": 0.03,  # Placeholder, should come from indicator engine
            "rsi": 45,
            "return_1h": 0.005,
            "return_24h": 0.04,
        }

        signal = self.decision_engine.generate_signal(market_features)
        if signal == "buy" or signal == "sell":
            if self.risk_manager.check_risk(signal):
                self.executor.execute_trade(signal, amount=0.01)
                self.last_trade_time = time.time()
                logging.info(f"Executed {signal} at {self.price}")

    def start(self):
        try:
            asyncio.run(self.listen())
        except KeyboardInterrupt:
            print("[Live] Terminated by user")
