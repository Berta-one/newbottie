class PositionMonitor:
    def __init__(self):
        self._positions = {}

    def add(self, symbol: str, data: dict):
        self._positions[symbol] = data

    def add_position(self, symbol: str, data: dict):
        """Alias for backward compatibility."""
        self.add(symbol, data)

    def remove(self, symbol: str):
        self._positions.pop(symbol, None)

    def update(self, symbol: str, updates: dict):
        if symbol in self._positions:
            self._positions[symbol].update(updates)

    def get_active_positions(self) -> dict:
        return self._positions
