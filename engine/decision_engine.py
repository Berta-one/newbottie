# engine/decision_engine.py

from quantum.hybrid_models import HybridQuantumEnsemble
from quantum.fallback_manager import FallbackManager
from quantum.backends import get_best_backend
import logging

logger = logging.getLogger(__name__)

class QuantumDecisionEngine:
    def __init__(self):
        self.quantum_enabled = True
        self.hybrid_model = HybridQuantumEnsemble()
        self.fallback = FallbackManager()
        self.backend = get_best_backend()

    def generate_signal(self, market_features):
        if self.quantum_enabled:
            try:
                signal = self.hybrid_model.predict(market_features)
                logger.info("✅ Quantum signal generated successfully")
                return signal
            except Exception as e:
                logger.warning(f"Quantum model failed: {e}")
                self.quantum_enabled = False
                return self.fallback.predict(market_features)
        else:
            return self.fallback.predict(market_features)