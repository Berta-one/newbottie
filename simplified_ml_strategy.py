"""
simplified_ml_strategy.py
===========================
Lightweight heuristic-based ML-like strategy for signal generation.
Uses technical indicators with weighted scoring.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, List

class SimplifiedMLStrategy:
    def __init__(self):
        self.feature_weights = {
            'momentum': 0.30,
            'rsi': 0.20,
            'volume': 0.15,
            'bollinger': 0.15,
            'trend': 0.20
        }
        self.prediction_history = []
        self.performance_metrics = {'accuracy': 0.0, 'total_predictions': 0, 'correct_predictions': 0}

    def predict_market_direction(self, klines: List[List]) -> Tuple[str, float, Dict]:
        """
        :param klines: List of OHLCV data from Binance (or mock)
        :return: (signal, confidence, distribution)
        """
        if len(klines) < 30:
            return "HOLD", 0.5, {'buy': 0.33, 'sell': 0.33, 'hold': 0.34}

        df = self._klines_to_dataframe(klines)
        features = self._extract_features(df)

        # Weighted scoring
        bullish_score = bearish_score = 0
        bullish_score += features['momentum_score'] * self.feature_weights['momentum']
        bullish_score += features['rsi_score'] * self.feature_weights['rsi']
        bullish_score += features['volume_score'] * self.feature_weights['volume']
        bullish_score += features['bollinger_score'] * self.feature_weights['bollinger']
        bullish_score += features['trend_score'] * self.feature_weights['trend']

        bearish_score = 1 - bullish_score
        hold_score = max(0.1, 1 - (bullish_score + bearish_score))

        total = bullish_score + bearish_score + hold_score
        buy_prob = bullish_score / total
        sell_prob = bearish_score / total
        hold_prob = hold_score / total

        if buy_prob > 0.6:
            signal = "BUY"
            confidence = buy_prob
        elif sell_prob > 0.6:
            signal = "SELL"
            confidence = sell_prob
        else:
            signal = "HOLD"
            confidence = max(buy_prob, sell_prob)

        return signal, confidence, {'buy': round(buy_prob, 3), 'sell': round(sell_prob, 3), 'hold': round(hold_prob, 3)}

    def _klines_to_dataframe(self, klines):
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'ct', 'qv', 'trades', 'tb_base', 'tb_quote', 'ignore'])
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df

    def _extract_features(self, df):
        close = df['close'].values
        vol = df['volume'].values
        rsi = self._rsi(close)
        upper, lower = self._bollinger(close)

        momentum_score = (close[-1] - close[-10]) / close[-10] if len(close) > 10 else 0
        rsi_score = 1 if rsi < 30 else (0 if rsi > 70 else 0.5)
        volume_score = 1 if vol[-1] > np.mean(vol[-10:]) else 0
        bollinger_score = 1 if close[-1] <= lower else (0 if close[-1] >= upper else 0.5)
        trend_score = 1 if close[-1] > np.mean(close[-20:]) else 0

        return {
            'momentum_score': momentum_score,
            'rsi_score': rsi_score,
            'volume_score': volume_score,
            'bollinger_score': bollinger_score,
            'trend_score': trend_score
        }

    def _rsi(self, prices, period=14):
        deltas = np.diff(prices)
        gains = deltas[deltas > 0].sum() / period
        losses = -deltas[deltas < 0].sum() / period
        rs = gains / (losses + 1e-6)
        return 100 - (100 / (1 + rs))

    def _bollinger(self, prices, period=20):
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        return sma + (2 * std), sma - (2 * std)