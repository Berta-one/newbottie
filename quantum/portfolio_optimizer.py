# quantum/portfolio_optimizer.py
import os
import logging
from typing import List, Tuple
import numpy as np

from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit.primitives import Sampler
from qiskit.circuit.library import TwoLocal

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


def _bitstring_to_weights(bits: List[int]) -> np.ndarray:
    """Map selection bits to equal weights over selected assets."""
    bits = np.array(bits, dtype=float)
    cnt = bits.sum()
    if cnt <= 0:
        # No selection, fallback to uniform tiny distribution
        return np.full_like(bits, 1.0 / len(bits))
    w = bits / cnt
    return w


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
        self.backend = get_backend()  # IBM or Aer
        shots = int(os.getenv("QUANTUM_SHOTS", "2048"))
        self.sampler = Sampler(options={"shots": shots}, backend=self.backend.backend)

        # Simple ansatz; you can tune entanglement later
        self.ansatz = TwoLocal(rotation_blocks="ry", entanglement_blocks="cz", reps=2, entanglement="linear")

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

        qp = _build_mv_qubo(mu=np.array(mu, dtype=float),
                            cov=np.array(cov, dtype=float),
                            lambda_risk=self.lambda_risk,
                            budget=budget)

        qaoa = QAOA(sampler=self.sampler, ansatz=self.ansatz)
        optimizer = MinimumEigenOptimizer(qaoa)

        log.info("QAOA start | assets=%d budget=%d backend=%s", n, budget, self.backend.kind)
        try:
            result = optimizer.solve(qp)
            # result.x is binary selection
            bits = [int(round(v)) for v in result.x]
            w = _bitstring_to_weights(bits)
            log.info("QAOA done | selection=%s", bits)
            return w
        except Exception as e:
            log.warning("QAOA failed (%s). Falling back to uniform weights.", e)
            return np.full(n, 1.0 / n, dtype=float)