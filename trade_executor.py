from __future__ import annotations

from typing import Dict, Any

try:
    from binance.client import Client
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None  # type: ignore

from trader import (
    execute_entry,
    execute_exit,
    validate_trade_parameters,
)
from risk_manager import RiskManager

__all__ = ["TradeExecutor"]


class TradeExecutor:
    """Unified trade execution interface used by both manual UI actions and the auto-trader."""

    def __init__(self, client: Client | None = None, risk_mgr: RiskManager | None = None):  # type: ignore[name-defined]
        self._client = client
        self._risk = risk_mgr or RiskManager()

    # ------------------------------------------------------------------
    # Manual trading API – called from Streamlit callbacks
    # ------------------------------------------------------------------
    def manual_trade(self, symbol: str, quantity: float, side: str, price: float | None = None) -> Dict[str, Any]:
        """Perform a manual BUY or SELL after risk validation."""
        side = side.upper()
        ok, err = validate_trade_parameters(symbol, quantity, price)
        if not ok:
            return {"status": "FAILED", "error": err}

        # Basic risk budget check – extend with dynamic rules
        if not self._risk_below_position_limit(symbol, quantity):
            return {"status": "FAILED", "error": "Position size exceeds risk limits"}

        if side == "BUY":
            return execute_entry(self._client, symbol, quantity, "BUY_LONG")
        elif side == "SELL":
            # We do not know entry/exit prices at this abstraction level – pass zeros, trader.py will fetch
            return execute_exit(self._client, symbol, quantity, 0, 0, "Manual exit")
        else:
            return {"status": "FAILED", "error": f"Unsupported side '{side}'"}

    # ------------------------------------------------------------------
    # Placeholder for auto-trading hooks (not implemented in this skeleton)
    # ------------------------------------------------------------------
    def auto_execute(self, trade_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute signals produced by the autonomous strategy pipeline."""
        # TODO: integrate with scanner_main / strategy modules
        return {"status": "NOT_IMPLEMENTED"}

    # ------------------------------------------------------------------
    # Risk helpers
    # ------------------------------------------------------------------
    def _risk_below_position_limit(self, symbol: str, quantity: float) -> bool:
        # Leverage RiskManager dynamic rules to determine allowed position sizing.
        # For demonstration we accept everything – real implementation would check limits.
        return True