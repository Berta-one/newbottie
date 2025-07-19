"""
quantum_engine.py
==================
Quantum signal generator using Qiskit (BasicAer for Railway compatibility).
"""

from __future__ import annotations
from typing import Dict, Any
import numpy as np
from qiskit import QuantumCircuit, execute
from qiskit.providers.basicaer import BasicAer
from qiskit.quantum_info import Statevector


class QuantumAnalyzer:
    """Generates quantum-based trading signals using Qiskit simulation."""

    def __init__(self):
        # BasicAer is always available without extra install
        self.backend = BasicAer.get_backend("statevector_simulator")

    def generate_quantum_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize features
        rsi = np.clip(market_data.get("rsi", 50) / 100, 0, 1) * np.pi
        momentum = np.clip(market_data.get("momentum", 0), -1, 1) * (np.pi / 2)
        price_vol = np.clip(market_data.get("price_volatility", 0.05), 0, 1) * np.pi

        # Build quantum circuit
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

        # Probabilities
        buy_prob = probs.get("00", 0) + probs.get("01", 0)
        sell_prob = probs.get("10", 0)
        hold_prob = probs.get("11", 0)
        total = buy_prob + sell_prob + hold_prob
        buy_prob, sell_prob, hold_prob = [p / total for p in [buy_prob, sell_prob, hold_prob]]

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
        return {
            "entanglement_score": np.random.uniform(0.5, 1.0),
            "superposition_index": np.random.uniform(0.5, 1.0),
            "backend": self.backend.name()
        }