# relaxed_strategy.py
# Place your enhanced_strategy_check and related functions here (from Claude's code or your own)

import statistics
from datetime import datetime


def check_relaxed_breakout(klines):
    if len(klines) < 120:
        return "HOLD"
    try:
        open_price = float(klines[0][1])
        close_price = float(klines[-1][4])
        change_pct = ((close_price - open_price) / open_price) * 100
        if change_pct >= 3.0:
            return "BUY_LONG"
        elif change_pct <= -3.0:
            return "BUY_SHORT"
        else:
            return "HOLD"
    except Exception:
        return "HOLD"


def check_momentum_strategy(klines):
    if len(klines) < 20:
        return "HOLD"
    try:
        recent_closes = [float(kline[4]) for kline in klines[-20:]]
        short_avg = sum(recent_closes[-5:]) / 5
        long_avg = sum(recent_closes[-15:]) / 15
        if short_avg > long_avg * 1.01:
            return "BUY_LONG"
        elif short_avg < long_avg * 0.99:
            return "BUY_SHORT"
        else:
            return "HOLD"
    except Exception:
        return "HOLD"


def check_volatility_breakout(klines):
    if len(klines) < 50:
        return "HOLD"
    try:
        closes = [float(kline[4]) for kline in klines[-50:]]
        returns = [
            (closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))
        ]
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        current_price = closes[-1]
        past_price = closes[-10] if len(closes) >= 10 else closes[0]
        change_pct = ((current_price - past_price) / past_price) * 100
        threshold = max(1.5, volatility * 100)
        if change_pct >= threshold:
            return "BUY_LONG"
        elif change_pct <= -threshold:
            return "BUY_SHORT"
        else:
            return "HOLD"
    except Exception:
        return "HOLD"


def check_simple_rsi_strategy(klines):
    if len(klines) < 20:
        return "HOLD"
    try:
        closes = [float(kline[4]) for kline in klines[-15:]]
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        if rsi < 35:
            return "BUY_LONG"
        elif rsi > 65:
            return "BUY_SHORT"
        else:
            return "HOLD"
    except Exception:
        return "HOLD"


def get_combined_signal(klines):
    if len(klines) < 120:
        return "HOLD", 0.5
    signals = []
    relaxed_signal = check_relaxed_breakout(klines)
    if relaxed_signal != "HOLD":
        signals.append(relaxed_signal)
    momentum_signal = check_momentum_strategy(klines)
    if momentum_signal != "HOLD":
        signals.append(momentum_signal)
    volatility_signal = check_volatility_breakout(klines)
    if volatility_signal != "HOLD":
        signals.append(volatility_signal)
    rsi_signal = check_simple_rsi_strategy(klines)
    if rsi_signal != "HOLD":
        signals.append(rsi_signal)
    if not signals:
        return "HOLD", 0.5
    long_votes = signals.count("BUY_LONG")
    short_votes = signals.count("BUY_SHORT")
    if long_votes >= 2:
        confidence = min(0.9, 0.6 + (long_votes - 2) * 0.1)
        return "BUY_LONG", confidence
    elif short_votes >= 2:
        confidence = min(0.9, 0.6 + (short_votes - 2) * 0.1)
        return "BUY_SHORT", confidence
    else:
        return "HOLD", 0.5


def enhanced_strategy_check(klines):
    signal, confidence = get_combined_signal(klines)
    return {
        "signal": signal,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat(),
        "strategy": "relaxed_multi",
    }
