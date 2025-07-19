"""
risk_manager.py
========================
Provides dynamic risk checks and limits for the trading bot.
"""

from __future__ import annotations
from typing import Dict, Any


class RiskManager:
    def __init__(self, max_risk_percent: float = 0.02, max_positions: int = 5):
        """
        :param max_risk_percent: Max % of account equity per trade (default: 2%)
        :param max_positions: Max open positions at any time
        """
        self.max_risk_percent = max_risk_percent
        self.max_positions = max_positions

    # -------------------------------
    # Core Risk Checks
    # -------------------------------
    def validate_trade(self, symbol: str, qty: float, price: float, total_balance_usd: float, open_positions: int) -> Dict[str, Any]:
        """
        Validate trade against risk rules.
        """
        position_value = qty * price
        max_allowed = total_balance_usd * self.max_risk_percent

        if open_positions >= self.max_positions:
            return {"status": False, "reason": f"Max positions ({self.max_positions}) reached."}

        if position_value > max_allowed:
            return {"status": False, "reason": f"Position ${position_value:.2f} exceeds risk limit ${max_allowed:.2f}"}

        return {"status": True}

    # -------------------------------
    # Risk Summary for UI
    # -------------------------------
    def get_risk_summary(self) -> Dict[str, Any]:
        return {
            "max_risk_percent": self.max_risk_percent,
            "max_positions": self.max_positions
        }