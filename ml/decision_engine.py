# ml/decision_engine.py

from quantum.hybrid_models import HybridQuantumEnsemble

class DecisionEngine:
    def __init__(self):
        self.ensemble = HybridQuantumEnsemble()

    def generate_signal(self, features):
        pred = self.ensemble.predict(features)
        if pred > 0.6:
            return "buy"
        elif pred < 0.4:
            return "sell"
        else:
            return "hold"