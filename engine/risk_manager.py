# engine/risk_manager.py

import time

class RiskManager:
    def __init__(self, cooldown_period=300):
        self.last_trade_time = 0
        self.cooldown_period = cooldown_period

    def should_trade(self) -> bool:
        now = time.time()
        if now - self.last_trade_time > self.cooldown_period:
            self.last_trade_time = now
            return True
        return False