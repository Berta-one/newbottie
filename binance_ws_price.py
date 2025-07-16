import json
import threading
import websocket

class BinancePriceWebSocket:
    def __init__(self, symbols, on_price_update):
        self.symbols = [s.lower() for s in symbols]
        self.on_price_update = on_price_update
        self.ws = None
        self.thread = None
        self.running = False

    def _get_stream_url(self):
        streams = "/".join([f"{symbol}@ticker" for symbol in self.symbols])
        return f"wss://stream.binance.com:9443/stream?streams={streams}"

    def _on_message(self, ws, message):
        data = json.loads(message)
        if 'data' in data and 's' in data['data'] and 'c' in data['data']:
            symbol = data['data']['s']
            price = float(data['data']['c'])
            self.on_price_update(symbol, price)

    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        print("WebSocket closed")

    def _on_open(self, ws):
        print("WebSocket connection opened")

    def start(self):
        self.running = True
        url = self._get_stream_url()
        self.ws = websocket.WebSocketApp(
            url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join()
