# engine/portfolio_manager.py

import numpy as np
from quantum.portfolio_optimizer import QuantumPortfolioOptimizer
from engine.classical_optimizer import ClassicalPortfolioOptimizer  # classical fallback
import logging

class HybridPortfolioManager:
    def __init__(self, num_assets, initial_capital=10000, risk_aversion=0.1, budget=None):
        self.num_assets = num_assets
        self.initial_capital = initial_capital
        self.risk_aversion = risk_aversion
        self.budget = budget if budget is not None else num_assets
        self.quantum_optimizer = QuantumPortfolioOptimizer(risk_aversion=risk_aversion, budget=self.budget)
        self.classical_optimizer = ClassicalPortfolioOptimizer(num_assets, initial_capital)
        self.logger = logging.getLogger("PortfolioManager")

    def rebalance(self, expected_returns, cov_matrix):
        """
        Try quantum optimization, fallback to classical if failure occurs.
        """
        self.logger.info("📈 Rebalancing portfolio using hybrid optimizer")

        try:
            selected_assets = self.quantum_optimizer.optimize(expected_returns, cov_matrix)

            if not selected_assets:
                raise ValueError("Quantum optimization returned empty set")
            
            self.logger.info(f"✅ Quantum portfolio selected: {selected_assets}")
            return selected_assets

        except Exception as e:
            self.logger.warning(f"⚠️ Quantum failed. Falling back to classical optimizer: {e}")
            classical_result = self.classical_optimizer.optimize(expected_returns, cov_matrix)

            # The classical optimiser returns a rich dictionary containing the
            # weight vector under the ``solution`` key.  For API consistency we
            # expose the weight vector directly to callers so that both the
            # quantum and classical branches yield a simple ``list``.
            selected_assets = (
                classical_result["solution"]
                if isinstance(classical_result, dict) and "solution" in classical_result
                else classical_result
            )

            self.logger.info(f"✅ Classical fallback selected: {selected_assets}")
            return selected_assets