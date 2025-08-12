# ml/feature_builder.py
import math
from typing import List, Dict, Any, Optional

def ema(series: List[float], period: int) -> List[float]:
    if period <= 1 or len(series) < period:
        return [float("nan")] * len(series)
    k = 2.0 / (period + 1.0)
    out = [float("nan")] * len(series)
    sma = sum(series[:period]) / period
    out[period - 1] = sma
    prev = sma
    for i in range(period, len(series)):
        v = series[i] * k + prev * (1.0 - k)
        out[i] = v
        prev = v
    return out

def rsi(series: List[float], period: int = 14) -> List[float]:
    if len(series) < period + 1:
        return [float("nan")] * len(series)
    gains, losses = [], []
    out = [float("nan")] * len(series)
    for i in range(1, len(series)):
        ch = series[i] - series[i - 1]
        gains.append(max(0.0, ch))
        losses.append(max(0.0, -ch))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rs = (avg_gain / avg_loss) if avg_loss > 0 else float("inf")
    out[period] = 100.0 - (100.0 / (1.0 + rs))
    ag, al = avg_gain, avg_loss
    for i in range(period + 1, len(series)):
        g = gains[i - 1]
        l = losses[i - 1]
        ag = (ag * (period - 1) + g) / period
        al = (al * (period - 1) + l) / period
        rs = (ag / al) if al > 0 else float("inf")
        out[i] = 100.0 - (100.0 / (1.0 + rs))
    return out

def _pct_change(a: float, b: float) -> float:
    try:
        if b == 0:
            return 0.0
        return (a / b) - 1.0
    except Exception:
        return 0.0

def build_single_bar_features(closes: List[float]) -> Optional[List[float]]:
    """
    Deterministic 5-feature vector aligned with api/app.py usage:
    [ret3, ret8, ret21, vol20_norm, rsi14_norm]
    """
    n = len(closes)
    if n < 60:
        return None
    r3  = _pct_change(closes[-1], closes[-4])
    r8  = _pct_change(closes[-1], closes[-9])
    r21 = _pct_change(closes[-1], closes[-22])
    rets = [_pct_change(closes[i], closes[i - 1]) for i in range(1, n)]
    vol20 = sum(abs(x) for x in rets[-20:]) / 20.0 if len(rets) >= 20 else 0.0
    rsi14 = rsi(closes, 14)[-1]
    rsi_norm = 0.0 if math.isnan(rsi14) else (rsi14 / 100.0)   # 0..1
    vol_norm = min(1.0, max(0.0, vol20 * 10.0))                # heuristic
    def clip01(x: float) -> float:
        return float(min(1.0, max(-1.0, x)))
    return [clip01(r3), clip01(r8), clip01(r21), vol_norm, rsi_norm]

def build_window_features(closes: List[float], at_index: int) -> Optional[List[float]]:
    """
    Same features as build_single_bar_features but computed at an index
    to support forward-looking labels.
    """
    if at_index < 60:
        return None
    sub = closes[: at_index + 1]
    return build_single_bar_features(sub)