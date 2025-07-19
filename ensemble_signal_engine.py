from simplified_ml_strategy import SimplifiedMLStrategy

class EnsembleSignalEngine:
    def __init__(self, client, quantum_trader, market_analyzer):
        self.client = client
        self.quantum_trader = quantum_trader
        self.market_analyzer = market_analyzer
        self.ml_strategy = SimplifiedMLStrategy()

    def get_signals(self, symbol, weights, min_confidence):
        quantum_signal = self.quantum_trader.evaluate_signal({})
        tech_indicators = self.market_analyzer.compute_indicators(symbol)
        ml_signal, ml_conf, _ = self.ml_strategy.predict_market_direction(self.market_analyzer.get_klines(symbol))

        final_decision = quantum_signal["decision"]
        final_confidence = (weights["quantum"] * quantum_signal["confidence"] +
                            weights["ml"] * ml_conf +
                            weights["technical"] * 0.5) / 100

        return {
            "symbol": symbol,
            "quantum": quantum_signal,
            "ml": {"decision": ml_signal, "confidence": ml_conf},
            "technical": {"decision": "BUY" if tech_indicators["rsi"] < 70 else "SELL", "confidence": 0.5},
            "final": {"decision": final_decision, "confidence": final_confidence},
            "circuit": quantum_signal["circuit"]
        }