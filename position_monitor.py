#!/usr/bin/env python3
"""
Position Monitor
================
Tracks open positions, applies SL/TP auto-close logic, and updates logs.
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any
from binance.client import Client

LOG_DIR = "logs"
ACTIVE_POSITIONS_FILE = os.path.join(LOG_DIR, "active_positions.json")


class PositionMonitor:
    def __init__(self):
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        if not os.path.exists(ACTIVE_POSITIONS_FILE):
            with open(ACTIVE_POSITIONS_FILE, "w") as f:
                json.dump({"active": {}}, f)

        self.active_positions = self._load_positions()

    # -------------------------------
    # Position Management
    # -------------------------------
    def add_position(self, symbol: str, qty: float, entry_price: float, sl: float, tp: float):
        self.active_positions[symbol] = {
            "symbol": symbol,
            "qty": qty,
            "entry_price": entry_price,
            "sl": sl,
            "tp": tp,
            "opened_at": datetime.now().isoformat()
        }
        self._save_positions()

    def remove_position(self, symbol: str):
        if symbol in self.active_positions:
            del self.active_positions[symbol]
            self._save_positions()

    def get_active_positions(self) -> Dict[str, Any]:
        return self.active_positions

    def get_portfolio_snapshot(self) -> Dict[str, Any]:
        """Used for risk checks."""
        return {
            sym: {
                "value": pos["qty"] * pos["entry_price"]
            }
            for sym, pos in self.active_positions.items()
        }

    # -------------------------------
    # SL/TP Monitor Loop
    # -------------------------------
    def monitor_positions(self, client: Client, callback_close):
        """
        Monitors positions in real-time and closes if SL or TP is hit.
        Runs in background thread from dashboard.
        :param client: Binance client for price checks
        :param callback_close: function(symbol, qty) to execute close trade
        """
        while True:
            if not self.active_positions:
                time.sleep(5)
                continue

            for symbol, pos in list(self.active_positions.items()):
                try:
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker["price"])
                    sl, tp = pos["sl"], pos["tp"]

                    if current_price <= sl:
                        callback_close(symbol, pos["qty"])
                        self._log_exit(symbol, pos, current_price, "SL")
                        self.remove_position(symbol)

                    elif current_price >= tp:
                        callback_close(symbol, pos["qty"])
                        self._log_exit(symbol, pos, current_price, "TP")
                        self.remove_position(symbol)

                except Exception as e:
                    print(f"[PositionMonitor ERROR] {e}")

            time.sleep(5)  # Check every 5 sec

    # -------------------------------
    # Internal Helpers
    # -------------------------------
    def _load_positions(self):
        try:
            with open(ACTIVE_POSITIONS_FILE, "r") as f:
                data = json.load(f)
            return data.get("active", {})
        except Exception:
            return {}

    def _save_positions(self):
        with open(ACTIVE_POSITIONS_FILE, "w") as f:
            json.dump({"active": self.active_positions}, f, indent=4)

    def _log_exit(self, symbol: str, pos: Dict[str, Any], exit_price: float, reason: str):
        log_line = (
            f"{datetime.now().isoformat()} | EXIT {symbol} | {reason} | "
            f"Qty: {pos['qty']} | Entry: {pos['entry_price']} | Exit: {exit_price}"
        )
        with open(os.path.join(LOG_DIR, "position_exits.log"), "a") as f:
            f.write(log_line + "\n")