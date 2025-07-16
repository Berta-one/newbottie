import websocket
import json
import threading

def on_message(ws, message):
    data = json.loads(message)
    print(f"Price update: {data}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    print("WebSocket connection opened")

def start_price_stream(symbol="btcusdt"):
    url = f"wss://stream.binance.com:9443/ws/{symbol}@trade"
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    print(f"Started WebSocket for {symbol} trades. Press Ctrl+C to exit.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        ws.close()

if __name__ == "__main__":
    start_price_stream("btcusdt")
