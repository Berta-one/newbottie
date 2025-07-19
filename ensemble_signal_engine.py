"""
ensemble_signal_engine.py
===========================
Combines Quantum, ML, and Technical strategies into a unified decision.
"""

from typing import Dict
from simplified_ml_strategy import SimplifiedMLStrategy

class EnsembleSignalEngine:
    def __init__(self, client, quantum_trader, market_analyzer):
        self.client = client
        self.quantum_trader = quantum_trader
        self.market_analyzer = market_analyzer
        self.ml_strategy = SimplifiedMLStrategy()

    def get_signals(self, symbol: str, weights: Dict, min_confidence: float) -> Dict:
        # Quantum
        q_signal = self.quantum_trader.evaluate_signal({
            "rsi": self.market_analyzer.get_latest_rsi(symbol),
            "momentum": self.market_analyzer.get_latest_momentum(symbol),
            "price_volatility": self.market_analyzer.get_volatility(symbol)
        })

        # ML
        klines = self.client.get_klines(symbol=symbol, interval="1h", limit=50)
        ml_signal, ml_conf, ml_dist = self.ml_strategy.predict_market_direction(klines)

        # Technical (basic heuristic)
        tech_signal = "BUY" if q_signal['confidence'] > 0.55 else "SELL"

        final_score = (
            q_signal['confidence'] * (weights['quantum'] / 100) +
            ml_conf * (weights['ml'] / 100) +
            (0.6 if tech_signal == "BUY" else 0.4) * (weights['technical'] / 100)
        )

        final_decision = "BUY" if final_score > 0.55 else ("SELL" if final_score < 0.45 else "HOLD")

        return {
            "symbol": symbol,
            "quantum": {"decision": q_signal['decision'], "confidence": q_signal['confidence']},
            "ml": {"decision": ml_signal, "confidence": ml_conf},
            "technical": {"decision": tech_signal, "confidence": 0.6 if tech_signal == "BUY" else 0.4},
            "final": {"decision": final_decision, "confidence": round(final_score, 3)},
            "distribution": {"buy": final_score, "sell": 1 - final_score, "hold": 0.1},
            "circuit": q_signal.get("circuit", "")
        }