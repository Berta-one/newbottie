import numpy as np
from scipy.optimize import minimize


class ClassicalPortfolioOptimizer:
    """Mean-variance (Markowitz) classical portfolio optimiser.

    Acts as a fallback when quantum optimisation fails or is unavailable.
    """

    def __init__(self, risk_aversion: float = 0.5):
        self.risk_aversion = risk_aversion

    def optimize(self, expected_returns, covariance_matrix, budget: float = 1.0):
        n_assets = len(expected_returns)
        mu = np.array(expected_returns, dtype=float)
        sigma = np.array(covariance_matrix, dtype=float)

        # Initial guess: equal weights
        x0 = np.full(n_assets, 1.0 / n_assets)

        # Objective: maximise return − λ * risk (we minimise its negative)
        def objective(weights):
            ret = np.dot(weights, mu)
            risk = weights.T @ sigma @ weights
            return -(ret - self.risk_aversion * risk)

        # Constraints: fully invested and long-only
        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - budget})
        bounds = tuple((0.0, 1.0) for _ in range(n_assets))

        res = minimize(objective, x0, bounds=bounds, constraints=constraints)

        return {
            'solution': res.x.tolist(),
            'objective_value': -res.fun,
            'status': res.message,
        }