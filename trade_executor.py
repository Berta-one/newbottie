#!/usr/bin/env python3
"""
Trade Executor
==============
Executes trades on Binance (spot), applies SL/TP logic, respects RiskManager rules.
"""

import os
import time
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from binance.client import Client
from binance.enums import *
from risk_manager import RiskManager
from position_monitor import PositionMonitor
from market_analyzer import MarketAnalyzer

LOG_FILE = "logs/trades.csv"


class TradeExecutor:
    def __init__(self, client: Client, risk_manager: RiskManager, test_mode: bool = True):
        self.client = client
        self.risk_manager = risk_manager
        self.test_mode = test_mode
        self.position_monitor = PositionMonitor()
        self.market_analyzer = MarketAnalyzer(client)

        # Ensure log file exists
        if not os.path.exists("logs"):
            os.makedirs("logs")
        if not os.path.exists(LOG_FILE):
            pd.DataFrame(columns=[
                "timestamp", "symbol", "side", "qty", "entry_price", "sl", "tp", "reason", 
                "confidence", "strategy"
            ]).to_csv(LOG_FILE, index=False)

    # -------------------------------
    # Core Methods
    # -------------------------------
    def manual_trade(self, symbol: str, qty: float, side: str, confidence: float = None, strategy: str = "manual"):
        price = self.market_analyzer.get_price(symbol)
        reason = "Manual trade"
        return self._execute_trade(symbol, qty, side, price, reason, confidence, strategy)

    def auto_execute(self, signal: Dict[str, Any]):
        """Execute trade from signal dict: {symbol, decision, confidence, atr}"""
        symbol = signal["symbol"]
        decision = signal["decision"]
        confidence = signal.get("confidence", 0.5)
        atr = signal.get("atr", 0.0)
        reason = signal.get("reason", "Auto signal")
        strategy = signal.get("strategy", "ensemble")

        if decision.upper() != "BUY":
            return f"Skipped {symbol} (decision={decision})"

        price = self.market_analyzer.get_price(symbol)

        # Calculate dynamic position size using risk manager + ATR
        qty = self._calculate_position_size(symbol, price, atr)
        if qty <= 0:
            return f"Trade skipped: insufficient size for {symbol}"

        open_positions = len(self.position_monitor.get_active_positions())
        total_balance_usd = self._get_total_usd_balance()
        risk_check = self.risk_manager.validate_trade(symbol, qty, price, total_balance_usd, open_positions)

        if not risk_check["status"]:
            return f"Risk check failed for {symbol}: {risk_check['reason']}"

        return self._execute_trade(symbol, qty, "BUY", price, reason, confidence, strategy, atr)

    # -------------------------------
    # Internal Execution Logic
    # -------------------------------
    def _execute_trade(self, symbol, qty, side, price, reason, confidence=None, strategy="manual", atr=None):
        # Compute SL and TP based on ATR or fallback %
        sl, tp = self._calculate_sl_tp(price, atr)

        if self.test_mode:
            order_id = f"TEST-{int(time.time())}"
            result = {
                "order_id": order_id,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "price": price,
                "sl": sl,
                "tp": tp,
                "status": "FILLED"
            }
        else:
            try:
                order = self.client.order_market_buy(symbol=symbol, quantity=qty) if side == "BUY" else \
                        self.client.order_market_sell(symbol=symbol, quantity=qty)
                result = order
            except Exception as e:
                return f"Execution error for {symbol}: {e}"

        # Log trade
        self._log_trade(symbol, side, qty, price, sl, tp, reason, confidence, strategy)

        # Register position for SL/TP monitoring
        if side == "BUY":
            self.position_monitor.add_position(symbol, qty, price, sl, tp)

        return f"Executed {side} {symbol} @ {price:.2f}, SL={sl:.2f}, TP={tp:.2f}"

    def _calculate_position_size(self, symbol: str, price: float, atr: float) -> float:
        total_balance = self._get_total_usd_balance()
        max_risk_usd = total_balance * self.risk_manager.max_risk_percent
        stop_distance = atr * 1.5 if atr > 0 else price * 0.02
        qty = max_risk_usd / stop_distance
        return round(qty, 6)

    def _calculate_sl_tp(self, entry_price: float, atr: float = None, rr_ratio: float = 2.0):
        if atr and atr > 0:
            sl = entry_price - atr * 1.5
            tp = entry_price + atr * 1.5 * rr_ratio
        else:
            sl = entry_price * 0.98  # fallback 2% stop
            tp = entry_price * 1.04  # fallback 4% target
        return sl, tp

    def _log_trade(self, symbol, side, qty, entry_price, sl, tp, reason, confidence, strategy):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "entry_price": entry_price,
            "sl": sl,
            "tp": tp,
            "reason": reason,
            "confidence": confidence,
            "strategy": strategy
        }
        df = pd.DataFrame([log_entry])
        df.to_csv(LOG_FILE, mode="a", header=False, index=False)

    def _get_total_usd_balance(self):
        return sum(v["value"] for v in self.position_monitor.get_portfolio_snapshot().values())