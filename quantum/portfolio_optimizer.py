# quantum/portfolio_optimizer.py

from qiskit_optimization.applications import PortfolioOptimization
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit.algorithms import QAOA
from qiskit import Aer
import numpy as np

class QuantumPortfolioOptimizer:
    def __init__(self, budget=3, risk_factor=0.1):
        self.backend = Aer.get_backend("qasm_simulator")
        self.budget = budget
        self.risk_factor = risk_factor

    def optimize(self, returns, covariances):
        num_assets = len(returns)
        portfolio = PortfolioOptimization(expected_returns=returns,
                                          covariances=covariances,
                                          risk_factor=self.risk_factor,
                                          budget=self.budget)
        q_problem = portfolio.to_quadratic_program()
        qaoa = QAOA(quantum_instance=self.backend)
        optimizer = MinimumEigenOptimizer(qaoa)
        result = optimizer.solve(q_problem)
        return result.x