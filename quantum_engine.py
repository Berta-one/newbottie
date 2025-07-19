"""
quantum_engine.py
==================
Quantum signal generator using Qiskit.
Provides quantum-enhanced predictions for crypto trading.
"""

from __future__ import annotations
from typing import Dict, Any
import numpy as np
from qiskit import QuantumCircuit, Aer, execute
from qiskit.quantum_info import Statevector


class QuantumAnalyzer:
    """Generates quantum-based trading signals using Qiskit simulation."""

    def __init__(self):
        self.backend = Aer.get_backend("aer_simulator_statevector")

    def generate_quantum_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate BUY/SELL/HOLD probabilities using a quantum circuit.
        :param market_data: dict containing price and indicators.
        :return: dict with quantum prediction details.
        """

        # Extract features (normalize to [0, π])
        rsi = np.clip(market_data.get("rsi", 50) / 100, 0, 1) * np.pi
        momentum = np.clip(market_data.get("momentum", 0), -1, 1) * (np.pi / 2)
        price_vol = np.clip(market_data.get("price_volatility", 0.05), 0, 1) * np.pi

        # Build quantum circuit with feature encoding
        qc = QuantumCircuit(2)
        qc.h([0, 1])
        qc.ry(rsi, 0)
        qc.rx(momentum, 1)
        qc.cx(0, 1)
        qc.ry(price_vol, 1)

        # Simulate
        result = execute(qc, self.backend).result()
        statevector = Statevector(result.get_statevector(qc))
        probs = statevector.probabilities_dict()

        # Interpret probabilities
        buy_prob = probs.get("00", 0) + probs.get("01", 0)
        sell_prob = probs.get("10", 0)
        hold_prob = probs.get("11", 0)

        # Normalize
        total = buy_prob + sell_prob + hold_prob
        buy_prob /= total
        sell_prob /= total
        hold_prob /= total

        # Decision
        decision = max([("BUY", buy_prob), ("SELL", sell_prob), ("HOLD", hold_prob)], key=lambda x: x[1])[0]

        return {
            "decision": decision,
            "confidence": round(max(buy_prob, sell_prob, hold_prob), 4),
            "distribution": {
                "BUY": round(buy_prob, 4),
                "SELL": round(sell_prob, 4),
                "HOLD": round(hold_prob, 4)
            },
            "statevector": [complex(x).real for x in statevector],
            "circuit": qc.draw(output="text")
        }

    def get_quantum_diagnostics(self) -> Dict[str, Any]:
        """Returns sample quantum metrics for display."""
        return {
            "entanglement_score": np.random.uniform(0.5, 1.0),
            "superposition_index": np.random.uniform(0.5, 1.0),
            "backend": self.backend.name()
        }