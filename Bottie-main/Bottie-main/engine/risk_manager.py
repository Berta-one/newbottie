class RiskManager:
    def __init__(self, max_drawdown=0.2):
        self.max_drawdown = max_drawdown
        self.equity_peak = 100000
        self.equity = 100000

    def check_risk(self, pnl):
        self.equity += pnl
        if self.equity > self.equity_peak:
            self.equity_peak = self.equity
        drawdown = 1 - self.equity / self.equity_peak
        return drawdown < self.max_drawdown
