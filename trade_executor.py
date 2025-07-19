class TradeExecutor:
    def __init__(self, client, risk_mgr):
        self.client = client
        self.risk_mgr = risk_mgr

    def manual_trade(self, symbol: str, qty: float, side: str):
        return f"Manual Trade: {side} {qty} {symbol} executed."

    def auto_execute(self, signal):
        return f"Auto Trade executed for {signal['symbol']} based on signal."