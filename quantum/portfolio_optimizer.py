# quantum/portfolio_optimizer.py

import numpy as np
from qiskit_optimization.applications.ising import portfolio
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit.algorithms import QAOA
from quantum.backends import get_quantum_instance


class QuantumPortfolioOptimizer:
    """Optimize asset selection using the Quantum Approximate Optimization Algorithm."""

    def __init__(self, risk_aversion: float = 0.1, budget: int | None = None):
        self.risk_aversion = risk_aversion
        self.budget = budget  # Number of assets to select (optional)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def optimize(self, expected_returns: list[float], covariance_matrix: list[list[float]]):
        """Return a binary list indicating selected assets.

        Parameters
        ----------
        expected_returns : list[float]
            Expected return for each asset.
        covariance_matrix : list[list[float]]
            Covariance matrix between asset returns.
        """
        num_assets = len(expected_returns)

        mu = np.array(expected_returns)
        sigma = np.array(covariance_matrix)

        # Build a QuadraticProgram representing the mean-variance objective
        qp = QuadraticProgram()
        for i in range(num_assets):
            qp.binary_var(name=f"x{i}")

        # Objective: minimise -(returns) + risk_aversion * variance
        objective_linear = {f"x{i}": -mu[i] for i in range(num_assets)}
        objective_quadratic = {
            (f"x{i}", f"x{j}"): self.risk_aversion * sigma[i][j]
            for i in range(num_assets)
            for j in range(num_assets)
        }
        qp.minimize(linear=objective_linear, quadratic=objective_quadratic)

        if self.budget is not None:
            # Constraint: exactly *budget* assets selected
            qp.linear_constraint(
                linear={f"x{i}": 1 for i in range(num_assets)},
                sense="==",
                rhs=self.budget,
                name="budget_constraint",
            )

        # Solve using QAOA
        quantum_instance = get_quantum_instance()
        qaoa = QAOA(quantum_instance=quantum_instance)
        optimizer = MinimumEigenOptimizer(qaoa)
        result = optimizer.solve(qp)

        selected_assets = [int(var.value) for var in result.variables]
        return selected_assets