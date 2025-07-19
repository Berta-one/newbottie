"""
Ensemble Signal Engine
Combines Quantum, ML, and Technical analysis for weighted signals.
"""

class EnsembleSignalEngine:
    def __init__(self, client, quantum_trader, market_analyzer):
        self.client = client
        self.quantum_trader = quantum_trader
        self.market_analyzer = market_analyzer

    def get_signals(self, symbol, weights, min_confidence=0.65):
        # Quantum signal
        quantum_signal = self.quantum_trader.evaluate_signal({"symbol": symbol})
        quantum_decision = quantum_signal["decision"]
        quantum_conf = quantum_signal["confidence"]

        # ML signal
        ml_signal, ml_conf, _ = self.market_analyzer.ml_strategy.predict(symbol)
        
        # Technical signal
        tech_signal, tech_conf = self.market_analyzer.technical_signal(symbol)

        # Weighted ensemble
        final_score = (
            quantum_conf * weights["quantum"] +
            ml_conf * weights["ml"] +
            tech_conf * weights["technical"]
        ) / 100
        final_decision = "BUY" if final_score > 0.55 else "SELL" if final_score < 0.45 else "HOLD"

        return {
            "symbol": symbol,
            "quantum": {"decision": quantum_decision, "confidence": quantum_conf},
            "ml": {"decision": ml_signal, "confidence": ml_conf},
            "technical": {"decision": tech_signal, "confidence": tech_conf},
            "final": {"decision": final_decision, "confidence": final_score},
            "circuit": quantum_signal["circuit"]
        }