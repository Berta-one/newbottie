"""
position_monitor.py
========================
Tracks open positions for manual and automated trades.
"""

from __future__ import annotations
from typing import Dict, Any
from datetime import datetime


class PositionMonitor:
    def __init__(self):
        self.positions: Dict[str, Dict[str, Any]] = {}

    # -------------------------------
    # Add or Update Position
    # -------------------------------
    def add_position(self, symbol: str, details: Dict[str, Any]):
        details["opened_at"] = details.get("opened_at", datetime.now().isoformat())
        self.positions[symbol] = details

    # -------------------------------
    # Remove Position
    # -------------------------------
    def remove_position(self, symbol: str):
        if symbol in self.positions:
            del self.positions[symbol]

    # -------------------------------
    # Get Position by Symbol
    # -------------------------------
    def get_position(self, symbol: str) -> Dict[str, Any]:
        return self.positions.get(symbol, {})

    # -------------------------------
    # Get All Active Positions
    # -------------------------------
    def get_active_positions(self) -> Dict[str, Any]:
        return self.positions

    # -------------------------------
    # Check if Position Exists
    # -------------------------------
    def is_open(self, symbol: str) -> bool:
        return symbol in self.positions