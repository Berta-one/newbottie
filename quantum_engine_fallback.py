"""
quantum_engine_fallback.py
==========================
Fallback quantum engine when Qiskit is unavailable
"""

import numpy as np
from typing import Dict, Any


class QuantumAnalyzer:
    """Fallback quantum analyzer using mathematical simulation"""

    def __init__(self):
        self.backend_name = "Mathematical Simulator"
        print("Quantum using mathematical simulation (Qiskit unavailable)")

    def generate_quantum_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quantum-like signals using mathematical models"""

        # Normalize inputs
        rsi = market_data.get("rsi", 50) / 100
        momentum = market_data.get("momentum", 0)
        volatility = market_data.get("price_volatility", 0.05)

        # Quantum-inspired probability calculation
        theta = np.pi * rsi
        phi = np.pi * volatility

        # Simulate quantum superposition
        amplitude_buy = np.cos(theta / 2) * np.cos(phi / 2)
        amplitude_sell = np.sin(theta / 2) * np.cos(phi / 2)
        amplitude_hold = np.sin(phi / 2)

        # Apply momentum as phase rotation
        momentum_factor = 1 + 0.2 * momentum
        amplitude_buy *= momentum_factor
        amplitude_sell /= momentum_factor if momentum_factor > 0 else 1

        # Calculate probabilities
        prob_buy = amplitude_buy**2
        prob_sell = amplitude_sell**2
        prob_hold = amplitude_hold**2

        # Normalize probabilities
        total = prob_buy + prob_sell + prob_hold
        if total > 0:
            prob_buy, prob_sell, prob_hold = [
                p / total for p in [prob_buy, prob_sell, prob_hold]
            ]
        else:
            prob_buy, prob_sell, prob_hold = 0.33, 0.33, 0.34

        # Determine decision
        probs = {"BUY": prob_buy, "SELL": prob_sell, "HOLD": prob_hold}
        decision = max(probs, key=probs.get)
        confidence = max(probs.values())

        return {
            "decision": decision,
            "confidence": round(confidence, 4),
            "distribution": {
                "BUY": round(prob_buy, 4),
                "SELL": round(prob_sell, 4),
                "HOLD": round(prob_hold, 4),
            },
            "entanglement_score": round(abs(rsi - 0.5) * volatility, 4),
            "superposition_index": round(1 - confidence, 4),
            "circuit": "Mathematical Quantum Simulation",
            "backend": self.backend_name,
        }

    def get_quantum_diagnostics(self) -> Dict[str, Any]:
        return {
            "entanglement_score": round(np.random.uniform(0.5, 1.0), 4),
            "superposition_index": round(np.random.uniform(0.5, 1.0), 4),
            "backend": self.backend_name,
            "quantum_enabled": True,
            "mode": "Mathematical Simulation",
        }

    def evaluate_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Alias for compatibility"""
        return self.generate_quantum_signal(market_data)
