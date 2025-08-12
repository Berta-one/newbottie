# ml/feature_builder.py
import math
from typing import List

def pct_change(series: List[float], n: int) -> float:
    if len(series) < n + 1:
        return 0.0
    a, b = series[-1], series[-1 - n]
    return 0.0 if b == 0 else (a - b) / b

def rsi(series: List[float], period: int = 14) -> float:
    if len(series) < period + 1:
        return 50.0
    gains = 0.0
    losses = 0.0
    for i in range(-period, 0):
        ch = series[i] - series[i - 1]
        if ch >= 0:
            gains += ch
        else:
            losses -= ch  # positive number
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def volatility(series: List[float], lookback: int = 20) -> float:
    if len(series) < lookback:
        return 0.0
    window = series[-lookback:]
    mean = sum(window) / lookback
    if mean == 0:
        return 0.0
    var = sum((x - mean) ** 2 for x in window) / max(1, lookback - 1)
    return math.sqrt(var) / mean

def build_features(closes: List[float]) -> list:
    """Return a small, stable feature vector for classification."""
    feats = [
        pct_change(closes, 3),
        pct_change(closes, 8),
        pct_change(closes, 21),
        volatility(closes, 20),
        rsi(closes, 14) / 100.0,  # normalize to [0,1]
    ]
    # clamp extremes to keep model stable
    clamped = []
    for i, v in enumerate(feats):
        if i < 3:  # returns ~[-0.1, 0.1]
            v = max(-0.1, min(0.1, v)) / 0.1
        elif i == 3:  # vol ratio ~[0, 0.2]
            v = max(0.0, min(0.2, v)) / 0.2
        else:  # rsi normalized already
            v = max(0.0, min(1.0, v))
        clamped.append(v)
    return clamped