class TradeExecutor:
    def __init__(self, mode="paper"):
        self.mode = mode

    def execute(self, symbol, signal, size):
        print(f"[EXECUTOR] {self.mode.upper()} TRADE -> {signal.upper()} {symbol} with size {size}")
