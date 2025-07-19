"""
Simplified ML Strategy
Lightweight scoring model using technical features (momentum, volume, volatility, RSI).
"""

import numpy as np

class MLStrategy:
    def predict(self, symbol):
        # Dummy implementation
        # Real version should fetch historical data, calculate features
        momentum = np.random.uniform(-0.03, 0.03)
        volatility = np.random.uniform(0.01, 0.05)
        confidence = abs(momentum) + (0.5 - volatility)
        confidence = max(0.5, min(confidence, 0.95))

        if momentum > 0.01:
            signal = "BUY"
        elif momentum < -0.01:
            signal = "SELL"
        else:
            signal = "HOLD"

        return signal, confidence, {"buy": 0.4, "sell": 0.3, "hold": 0.3}