 -*- coding: utf-8 -*-
"""
Fallback Quantum Trader
Used when Qiskit is not available
"""


class FallbackQuantumTrader:
    """Classical trading fallback when quantum computing not available"""

    def __init__(self):
        self.name = "FallbackQuantumTrader"
        self.quantum_available = False

    def quantum_random(self, size=1):
        """Fallback to classical random"""
        import random

        return [random.random() for _ in range(size)]

    def quantum_analyze(self, data):
        """Fallback to classical analysis"""
        import statistics

        return {
            "confidence": statistics.mean(data) if data else 0.5,
            "volatility": statistics.stdev(data) if len(data) > 1 else 0.1,
            "trend": "NEUTRAL",
        }

    def get_status(self):
        return "[FAIL] Quantum Trader disabled (missing Qiskit)"


# Auto-detect and provide appropriate trader
try:
    import qiskit
    from .quantum_trader import QuantumTrader

    trader = QuantumTrader()
    trader_status = "[PASS] Quantum Trader enabled"
except ImportError:
    trader = FallbackQuantumTrader()
    trader_status = trader.get_status()

__all__ = ["trader", "trader_status", "FallbackQuantumTrader"]

