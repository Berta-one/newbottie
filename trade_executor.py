from typing import Dict, Any

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None

from trader import execute_entry, execute_exit, validate_trade_parameters
from risk_manager import RiskManager

__all__ = ["TradeExecutor"]

class TradeExecutor:
    """Unified trade execution for manual and auto-trading."""

    def __init__(self, client: Client | None = None, risk_mgr: RiskManager | None = None):
        self._client = client
        self._risk = risk_mgr or RiskManager()

    def manual_trade(self, symbol: str, quantity: float, side: str, price: float | None = None) -> Dict[str, Any]:
        """Perform a manual BUY or SELL after risk validation."""
        side = side.upper()
        ok, err = validate_trade_parameters(symbol, quantity, price)
        if not ok:
            return {"status": "FAILED", "error": err}

        if not self._risk._risk_below_position_limit(symbol, quantity):
            return {"status": "FAILED", "error": "Position size exceeds risk limits"}

        if side == "BUY":
            return execute_entry(self._client, symbol, quantity, "BUY_LONG")
        elif side == "SELL":
            return execute_exit(self._client, symbol, quantity, 0, 0, "Manual exit")
        else:
            return {"status": "FAILED", "error": f"Unsupported side '{side}'"}

    def auto_execute(self, trade_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute signals from autonomous strategy pipeline."""
        return {"status": "NOT_IMPLEMENTED"}
