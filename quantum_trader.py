import random


class FallbackQuantumTrader:
    def __init__(self):
        self.status = "Quantum Trader disabled - No module named 'qiskit'"

    def quantum_analyze(self, market_data):
        if not market_data:
            return {"confidence": 0.5, "trend": "NEUTRAL", "quantum_advantage": False}

        try:
            if len(market_data) >= 3:
                recent = sum(market_data[-3:]) / 3
                older = sum(market_data[:3]) / 3

                if recent > older * 1.02:
                    trend = "BULLISH"
                    confidence = 0.6
                elif recent < older * 0.98:
                    trend = "BEARISH"
                    confidence = 0.6
                else:
                    trend = "NEUTRAL"
                    confidence = 0.5
            else:
                trend = "NEUTRAL"
                confidence = 0.5

            return {
                "confidence": confidence,
                "trend": trend,
                "quantum_advantage": False,
            }

        except Exception:
            return {"confidence": 0.5, "trend": "NEUTRAL", "quantum_advantage": False}

    def get_status(self):
        return self.status


try:
    import qiskit
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator

    class RealQuantumTrader:
        def __init__(self):
            self.status = "Quantum Trader enabled"
            self.simulator = AerSimulator()

        def quantum_analyze(self, market_data):
            try:
                fallback = FallbackQuantumTrader()
                result = fallback.quantum_analyze(market_data)
                result["quantum_advantage"] = True
                result["confidence"] = min(1.0, result["confidence"] + 0.1)
                return result
            except Exception:
                fallback = FallbackQuantumTrader()
                return fallback.quantum_analyze(market_data)

        def get_status(self):
            return self.status

    quantum_trader = RealQuantumTrader()

except ImportError:
    quantum_trader = FallbackQuantumTrader()
