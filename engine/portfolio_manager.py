# engine/portfolio_manager.py

from quantum.portfolio_optimizer import QuantumPortfolioOptimizer
from classical.portfolio_optimizer import ClassicalPortfolioOptimizer
import logging

logger = logging.getLogger(__name__)

class HybridPortfolioManager:
    def __init__(self, use_quantum=True):
        self.quantum = QuantumPortfolioOptimizer()
        self.classical = ClassicalPortfolioOptimizer()
        self.use_quantum = use_quantum

    def rebalance(self, returns, covariances):
        try:
            if self.use_quantum:
                logger.info("🧠 Using Quantum Optimizer for portfolio")
                return self.quantum.optimize(returns, covariances)
        except Exception as e:
            logger.warning(f"⚠️ Quantum optimization failed: {e}")

        logger.info("🔁 Falling back to Classical Optimizer")
        return self.classical.optimize(returns, covariances)