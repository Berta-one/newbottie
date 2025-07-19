"""
Simplified ML Strategy
=======================
Rule-based predictive engine using technical indicators as ML-like features.
Does not require heavy ML libraries but behaves like an ML inference engine.
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Tuple, List


class MLStrategy:
    def __init__(self):
        # Weighted importance for pseudo-ML scoring
        self.feature_weights = {
            'price_momentum': 0.20,
            'volume_confirmation': 0.15,
            'volatility_adjustment': 0.10,
            'trend_strength': 0.15,
            'mean_reversion': 0.10,
            'support_resistance': 0.10,
            'time_factor': 0.05,
            'market_structure': 0.15
        }
        self.prediction_history = []
        self.performance_metrics = {'accuracy': 0.0, 'total_predictions': 0, 'correct_predictions': 0}

    # -----------------------------
    # Core API
    # -----------------------------
    def predict_market_direction(self, klines, timeframe='1h') -> Tuple[str, float, Dict]:
        """
        Main prediction method. Calculates features and produces pseudo-ML signal.
        Returns: (signal, confidence, distribution)
        """
        features = self.extract_features(klines)
        if features is None:
            return "HOLD", 0.5, {'buy': 0.33, 'sell': 0.33, 'hold': 0.34}

        bullish_score, bearish_score = 0.0, 0.0

        # Momentum factor
        momentum_score = (features['momentum_5'] * 0.4 +
                          features['momentum_10'] * 0.3 +
                          features['momentum_20'] * 0.3)
        if momentum_score > 0.02:
            bullish_score += self.feature_weights['price_momentum']
        elif momentum_score < -0.02:
            bearish_score += self.feature_weights['price_momentum']

        # Volume confirmation
        if features['volume_ratio_5'] > 1.5:
            if momentum_score > 0:
                bullish_score += self.feature_weights['volume_confirmation']
            else:
                bearish_score += self.feature_weights['volume_confirmation']

        # Volatility adjustment (high volatility dampens confidence)
        if features['volatility'] > 0.05:
            bullish_score *= 0.8
            bearish_score *= 0.8

        # Trend alignment
        if features['trend_alignment'] == 1:
            bullish_score += self.feature_weights['trend_strength']
        elif features['trend_alignment'] == -1:
            bearish_score += self.feature_weights['trend_strength']

        # Mean reversion via RSI
        if features['rsi'] < 30:
            bullish_score += self.feature_weights['mean_reversion']
        elif features['rsi'] > 70:
            bearish_score += self.feature_weights['mean_reversion']

        # Support/Resistance influence
        if features['support_distance'] > 0.02:
            bullish_score += self.feature_weights['support_resistance'] * 0.5
        if features['resistance_distance'] > 0.02:
            bearish_score += self.feature_weights['support_resistance'] * 0.5

        # Market structure
        if features['structure_score'] > 0.6:
            bullish_score += self.feature_weights['market_structure']
        elif features['structure_score'] < 0.4:
            bearish_score += self.feature_weights['market_structure']

        # Time session multiplier
        time_multiplier = features['session_score'] * features['weekend_factor']
        bullish_score *= time_multiplier
        bearish_score *= time_multiplier

        # Normalize probabilities
        total_score = bullish_score + bearish_score
        if total_score == 0:
            bullish_prob, bearish_prob = 0.5, 0.5
        else:
            bullish_prob = bullish_score / total_score
            bearish_prob = bearish_score / total_score
        hold_prob = max(0, 1 - bullish_prob - bearish_prob)

        # Decision
        if bullish_prob > 0.6:
            signal, confidence = "BUY_LONG", bullish_prob
        elif bearish_prob > 0.6:
            signal, confidence = "BUY_SHORT", bearish_prob
        else:
            signal, confidence = "HOLD", max(bullish_prob, bearish_prob)

        # Save prediction
        self.prediction_history.append({'timestamp': datetime.now(), 'signal': signal,
                                        'confidence': confidence, 'features': features})
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-1000:]

        return signal, confidence, {'buy': bullish_prob, 'sell': bearish_prob, 'hold': hold_prob}

    # -----------------------------
    # Feature Extraction
    # -----------------------------
    def extract_features(self, klines) -> Dict:
        if len(klines) < 50:
            return None
        df = self._klines_to_dataframe(klines)

        features = {}
        features.update(self._calculate_price_momentum(df))
        features.update(self._calculate_volume_features(df))
        features.update(self._calculate_volatility_features(df))
        features.update(self._calculate_trend_features(df))
        features.update(self._calculate_mean_reversion_features(df))
        features.update(self._calculate_support_resistance_features(df))
        features.update(self._calculate_time_features())
        features.update(self._calculate_market_structure_features(df))
        return features

    def _klines_to_dataframe(self, klines) -> pd.DataFrame:
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        return df.astype({'open': float, 'high': float, 'low': float,
                          'close': float, 'volume': float, 'timestamp': int})

    # -----------------------------
    # Feature Calculations
    # -----------------------------
    def _calculate_price_momentum(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        return {
            'momentum_5': (close[-1] - close[-5]) / close[-5] if len(close) >= 5 else 0,
            'momentum_10': (close[-1] - close[-10]) / close[-10] if len(close) >= 10 else 0,
            'momentum_20': (close[-1] - close[-20]) / close[-20] if len(close) >= 20 else 0
        }

    def _calculate_volume_features(self, df: pd.DataFrame) -> Dict:
        volume = df['volume'].values
        vol_ma_5 = np.mean(volume[-5:]) if len(volume) >= 5 else volume[-1]
        vol_ma_20 = np.mean(volume[-20:]) if len(volume) >= 20 else vol_ma_5
        current_vol = volume[-1]
        return {
            'volume_ratio_5': current_vol / vol_ma_5 if vol_ma_5 else 1,
            'volume_ratio_20': current_vol / vol_ma_20 if vol_ma_20 else 1,
            'volume_trend': np.polyfit(range(5), volume[-5:], 1)[0] if len(volume) >= 5 else 0
        }

    def _calculate_volatility_features(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        returns = np.diff(close) / close[:-1] if len(close) > 1 else [0]
        return {'volatility': np.std(returns)}

    def _calculate_trend_features(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        if len(close) < 50:
            return {'trend_alignment': 0}
        sma_10 = np.mean(close[-10:])
        sma_20 = np.mean(close[-20:])
        sma_50 = np.mean(close[-50:])
        if sma_10 > sma_20 > sma_50:
            trend_alignment = 1
        elif sma_10 < sma_20 < sma_50:
            trend_alignment = -1
        else:
            trend_alignment = 0
        return {'trend_alignment': trend_alignment}

    def _calculate_mean_reversion_features(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        if len(close) < 15:
            return {'rsi': 50}
        deltas = np.diff(close[-15:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))
        return {'rsi': rsi}

    def _calculate_support_resistance_features(self, df: pd.DataFrame) -> Dict:
        high, low, close = df['high'].values, df['low'].values, df['close'].values
        recent_high = np.max(high[-20:]) if len(high) >= 20 else high[-1]
        recent_low = np.min(low[-20:]) if len(low) >= 20 else low[-1]
        current_price = close[-1]
        return {
            'resistance_distance': (recent_high - current_price) / current_price,
            'support_distance': (current_price - recent_low) / current_price
        }

    def _calculate_time_features(self) -> Dict:
        hour = datetime.now().hour
        if 6 <= hour <= 10:
            session_score = 0.8
        elif 13 <= hour <= 17:
            session_score = 1.0
        elif 20 <= hour <= 24:
            session_score = 0.7
        else:
            session_score = 0.3
        weekend_factor = 0.5 if datetime.now().weekday() >= 5 else 1.0
        return {'session_score': session_score, 'weekend_factor': weekend_factor}

    def _calculate_market_structure_features(self, df: pd.DataFrame) -> Dict:
        high, low = df['high'].values, df['low'].values
        if len(high) < 10:
            return {'structure_score': 0.5}
        higher_highs = sum(1 for i in range(1, 10) if high[-i] > high[-i - 1])
        higher_lows = sum(1 for i in range(1, 10) if low[-i] > low[-i - 1])
        return {'structure_score': (higher_highs + higher_lows) / 18}

    # Performance Tracking
    def update_performance(self, actual: str, predicted: str):
        self.performance_metrics['total_predictions'] += 1
        if actual == predicted:
            self.performance_metrics['correct_predictions'] += 1
        self.performance_metrics['accuracy'] = self.performance_metrics['correct_predictions'] / self.performance_metrics['total_predictions']

    def get_performance_metrics(self) -> Dict:
        return self.performance_metrics.copy()