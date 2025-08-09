# engine/integrated_portfolio_engine.py
import logging
from typing import Dict, Any, List

from engine.execution_manager import ExecutionManager

logger = logging.getLogger("IntegratedPortfolioEngine")


class IntegratedPortfolioEngine:
    """
    Orchestrates the trading workflow: receives bars, triggers signal generation,
    portfolio optimization, and execution.
    """

    def __init__(self, symbols: List[str], initial_capital: float = 10_000.0):
        self.symbols = symbols
        self.exec_manager = ExecutionManager(symbols=symbols, initial_capital=initial_capital)

    def on_bar(self, bar: Dict[str, Any]) -> None:
        """
        Process a new bar (market data point).
        bar example:
          {"symbol":"BTC/USDT","close":float,"high":float,"low":float,"volume":float,...}
        """
        try:
            self.exec_manager.on_bar(bar)
        except Exception as exc:
            logger.exception("IntegratedPortfolioEngine.on_bar failed: %s", exc)