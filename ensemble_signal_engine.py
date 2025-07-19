"""
ensemble_signal_engine.py
==========================
Combines Quantum, ML, and Technical signals into an ensemble strategy decision.
"""

from typing import Dict, Any
from quantum_trading_integration import QuantumTrader
from quantum_engine import QuantumAnalyzer
from simplified_ml_strategy import MLStrategy
from market_analyzer import MarketAnalyzer


class EnsembleSignalEngine:
    def __init__(self, client, quantum_trader: QuantumTrader, market_analyzer: MarketAnalyzer):
        self.client = client
        self.quantum_trader = quantum_trader
        self.quantum_analyzer = QuantumAnalyzer()
        self.market_analyzer = market_analyzer
        self.ml_strategy = MLStrategy()

    def get_signals(self, symbol: str, weights: Dict[str, float], min_confidence: float = 0.65) -> Dict[str, Any]:
        """
        Compute ensemble signal for a given trading pair.

        Args:
            symbol (str): Trading pair, e.g., 'BTCUSDT'
            weights (dict): {'quantum': %, 'ml': %, 'technical': %}
            min_confidence (float): Minimum confidence threshold for final signal

        Returns:
            dict: Combined signal details
        """

        # Fetch technical indicators
        rsi = self.market_analyzer.get_latest_rsi(symbol)
        momentum = self.market_analyzer.get_latest_momentum(symbol)
        volatility = self.market_analyzer.get_volatility(symbol)

        # Quantum signal
        quantum_signal = self.quantum_trader.evaluate_signal({
            "rsi": rsi,
            "momentum": momentum,
            "price_volatility": volatility
        })

        # ML signal
        ml_signal = self.ml_strategy.predict(symbol)

        # Technical decision
        tech_decision, tech_conf = self._technical_decision(rsi, momentum)

        # Normalize weights
        total_weight = weights['quantum'] + weights['ml'] + weights['technical']
        q_w = weights['quantum'] / total_weight
        m_w = weights['ml'] / total_weight
        t_w = weights['technical'] / total_weight

        # Compute final score
        final_conf = (
            quantum_signal["confidence"] * q_w +
            ml_signal["confidence"] * m_w +
            tech_conf * t_w
        )
        final_decision = "BUY" if final_conf >= min_confidence else "SELL"

        return {
            "symbol": symbol,
            "quantum": {"decision": quantum_signal["decision"], "confidence": quantum_signal["confidence"]},
            "ml": {"decision": ml_signal["decision"], "confidence": ml_signal["confidence"]},
            "technical": {"decision": tech_decision, "confidence": tech_conf},
            "final": {"decision": final_decision, "confidence": round(final_conf, 2)},
            "circuit": quantum_signal.get("circuit", "")
        }

    def _technical_decision(self, rsi: float, momentum: float) -> (str, float):
        """
        Simple RSI & Momentum based decision.
        """
        if rsi < 30 and momentum > 0:
            return "BUY", 0.8
        elif rsi > 70 and momentum < 0:
            return "SELL", 0.8
        else:
            return "HOLD", 0.5