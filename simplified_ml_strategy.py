
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple


class SimplifiedMLStrategy:
    """Simplified ML-inspired strategy that doesn't require sklearn. Uses ensemble of technical indicators with weighted scoring."""
    def __init__(self):
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
        self.performance_metrics = {
            'accuracy': 0.0,
            'total_predictions': 0,
            'correct_predictions': 0
        }

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
        return df.astype({
            'open': float, 'high': float, 'low': float,
            'close': float, 'volume': float, 'timestamp': int
        })

    def _calculate_price_momentum(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        momentum_5 = (close[-1] - close[-5]) / close[-5] if len(close) >= 5 else 0
        momentum_10 = (close[-1] - close[-10]) / close[-10] if len(close) >= 10 else 0
        momentum_20 = (close[-1] - close[-20]) / close[-20] if len(close) >= 20 else 0
        roc = (close[-1] - close[-10]) / close[-10] if len(close) >= 10 else 0
        acceleration = (close[-1] - close[-2]) - (close[-2] - close[-3]) if len(close) >= 3 else 0
        return {
            'momentum_5': momentum_5,
            'momentum_10': momentum_10,
            'momentum_20': momentum_20,
            'rate_of_change': roc,
            'acceleration': acceleration
        }

    def _calculate_volume_features(self, df: pd.DataFrame) -> Dict:
        volume = df['volume'].values
        vol_ma_5 = np.mean(volume[-5:]) if len(volume) >= 5 else volume[-1]
        vol_ma_20 = np.mean(volume[-20:]) if len(volume) >= 20 else vol_ma_5
        current_vol = volume[-1]
        vol_ratio_5 = current_vol / vol_ma_5 if vol_ma_5 > 0 else 1
        vol_ratio_20 = current_vol / vol_ma_20 if vol_ma_20 > 0 else 1
        vol_trend = np.polyfit(range(5), volume[-5:], 1)[0] if len(volume) >= 5 else 0
        close = df['close'].values
        obv_trend = 0
        if len(close) >= 10:
            obv_values = []
            obv = 0
            for i in range(-10, 0):
                if i == -10:
                    obv_values.append(obv)
                else:
                    if close[i] > close[i-1]:
                        obv += volume[i]
                    elif close[i] < close[i-1]:
                        obv -= volume[i]
                    obv_values.append(obv)
            if len(obv_values) >= 3:
                obv_trend = np.polyfit(range(len(obv_values)), obv_values, 1)[0]
        return {
            'volume_ratio_5': vol_ratio_5,
            'volume_ratio_20': vol_ratio_20,
            'volume_trend': vol_trend,
            'obv_trend': obv_trend
        }

    def _calculate_volatility_features(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        if len(close) >= 20:
            returns = np.diff(close) / close[:-1]
            volatility = np.std(returns)
        else:
            volatility = 0
        if len(high) >= 2:
            tr_values = []
            for i in range(1, len(high)):
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
                tr_values.append(tr)
            atr = np.mean(tr_values[-14:]) if len(tr_values) >= 14 else np.mean(tr_values)
            atr_pct = atr / close[-1] if close[-1] > 0 else 0
        else:
            atr_pct = 0
        if len(close) >= 20:
            sma_20 = np.mean(close[-20:])
            std_20 = np.std(close[-20:])
            upper_band = sma_20 + (2 * std_20)
            lower_band = sma_20 - (2 * std_20)
            bb_position = (close[-1] - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
        else:
            bb_position = 0.5
        return {
            'volatility': volatility,
            'atr_percentage': atr_pct,
            'bb_position': bb_position
        }

    def _calculate_trend_features(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        if len(close) >= 50:
            sma_10 = np.mean(close[-10:])
            sma_20 = np.mean(close[-20:])
            sma_50 = np.mean(close[-50:])
            if sma_10 > sma_20 > sma_50:
                trend_alignment = 1
            elif sma_10 < sma_20 < sma_50:
                trend_alignment = -1
            else:
                trend_alignment = 0
        else:
            trend_alignment = 0
        current_price = close[-1]
        if len(close) >= 20:
            sma_20 = np.mean(close[-20:])
            price_vs_ma = (current_price - sma_20) / sma_20
        else:
            price_vs_ma = 0
        if len(close) >= 20:
            x = np.arange(20)
            y = close[-20:]
            trend_slope = np.polyfit(x, y, 1)[0]
            trend_strength = abs(trend_slope) / current_price
        else:
            trend_strength = 0
        return {
            'trend_alignment': trend_alignment,
            'price_vs_ma': price_vs_ma,
            'trend_strength': trend_strength
        }

    def _calculate_mean_reversion_features(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        if len(close) >= 15:
            deltas = np.diff(close[-15:])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 50
        if len(close) >= 20:
            mean_20 = np.mean(close[-20:])
            distance_from_mean = (close[-1] - mean_20) / mean_20
        else:
            distance_from_mean = 0
        if len(close) >= 20:
            std_20 = np.std(close[-20:])
            if std_20 > 0:
                z_score = (close[-1] - mean_20) / std_20
            else:
                z_score = 0
        else:
            z_score = 0
        return {
            'rsi': rsi,
            'distance_from_mean': distance_from_mean,
            'z_score': z_score
        }

    def _calculate_support_resistance_features(self, df: pd.DataFrame) -> Dict:
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        current_price = close[-1]
        if len(high) >= 20:
            recent_high = np.max(high[-20:])
            recent_low = np.min(low[-20:])
            resistance_distance = (recent_high - current_price) / current_price
            support_distance = (current_price - recent_low) / current_price
        else:
            resistance_distance = 0
            support_distance = 0
        if len(high) >= 3:
            pivot = (high[-2] + low[-2] + close[-2]) / 3
            pivot_distance = (current_price - pivot) / pivot
        else:
            pivot_distance = 0
        return {
            'resistance_distance': resistance_distance,
            'support_distance': support_distance,
            'pivot_distance': pivot_distance
        }

    def _calculate_time_features(self) -> Dict:
        current_time = datetime.now()
        hour = current_time.hour
        if 6 <= hour <= 10:
            session_score = 0.8
        elif 13 <= hour <= 17:
            session_score = 1.0
        elif 20 <= hour <= 24:
            session_score = 0.7
        else:
            session_score = 0.3
        weekday = current_time.weekday()
        weekend_factor = 0.5 if weekday >= 5 else 1.0
        return {
            'session_score': session_score,
            'weekend_factor': weekend_factor
        }

    def _calculate_market_structure_features(self, df: pd.DataFrame) -> Dict:
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        if len(high) >= 10:
            recent_highs = high[-10:]
            recent_lows = low[-10:]
            higher_highs = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] > recent_highs[i-1])
            higher_lows = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] > recent_lows[i-1])
            structure_score = (higher_highs + higher_lows) / 18
        else:
            structure_score = 0.5
        if len(close) >= 3:
            open_price = float(df['open'].iloc[-1])
            body_size = abs(close[-1] - open_price)
            total_range = high[-1] - low[-1]
            doji_factor = 1 - (body_size / total_range) if total_range > 0 else 0
        else:
        return {
            'structure_score': structure_score,
            'doji_factor': doji_factor
        }

    def predict_market_direction(self, klines, timeframe='1h') -> Tuple[str, float, Dict]:
        features = self.extract_features(klines)
        if features is None:
            return "HOLD", 0.5, {'buy': 0.33, 'sell': 0.33, 'hold': 0.34}
        bullish_score = 0
        bearish_score = 0
        momentum_score = (features['momentum_5'] * 0.4 +
                         features['momentum_10'] * 0.3 +
                         features['momentum_20'] * 0.3)
        if momentum_score > 0.02:
            bullish_score += self.feature_weights['price_momentum']
        elif momentum_score < -0.02:
            bearish_score += self.feature_weights['price_momentum']
        if features['volume_ratio_5'] > 1.5 and features['volume_trend'] > 0:
            if momentum_score > 0:
                bullish_score += self.feature_weights['volume_confirmation']
            else:
                bearish_score += self.feature_weights['volume_confirmation']
        if features['volatility'] > 0.05:
            bullish_score *= 0.8
            bearish_score *= 0.8
        if features['trend_alignment'] == 1:
            bullish_score += self.feature_weights['trend_strength']
        elif features['trend_alignment'] == -1:
            bearish_score += self.feature_weights['trend_strength']
        rsi = features['rsi']
        if rsi < 30:
            bullish_score += self.feature_weights['mean_reversion']
        elif rsi > 70:
            bearish_score += self.feature_weights['mean_reversion']
        if features['support_distance'] > 0.02:
            bullish_score += self.feature_weights['support_resistance'] * 0.5
        if features['resistance_distance'] > 0.02:
            bearish_score += self.feature_weights['support_resistance'] * 0.5
        time_multiplier = features['session_score'] * features['weekend_factor']
        bullish_score *= time_multiplier
        bearish_score *= time_multiplier
        if features['structure_score'] > 0.6:
            bullish_score += self.feature_weights['market_structure']
        elif features['structure_score'] < 0.4:
            bearish_score += self.feature_weights['market_structure']
        total_score = bullish_score + bearish_score
        if total_score > 0:
            bullish_prob = bullish_score / total_score
            bearish_prob = bearish_score / total_score
        else:
            bullish_prob = 0.5
            bearish_prob = 0.5
        hold_prob = 1 - bullish_prob - bearish_prob
        if bullish_prob > 0.6:
            signal = "BUY_LONG"
            confidence = bullish_prob
        elif bearish_prob > 0.6:
            signal = "BUY_SHORT"
            confidence = bearish_prob
        else:
            signal = "HOLD"
            confidence = max(bullish_prob, bearish_prob)
        self.prediction_history.append({
            'timestamp': datetime.now(),
            'signal': signal,
            'confidence': confidence,
            'features': features
        })
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-1000:]
        return signal, confidence, {
            'buy': bullish_prob,
            'sell': bearish_prob,
            'hold': hold_prob
        }

    def get_feature_importance(self) -> List[Tuple[str, float]]:
        return list(self.feature_weights.items())

    def update_performance(self, actual_result: str, predicted_signal: str):
        self.performance_metrics['total_predictions'] += 1
        if actual_result == predicted_signal:
            self.performance_metrics['correct_predictions'] += 1
        if self.performance_metrics['total_predictions'] > 0:
            self.performance_metrics['accuracy'] = (
                self.performance_metrics['correct_predictions'] /
                self.performance_metrics['total_predictions']
            )

    def get_performance_metrics(self) -> Dict:


    def _calculate_price_momentum(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        momentum_5 = (close[-1] - close[-5]) / close[-5] if len(close) >= 5 else 0
        momentum_10 = (close[-1] - close[-10]) / close[-10] if len(close) >= 10 else 0
        momentum_20 = (close[-1] - close[-20]) / close[-20] if len(close) >= 20 else 0
        roc = (close[-1] - close[-10]) / close[-10] if len(close) >= 10 else 0
        acceleration = (close[-1] - close[-2]) - (close[-2] - close[-3]) if len(close) >= 3 else 0
        return {
            'momentum_5': momentum_5,
            'momentum_10': momentum_10,
            'momentum_20': momentum_20,
            'rate_of_change': roc,
            'acceleration': acceleration
        }

    def _calculate_volume_features(self, df: pd.DataFrame) -> Dict:
        volume = df['volume'].values
        vol_ma_5 = np.mean(volume[-5:]) if len(volume) >= 5 else volume[-1]
        vol_ma_20 = np.mean(volume[-20:]) if len(volume) >= 20 else vol_ma_5
        current_vol = volume[-1]
        vol_ratio_5 = current_vol / vol_ma_5 if vol_ma_5 > 0 else 1
        vol_ratio_20 = current_vol / vol_ma_20 if vol_ma_20 > 0 else 1
        vol_trend = np.polyfit(range(5), volume[-5:], 1)[0] if len(volume) >= 5 else 0
        close = df['close'].values
        obv_trend = 0
        if len(close) >= 10:
            obv_values = []
            obv = 0
            for i in range(-10, 0):
                if i == -10:
                    obv_values.append(obv)
                else:
                    if close[i] > close[i-1]:
                        obv += volume[i]
                    elif close[i] < close[i-1]:
                        obv -= volume[i]
                    obv_values.append(obv)
            if len(obv_values) >= 3:
                obv_trend = np.polyfit(range(len(obv_values)), obv_values, 1)[0]
        return {
            'volume_ratio_5': vol_ratio_5,
            'volume_ratio_20': vol_ratio_20,
            'volume_trend': vol_trend,
            'obv_trend': obv_trend
        }

    def _calculate_volatility_features(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        if len(close) >= 20:
            returns = np.diff(close) / close[:-1]
            volatility = np.std(returns)
        else:
            volatility = 0
        if len(high) >= 2:
            tr_values = []
            for i in range(1, len(high)):
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
                tr_values.append(tr)
            atr = np.mean(tr_values[-14:]) if len(tr_values) >= 14 else np.mean(tr_values)
            atr_pct = atr / close[-1] if close[-1] > 0 else 0
        else:
            atr_pct = 0
        if len(close) >= 20:
            sma_20 = np.mean(close[-20:])
            std_20 = np.std(close[-20:])
            upper_band = sma_20 + (2 * std_20)
            lower_band = sma_20 - (2 * std_20)
            bb_position = (close[-1] - lower_band) / (upper_band - lower_band) if upper_band != lower_band else 0.5
        else:
            bb_position = 0.5
        return {
            'volatility': volatility,
            'atr_percentage': atr_pct,
            'bb_position': bb_position
        }

    def _calculate_trend_features(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        if len(close) >= 50:
            sma_10 = np.mean(close[-10:])
            sma_20 = np.mean(close[-20:])
            sma_50 = np.mean(close[-50:])
            if sma_10 > sma_20 > sma_50:
                trend_alignment = 1
            elif sma_10 < sma_20 < sma_50:
                trend_alignment = -1
            else:
                trend_alignment = 0
        else:
            trend_alignment = 0
        current_price = close[-1]
        if len(close) >= 20:
            sma_20 = np.mean(close[-20:])
            price_vs_ma = (current_price - sma_20) / sma_20
        else:
            price_vs_ma = 0
        if len(close) >= 20:
            x = np.arange(20)
            y = close[-20:]
            trend_slope = np.polyfit(x, y, 1)[0]
            trend_strength = abs(trend_slope) / current_price
        else:
            trend_strength = 0
        return {
            'trend_alignment': trend_alignment,
            'price_vs_ma': price_vs_ma,
            'trend_strength': trend_strength
        }

    def _calculate_mean_reversion_features(self, df: pd.DataFrame) -> Dict:
        close = df['close'].values
        if len(close) >= 15:
            deltas = np.diff(close[-15:])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 50
        if len(close) >= 20:
            mean_20 = np.mean(close[-20:])
            distance_from_mean = (close[-1] - mean_20) / mean_20
        else:
            distance_from_mean = 0
        if len(close) >= 20:
            std_20 = np.std(close[-20:])
            if std_20 > 0:
                z_score = (close[-1] - mean_20) / std_20
            else:
                z_score = 0
        else:
            z_score = 0
        return {
            'rsi': rsi,
            'distance_from_mean': distance_from_mean,
            'z_score': z_score
        }

    def _calculate_support_resistance_features(self, df: pd.DataFrame) -> Dict:
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        current_price = close[-1]
        if len(high) >= 20:
            recent_high = np.max(high[-20:])
            recent_low = np.min(low[-20:])
            resistance_distance = (recent_high - current_price) / current_price
            support_distance = (current_price - recent_low) / current_price
        else:
            resistance_distance = 0
            support_distance = 0
        if len(high) >= 3:
            pivot = (high[-2] + low[-2] + close[-2]) / 3
            pivot_distance = (current_price - pivot) / pivot
        else:
            pivot_distance = 0
        return {
            'resistance_distance': resistance_distance,
            'support_distance': support_distance,
            'pivot_distance': pivot_distance
        }

    def _calculate_time_features(self) -> Dict:
        current_time = datetime.now()
        hour = current_time.hour
        if 6 <= hour <= 10:
            session_score = 0.8
        elif 13 <= hour <= 17:
            session_score = 1.0
        elif 20 <= hour <= 24:
            session_score = 0.7
        else:
            session_score = 0.3
        weekday = current_time.weekday()
        weekend_factor = 0.5 if weekday >= 5 else 1.0
        return {
            'session_score': session_score,
            'weekend_factor': weekend_factor
        }

    def _calculate_market_structure_features(self, df: pd.DataFrame) -> Dict:
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        if len(high) >= 10:
            recent_highs = high[-10:]
            recent_lows = low[-10:]
            higher_highs = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] > recent_highs[i-1])
            higher_lows = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] > recent_lows[i-1])
            structure_score = (higher_highs + higher_lows) / 18
        else:
            structure_score = 0.5
        if len(close) >= 3:
            open_price = float(df['open'].iloc[-1])
            body_size = abs(close[-1] - open_price)
            total_range = high[-1] - low[-1]
            doji_factor = 1 - (body_size / total_range) if total_range > 0 else 0
        else:
            doji_factor = 0
        return {
            'structure_score': structure_score,
            'doji_factor': doji_factor
        }

    def predict_market_direction(self, klines, timeframe='1h') -> Tuple[str, float, Dict]:
        features = self.extract_features(klines)
        if features is None:
            return "HOLD", 0.5, {'buy': 0.33, 'sell': 0.33, 'hold': 0.34}
        bullish_score = 0
        bearish_score = 0
        momentum_score = (features['momentum_5'] * 0.4 +
                         features['momentum_10'] * 0.3 +
                         features['momentum_20'] * 0.3)
        if momentum_score > 0.02:
            bullish_score += self.feature_weights['price_momentum']
        elif momentum_score < -0.02:
            bearish_score += self.feature_weights['price_momentum']
        if features['volume_ratio_5'] > 1.5 and features['volume_trend'] > 0:
            if momentum_score > 0:
                bullish_score += self.feature_weights['volume_confirmation']
            else:
                bearish_score += self.feature_weights['volume_confirmation']
        if features['volatility'] > 0.05:
            bullish_score *= 0.8
            bearish_score *= 0.8
        if features['trend_alignment'] == 1:
            bullish_score += self.feature_weights['trend_strength']
        elif features['trend_alignment'] == -1:
            bearish_score += self.feature_weights['trend_strength']
        rsi = features['rsi']
        if rsi < 30:
            bullish_score += self.feature_weights['mean_reversion']
        elif rsi > 70:
            bearish_score += self.feature_weights['mean_reversion']
        if features['support_distance'] > 0.02:
            bullish_score += self.feature_weights['support_resistance'] * 0.5
        if features['resistance_distance'] > 0.02:
            bearish_score += self.feature_weights['support_resistance'] * 0.5
        time_multiplier = features['session_score'] * features['weekend_factor']
        bullish_score *= time_multiplier
        bearish_score *= time_multiplier
        if features['structure_score'] > 0.6:
            bullish_score += self.feature_weights['market_structure']
        elif features['structure_score'] < 0.4:
            bearish_score += self.feature_weights['market_structure']
        total_score = bullish_score + bearish_score
        if total_score > 0:
            bullish_prob = bullish_score / total_score
            bearish_prob = bearish_score / total_score
        else:
            bullish_prob = 0.5
            bearish_prob = 0.5
        hold_prob = 1 - bullish_prob - bearish_prob
        if bullish_prob > 0.6:
            signal = "BUY_LONG"
            confidence = bullish_prob
        elif bearish_prob > 0.6:
            signal = "BUY_SHORT"
            confidence = bearish_prob
        else:
            signal = "HOLD"
            confidence = max(bullish_prob, bearish_prob)
        self.prediction_history.append({
            'timestamp': datetime.now(),
            'signal': signal,
            'confidence': confidence,
            'features': features
        })
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-1000:]
        return signal, confidence, {
            'buy': bullish_prob,
            'sell': bearish_prob,
            'hold': hold_prob
        }

    def get_feature_importance(self) -> List[Tuple[str, float]]:
        return list(self.feature_weights.items())

    def update_performance(self, actual_result: str, predicted_signal: str):
        self.performance_metrics['total_predictions'] += 1
        if actual_result == predicted_signal:
            self.performance_metrics['correct_predictions'] += 1
        if self.performance_metrics['total_predictions'] > 0:
            self.performance_metrics['accuracy'] = (
                self.performance_metrics['correct_predictions'] /
                self.performance_metrics['total_predictions']
            )

    def get_performance_metrics(self) -> Dict:
        return self.performance_metrics.copy()
