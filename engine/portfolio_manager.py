# engine/portfolio_manager.py

import numpy as np
from quantum.portfolio_optimizer import QuantumPortfolioOptimizer
from engine.classical_portfolio import ClassicalPortfolioOptimizer  # assume this is your classical fallback
import logging

class HybridPortfolioManager:
    def __init__(self, num_assets, initial_capital=10000, risk_aversion=0.1, budget=None):
        self.num_assets = num_assets
        self.initial_capital = initial_capital
        self.risk_aversion = risk_aversion
        self.budget = budget if budget is not None else num_assets
        self.quantum_optimizer = QuantumPortfolioOptimizer(num_assets, budget=self.budget, risk_aversion=risk_aversion)
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
            selected_assets = self.classical_optimizer.optimize(expected_returns, cov_matrix)
            self.logger.info(f"✅ Classical fallback selected: {selected_assets}")
            return selected_assets