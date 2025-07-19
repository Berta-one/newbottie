#!/usr/bin/env python3
"""
PositionMonitor
===============
Tracks open positions and calculates:
- Realized PnL
- Unrealized PnL
"""

from typing import Dict
from datetime import datetime

class PositionMonitor:
    def __init__(self):
        self.positions: Dict[str, dict] = {}
        self.realized_pnl = 0.0

    def open_position(self, symbol, price, qty):
        """Add or update position."""
        if symbol in self.positions:
            pos = self.positions[symbol]
            total_qty = pos["qty"] + qty
            avg_price = ((pos["avg_price"] * pos["qty"]) + (price * qty)) / total_qty
            self.positions[symbol].update({"avg_price": avg_price, "qty": total_qty})
        else:
            self.positions[symbol] = {"avg_price": price, "qty": qty, "opened": datetime.now()}

    def close_position(self, symbol, sell_price):
        """Close position and calculate PnL."""
        if symbol not in self.positions:
            return 0.0
        pos = self.positions.pop(symbol)
        pnl = (sell_price - pos["avg_price"]) * pos["qty"]
        self.realized_pnl += pnl
        return pnl

    def get_active_positions(self):
        return self.positions

    def get_realized_pnl(self):
        return self.realized_pnl

    def get_unrealized_pnl(self, price_lookup):
        unrealized = {}
        for symbol, pos in self.positions.items():
            current_price = price_lookup(symbol)
            unrealized[symbol] = (current_price - pos["avg_price"]) * pos["qty"]
        return unrealized