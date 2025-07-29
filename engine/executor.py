# engine/executor.py

class TradeExecutor:
    def __init__(self, mode="paper"):
        self.mode = mode

    def execute(self, signal: str, symbol: str, price: float):
        if signal == "buy":
            print(f"🟢 BUY {symbol} at {price}")
        elif signal == "sell":
            print(f"🔴 SELL {symbol} at {price}")
        else:
            print(f"⚪ HOLD {symbol} at {price}")