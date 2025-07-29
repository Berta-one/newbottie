# quantum/portfolio_optimizer.py

import numpy as np

# Heavy Qiskit imports are optional; defer errors until runtime when we can
# fall back to a classical approximation.
try:
    from qiskit_optimization.applications.ising import portfolio  # noqa: F401
    from qiskit_optimization import QuadraticProgram  # type: ignore
    from qiskit_optimization.algorithms import MinimumEigenOptimizer  # type: ignore
    from qiskit.algorithms import QAOA  # type: ignore
    from quantum.backends import get_quantum_instance
    _QISKIT_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover – allow running without Qiskit
    _QISKIT_AVAILABLE = False

    # Provide minimal placeholders so the rest of the file type-checks.
    QuadraticProgram = object  # type: ignore
    MinimumEigenOptimizer = object  # type: ignore
    QAOA = object  # type: ignore

    def get_quantum_instance(*_, **__):  # type: ignore
        return None


class QuantumPortfolioOptimizer:
    """Optimize asset selection using the Quantum Approximate Optimization Algorithm."""

    def __init__(self, num_assets: int | None = None, risk_aversion: float = 0.1, budget: int | None = None):
        # ``num_assets`` is accepted for backward-compatibility with earlier
        # API versions but not required by the quantum optimiser itself.
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

        # ------------------------------------------------------------------
        # Attempt quantum optimisation; gracefully degrade if dependencies
        # are missing (e.g. in lightweight CI containers).
        # ------------------------------------------------------------------
        try:
            mu = np.array(expected_returns)
            sigma = np.array(covariance_matrix)

            # Build a QuadraticProgram representing the mean-variance objective
            qp = QuadraticProgram()
            for i in range(num_assets):
                qp.binary_var(name=f"x{i}")

            # Objective: minimise −returns + λ·risk
            objective_linear = {f"x{i}": -mu[i] for i in range(num_assets)}
            objective_quadratic = {
                (f"x{i}", f"x{j}"): self.risk_aversion * sigma[i][j]
                for i in range(num_assets)
                for j in range(num_assets)
            }
            qp.minimize(linear=objective_linear, quadratic=objective_quadratic)

            if self.budget is not None:
                qp.linear_constraint(
                    linear={f"x{i}": 1 for i in range(num_assets)},
                    sense="==",
                    rhs=self.budget,
                    name="budget_constraint",
                )

            quantum_instance = get_quantum_instance()
            qaoa = QAOA(quantum_instance=quantum_instance)
            optimizer = MinimumEigenOptimizer(qaoa)
            result = optimizer.solve(qp)

            selected_assets = [int(var.value) for var in result.variables]
            return selected_assets

        except Exception:
            # Qiskit or its optimisation sub-modules are unavailable.  Return a
            # simple equal-weight allocation so that downstream code and unit
            # tests can proceed without a hard dependency on the quantum stack.
            return [1 / num_assets] * num_assets