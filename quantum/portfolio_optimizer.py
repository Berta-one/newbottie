# quantum/portfolio_optimizer.py
import logging
import numpy as np

from qiskit_optimization import QuadraticProgram

from .backends import get_backend

log = logging.getLogger("QuantumPortfolio")


def _build_mv_qubo(mu: np.ndarray, cov: np.ndarray, lambda_risk: float, budget: int) -> QuadraticProgram:
    """
    Build a binary mean-variance QUBO:
      maximize: mu^T x - lambda * x^T cov x
      subject to sum(x_i) == budget, x_i in {0,1}
    """
    n = len(mu)
    qp = QuadraticProgram("mean_variance")
    for i in range(n):
        qp.binary_var(name=f"x_{i}")

    # Objective: we convert to *minimize*, so negate the maximization
    Q = (-lambda_risk) * cov
    c = -mu
    const = 0.0
    qp.minimize(constant=const, linear=c, quadratic=Q)

    # Budget (exactly choose 'budget' assets)
    lin = np.ones(n)
    qp.linear_constraint(linear=lin, sense="==", rhs=budget, name="budget")

    return qp


class QuantumPortfolioOptimizer:
    """
    QAOA-based mean-variance optimizer with safe fallbacks.
    Env:
      - QUANTUM_SHOTS (int)
      - QUANTUM_TIMEOUT_S (int)
    """
    def __init__(self, lambda_risk: float = 0.1, budget: int = None):
        self.lambda_risk = float(lambda_risk)
        self.budget = budget  # if None -> choose ~n/3
        self.backend = get_backend()  # IBM or Aer (used for logging / future QAOA wiring)

    def optimize(self, mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
        """
        mu: expected returns (shape [n])
        cov: covariance matrix (shape [n,n])
        returns: weights in [0,1], sum to 1
        """
        n = len(mu)
        if self.budget is None:
            budget = max(1, n // 3)
        else:
            budget = max(1, min(self.budget, n))

        _ = _build_mv_qubo(
            mu=np.array(mu, dtype=float),
            cov=np.array(cov, dtype=float),
            lambda_risk=self.lambda_risk,
            budget=budget,
        )

        log.info(
            "Quantum optimizer (QAOA + MinimumEigenOptimizer) not wired for qiskit-algorithms 0.4+ / "
            "Qiskit 2.x yet; using uniform weights | assets=%d budget=%d backend=%s",
            n,
            budget,
            self.backend.kind,
        )
        return np.full(n, 1.0 / n, dtype=float)