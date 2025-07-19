"""
Ensemble Signal Engine
========================
Combines Quantum, ML, and Technical signals with weighted scoring.
"""

from typing import Dict, Any
from quantum_trading_integration import QuantumTrader
from market_analyzer import MarketAnalyzer
from simplified_ml_strategy import MLStrategy


class EnsembleSignalEngine:
    def __init__(self, client, quantum_trader: QuantumTrader, market_analyzer: MarketAnalyzer):
        self.client = client
        self.quantum_trader = quantum_trader
        self.market_analyzer = market_analyzer
        self.ml_strategy = MLStrategy()

    def get_signals(self, symbol: str, weights: Dict[str, float], min_confidence: float = 0.65) -> Dict[str, Any]:
        """
        Get combined signal using ensemble from Quantum, ML, and Technical strategies.
        """
        # Quantum signal
        quantum_signal = self.quantum_trader.evaluate_signal({
            "rsi": self.market_analyzer.get_latest_rsi(symbol),
            "momentum": self.market_analyzer.get_latest_momentum(symbol),
            "price_volatility": self.market_analyzer.get_volatility(symbol)
        })

        # ML signal
        klines = self.client.get_klines(symbol=symbol, interval='1h', limit=100)
        ml_signal, ml_confidence, ml_distribution = self.ml_strategy.predict_market_direction(klines)

        # Technical signal (simplified: using RSI & Momentum only)
        tech_rsi = self.market_analyzer.get_latest_rsi(symbol)
        tech_decision = "BUY" if tech_rsi < 30 else "SELL" if tech_rsi > 70 else "HOLD"
        tech_confidence = abs((50 - tech_rsi) / 50)  # normalize to [0, 1]

        # Combine weighted score
        combined_score = (
            quantum_signal["confidence"] * weights["quantum"] +
            ml_confidence * weights["ml"] +
            tech_confidence * weights["technical"]
        ) / sum(weights.values())

        # Final decision
        decision = "HOLD"
        if combined_score > min_confidence:
            if quantum_signal["decision"] == "BUY" or ml_signal.startswith("BUY") or tech_decision == "BUY":
                decision = "BUY"
            elif quantum_signal["decision"] == "SELL" or ml_signal == "BUY_SHORT" or tech_decision == "SELL":
                decision = "SELL"

        return {
            "symbol": symbol,
            "quantum": {
                "decision": quantum_signal["decision"],
                "confidence": quantum_signal["confidence"],
                "distribution": quantum_signal["distribution"]
            },
            "ml": {
                "decision": ml_signal,
                "confidence": ml_confidence,
                "distribution": ml_distribution
            },
            "technical": {
                "decision": tech_decision,
                "confidence": tech_confidence
            },
            "final": {
                "decision": decision,
                "confidence": combined_score
            },
            "circuit": quantum_signal["circuit"]
        }