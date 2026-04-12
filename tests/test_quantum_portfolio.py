# tests/test_quantum_portfolio.py

import unittest

import numpy as np

from engine.portfolio_manager import HybridPortfolioManager
from quantum.portfolio_optimizer import QuantumPortfolioOptimizer


class TestPortfolioOptimizer(unittest.TestCase):
    def test_quantum_optimizer_runs(self):
        mu = np.array([0.05, 0.02, 0.03], dtype=float)
        cov = np.array(
            [
                [0.001, 0.0001, 0.0002],
                [0.0001, 0.002, 0.0003],
                [0.0002, 0.0003, 0.001],
            ],
            dtype=float,
        )
        qp = QuantumPortfolioOptimizer(lambda_risk=0.1, budget=1)
        weights = qp.optimize(mu, cov)
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(float(sum(weights)), 1.0, delta=0.1)

    def test_hybrid_fallback_runs(self):
        symbols = ["A", "B", "C"]
        conf_map = {"A": 0.3, "B": 0.5, "C": 0.2}
        hp = HybridPortfolioManager(max_pos_pct=0.5)
        weights = hp.target_weights(symbols, conf_map)
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(sum(weights.values()), 1.0, delta=0.01)


if __name__ == "__main__":
    unittest.main()
