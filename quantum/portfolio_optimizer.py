# quantum/portfolio_optimizer.py

import numpy as np
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit.algorithms import QAOA
from qiskit.utils import algorithm_globals
from qiskit_aer.primitives import Sampler
from quantum.backends import get_ibmq_provider

class QuantumPortfolioOptimizer:
    def __init__(self, num_assets: int, budget: int = None, risk_aversion: float = 0.1):
        self.num_assets = num_assets
        self.budget = budget if budget is not None else num_assets
        self.risk_aversion = risk_aversion
        algorithm_globals.random_seed = 42
        self.provider = get_ibmq_provider()
        self.backend = self.provider.get_backend('ibmq_qasm_simulator')  # Replace with real backend if needed
        self.sampler = Sampler()  # For QAOA
        self.qaoa = QAOA(sampler=self.sampler, reps=1)

    def build_problem(self, expected_returns, cov_matrix):
        """
        Construct the portfolio optimization problem as a Quadratic Program.
        Maximize return - λ * risk, subject to budget.
        """
        qp = QuadraticProgram()
        for i in range(self.num_assets):
            qp.binary_var(name=f"x{i}")

        linear = {f"x{i}": -expected_returns[i] for i in range(self.num_assets)}
        quadratic = {
            (f"x{i}", f"x{j}"): self.risk_aversion * cov_matrix[i][j]
            for i in range(self.num_assets) for j in range(self.num_assets)
        }

        qp.minimize(linear=linear, quadratic=quadratic)

        # Budget constraint: sum x_i == budget
        constraint = {f"x{i}": 1 for i in range(self.num_assets)}
        qp.linear_constraint(linear=constraint, sense='==', rhs=self.budget, name='budget')

        return qp

    def optimize(self, expected_returns, cov_matrix):
        """
        Solve the optimization problem using QAOA and return selected asset indices.
        """
        problem = self.build_problem(expected_returns, cov_matrix)
        optimizer = MinimumEigenOptimizer(self.qaoa)
        try:
            result = optimizer.solve(problem)
            selected_assets = [i for i, x in enumerate(result.x) if x > 0.5]
            print(f"✅ Quantum Optimizer selected assets: {selected_assets}")
            return selected_assets
        except Exception as e:
            print(f"❌ Quantum Optimization failed: {e}")
            return []