from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List

__all__ = ["PositionMonitor"]


class PositionMonitor:
    """Lightweight in-memory position registry.

    A production implementation should persist this data (e.g. database, Redis).
    For the dashboard demo we keep it simple.
    """

    def __init__(self) -> None:
        # Keyed by symbol – value is an opaque dict containing at least entry_price & qty
        self._positions: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def add(self, symbol: str, position_data: Dict[str, Any]) -> None:
        position_data.setdefault("opened_at", datetime.now().isoformat())
        self._positions[symbol] = position_data

    def remove(self, symbol: str) -> None:
        self._positions.pop(symbol, None)

    def update(self, symbol: str, updates: Dict[str, Any]) -> None:
        if symbol in self._positions:
            self._positions[symbol].update(updates)

    def exists(self, symbol: str) -> bool:
        return symbol in self._positions

    # ------------------------------------------------------------------
    # New method required by hybrid_bot.py
    # ------------------------------------------------------------------
    def get_active_positions(self) -> Dict[str, Dict[str, Any]]:
        """Return all currently tracked active positions."""
        return self._positions
