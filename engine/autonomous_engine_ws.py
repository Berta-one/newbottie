# engine/autonomous_engine_ws.py

import asyncio
import json
import websockets
from engine.trading_core import TradingEngine
from utils.logger import get_logger

logger = get_logger(__name__)

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"

class WebSocketEngine:
    def __init__(self, symbol="BTCUSDT", interval="1m"):
        self.symbol = symbol.lower()
        self.interval = interval
        self.engine = TradingEngine()

    async def listen(self):
        ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@kline_{self.interval}"
        async with websockets.connect(ws_url) as websocket:
            logger.info("WebSocket connected.")
            while True:
                try:
                    data = await websocket.recv()
                    kline = json.loads(data).get("k")
                    if kline and kline['x']:  # Candle is closed
                        price_info = {
                            'timestamp': kline['t'],
                            'open': float(kline['o']),
                            'high': float(kline['h']),
                            'low': float(kline['l']),
                            'close': float(kline['c']),
                            'volume': float(kline['v']),
                        }
                        logger.info(f"Received closed candle: {price_info}")
                        self.engine.process_price(price_info)
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                    await asyncio.sleep(5)

if __name__ == "__main__":
    ws = WebSocketEngine()
    asyncio.run(ws.listen())