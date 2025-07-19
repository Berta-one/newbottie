from datetime import datetime
from typing import Dict, Any

__all__ = ["PositionMonitor"]

class PositionMonitor:
    """Tracks active positions for manual and auto trades."""

    def __init__(self):
        self._positions: Dict[str, Dict[str, Any]] = {}

    def add(self, symbol: str, data: Dict[str, Any]):
        data.setdefault("opened_at", datetime.now().isoformat())
        self._positions[symbol] = data

    def add_position(self, symbol: str, data: Dict[str, Any]):
        """Alias for backward compatibility."""
        self.add(symbol, data)

    def remove(self, symbol: str):
        self._positions.pop(symbol, None)

    def update(self, symbol: str, updates: Dict[str, Any]):
        if symbol in self._positions:
            self._positions[symbol].update(updates)

    def exists(self, symbol: str) -> bool:
        return symbol in self._positions

    def get_active_positions(self) -> Dict[str, Dict[str, Any]]:
        """Return all currently tracked active positions."""
        return self._positions
