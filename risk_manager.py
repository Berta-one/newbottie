class RiskManager:
    def __init__(self, max_risk_percent: float = 0.02, max_positions: int = 5):
        self.max_risk_percent = max_risk_percent
        self.max_positions = max_positions

    def validate_trade(self, symbol, qty, price, total_balance_usd, open_positions):
        position_value = qty * price
        max_allowed = total_balance_usd * self.max_risk_percent

        if open_positions >= self.max_positions:
            return {"status": False, "reason": f"Max positions ({self.max_positions}) reached."}

        if position_value > max_allowed:
            return {"status": False, "reason": f"Position ${position_value:.2f} exceeds ${max_allowed:.2f}"}

        return {"status": True}

    def get_risk_summary(self):
        return {"max_risk_percent": self.max_risk_percent, "max_positions": self.max_positions}