"""
trade_executor.py
========================
Handles trade execution for manual and automated strategies.
"""

from __future__ import annotations
from typing import Dict, Any
from binance.client import Client
from position_monitor import PositionMonitor
from risk_manager import RiskManager


class TradeExecutor:
    def __init__(self, client: Client, risk_mgr: RiskManager):
        self.client = client
        self.risk_mgr = risk_mgr
        self.position_monitor = PositionMonitor()

    # -------------------------------
    # Manual Trade Execution
    # -------------------------------
    def manual_trade(self, symbol: str, qty: float, side: str) -> Dict[str, Any]:
        try:
            # Get account balance for risk validation
            account = self.client.get_account()
            total_balance_usd = sum(float(b["free"]) for b in account["balances"] if b["asset"] == "USDT")
            price = float(self.client.get_symbol_ticker(symbol=symbol)["price"])

            # Validate risk
            open_positions = len(self.position_monitor.get_active_positions())
            risk_check = self.risk_mgr.validate_trade(symbol, qty, price, total_balance_usd, open_positions)
            if not risk_check["status"]:
                return {"status": "FAILED", "reason": risk_check["reason"]}

            # Execute order
            if side.upper() == "BUY":
                order = self.client.order_market_buy(symbol=symbol, quantity=qty)
                self.position_monitor.add_position(symbol, {"qty": qty, "side": "BUY", "price": price})
            elif side.upper() == "SELL":
                order = self.client.order_market_sell(symbol=symbol, quantity=qty)
                self.position_monitor.remove_position(symbol)
            else:
                return {"status": "FAILED", "reason": f"Invalid side {side}"}

            return {"status": "SUCCESS", "orderId": order["orderId"], "symbol": symbol, "side": side}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}

    # -------------------------------
    # Auto-Trade Execution
    # -------------------------------
    def auto_execute(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        try:
            symbol = signal["symbol"]
            decision = signal["decision"]
            qty = 0.001  # Default minimal lot size (could be dynamic)

            if decision == "BUY":
                return self.manual_trade(symbol, qty, "BUY")
            elif decision == "SELL":
                return self.manual_trade(symbol, qty, "SELL")
            else:
                return {"status": "SKIPPED", "reason": "HOLD signal"}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}