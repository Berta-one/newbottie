class PositionMonitor:
    def __init__(self):
        self.positions = {}
        self.realized_pnl = 0.0

    def open_position(self, symbol, qty, price):
        self.positions[symbol] = {"qty": qty, "entry": price}

    def close_position(self, symbol, exit_price):
        if symbol not in self.positions:
            return 0.0
        pos = self.positions.pop(symbol)
        pnl = (exit_price - pos["entry"]) * pos["qty"]
        self.realized_pnl += pnl
        return pnl

    def get_active_positions(self):
        return self.positions

    def get_realized_pnl(self):
        return self.realized_pnl