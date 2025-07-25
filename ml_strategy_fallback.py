 -*- coding: utf-8 -*-
"""
ml_strategy_fallback.py
======================
Fallback ML strategy when scikit-learn is unavailable
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple


class MLEnhancedStrategy:
    """Fallback ML strategy using statistical methods"""

    def __init__(self):
        self.trained = False
        print("ML using statistical simulation (scikit-learn unavailable)")

    def extract_ml_features(self, klines):
        """Extract features using pandas only"""
        if len(klines) < 120:
            return None

        df = pd.DataFrame(
            klines,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_volume",
                "trades",
                "taker_buy_base",
                "taker_buy_quote",
                "ignore",
            ],
        )
        df = df.astype(
            {
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float,
            }
        )

        # Calculate features
        current_price = df["close"].iloc[-1]
        price_2h_ago = df["close"].iloc[0]
        price_change_2h = ((current_price - price_2h_ago) / price_2h_ago) * 100

        volume_ratio = df["volume"].iloc[-1] / df["volume"].mean()
        volatility = df["close"].pct_change().std() * 100

        # Simple RSI calculation
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1]))

        sma_5 = df["close"].rolling(5).mean().iloc[-1]
        sma_20 = df["close"].rolling(20).mean().iloc[-1]
        sma_ratio = sma_5 / sma_20 if sma_20 > 0 else 1

        return {
            "price_change_2h": price_change_2h,
            "volume_ratio": volume_ratio,
            "volatility": volatility,
            "rsi": rsi,
            "sma_5_20_ratio": sma_ratio,
            "price_momentum": price_change_2h / 10,
        }

    def get_ml_prediction(self, klines) -> Tuple[str, float]:
        """Generate ML-like prediction using statistical methods"""
        features = self.extract_ml_features(klines)
        if not features:
            return "HOLD", 0.5

        score = 0
        confidence_factors = []

        # RSI signals
        if features["rsi"] < 30:
            score += 0.3
            confidence_factors.append(0.7)
        elif features["rsi"] > 70:
            score -= 0.3
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.4)

        # Price momentum
        if features["price_change_2h"] > 2:
            score += 0.2
            confidence_factors.append(0.6)
        elif features["price_change_2h"] < -2:
            score -= 0.2
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.3)

        # Volume confirmation
        if features["volume_ratio"] > 1.5:
            score += 0.1
            confidence_factors.append(0.5)
        else:
            confidence_factors.append(0.3)

        # Moving average trend
        if features["sma_5_20_ratio"] > 1.02:
            score += 0.1
        elif features["sma_5_20_ratio"] < 0.98:
            score -= 0.1

        confidence = np.mean(confidence_factors)

        if score > 0.2:
            signal = "BUY_LONG"
        elif score < -0.2:
            signal = "BUY_SHORT"
        else:
            signal = "HOLD"

        return signal, confidence

    def combine_with_traditional_strategy(
        self, klines, traditional_signal, traditional_confidence
    ):
        """Combine ML prediction with traditional strategy"""
        ml_signal, ml_confidence = self.get_ml_prediction(klines)

        if ml_signal == traditional_signal:
            combined_confidence = (
                ml_confidence * 0.4 + traditional_confidence * 0.6
            ) * 1.1
            final_signal = ml_signal
        else:
            combined_confidence = (
                ml_confidence * 0.4 + traditional_confidence * 0.6
            ) * 0.8
            final_signal = "HOLD" if combined_confidence < 0.6 else traditional_signal

        return final_signal, min(1.0, combined_confidence)

