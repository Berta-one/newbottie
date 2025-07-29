# engine/execution_manager.py

import numpy as np
from engine.portfolio_manager import HybridPortfolioManager
from engine.signal_generator import SignalGenerator
from engine.trade_executor import TradeExecutor  # hypothetical module
import logging

class ExecutionManager:
    def __init__(self, num_assets):
        self.signal_generator = SignalGenerator()
        self.portfolio_manager = HybridPortfolioManager(num_assets)
        self.trade_executor = TradeExecutor()
        self.logger = logging.getLogger("ExecutionManager")

    def run_cycle(self, market_data):
        """
        Single trading cycle — extract features, generate signals, rebalance, and execute.
        """
        self.logger.info("🔁 Running trading cycle")

        # 1. Generate signals (or scores)
        expected_returns, cov_matrix = self.signal_generator.analyze(market_data)

        # 2. Portfolio optimization (Quantum or Classical fallback)
        selected_assets = self.portfolio_manager.rebalance(expected_returns, cov_matrix)

        # 3. Execute trades
        self.trade_executor.execute(selected_assets)