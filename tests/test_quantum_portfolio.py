# tests/test_quantum_portfolio.py

import unittest
from quantum.portfolio_optimizer import QuantumPortfolioOptimizer
from engine.portfolio_manager import HybridPortfolioManager
import numpy as np

class TestPortfolioOptimizer(unittest.TestCase):

    def test_quantum_optimizer_runs(self):
        returns = [0.05, 0.02, 0.03]
        cov = [
            [0.001, 0.0001, 0.0002],
            [0.0001, 0.002, 0.0003],
            [0.0002, 0.0003, 0.001]
        ]
        qp = QuantumPortfolioOptimizer(num_assets=3)
        weights = qp.optimize(returns, cov)
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(sum(weights), 1.0, delta=0.1)

    def test_hybrid_fallback_runs(self):
        returns = [0.01, 0.02, 0.04]
        cov = np.identity(3).tolist()
        hp = HybridPortfolioManager(num_assets=3)
        weights = hp.rebalance(returns, cov)
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(sum(weights), 1.0, delta=0.1)

if __name__ == "__main__":
    unittest.main()