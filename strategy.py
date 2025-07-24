#!/usr/bin/env python3
"""
Enhanced Cryptocurrency Breakout Trading Strategy
================================================

Enhanced breakout strategy with volume confirmation, time filtering,
market structure analysis, volatility adjustment, and RSI filtering.

Features:
- 5% price moves over 2 hours (120 1-minute candles)
- Volume confirmation (1.5x average volume)
- Time-of-day filtering (avoid low volume hours)
- Market structure analysis (trend direction)
- Volatility adjustment (increase threshold in high volatility)
- RSI filtering (avoid overbought/oversold)
- Confidence scoring (0.0-1.0)
"""

import pytz
from datetime import datetime
import statistics
import numpy as np
from typing import List, Tuple, Dict, Any


def check_breakout_enhanced(klines: List) -> str:
    """
    Enhanced breakout detection with multiple filters

    Args:
        klines: List of 120 1-minute candlestick data

    Returns:
        "BUY_LONG", "BUY_SHORT", or "HOLD"
    """
    if len(klines) < 120:
        return "HOLD"

    # Check if it's a good trading time
    if not is_good_trading_time():
        return "HOLD"

    # Calculate price change over 2 hours
    open_price = float(klines[0][1])  # Opening price 2 hours ago
    close_price = float(klines[-1][4])  # Current closing price
    price_change_pct = ((close_price - open_price) / open_price) * 100

    # Volume confirmation
    if not has_volume_confirmation(klines):
        return "HOLD"

    # Market structure analysis
    market_structure = analyze_market_structure(klines)
    if market_structure == "SIDEWAYS":
        return "HOLD"

    # Volatility adjustment
    volatility = calculate_volatility(klines)
    breakout_threshold = 5.0  # Base threshold
    if volatility > 5.0:  # High volatility adjustment
        breakout_threshold = min(breakout_threshold + (volatility - 5.0), 6.0)

    # RSI filtering
    rsi = calculate_rsi(klines)
    if rsi > 80 or rsi < 20:  # Avoid overbought/oversold
        return "HOLD"

    # Determine signal based on enhanced criteria
    if price_change_pct >= breakout_threshold:
        if market_structure == "UPTREND":
            return "BUY_LONG"
        else:
            return "HOLD"  # Don't buy against the trend
    elif price_change_pct <= -breakout_threshold:
        if market_structure == "DOWNTREND":
            return "BUY_SHORT"
        else:
            return "HOLD"  # Don't short against the trend

    return "HOLD"


def get_strategy_confidence(klines: List) -> float:
    """
    Calculate strategy confidence score (0.0 to 1.0)

    Args:
        klines: List of candlestick data

    Returns:
        Confidence score between 0.0 and 1.0
    """
    if len(klines) < 120:
        return 0.0

    confidence_factors = []

    # Time factor (higher confidence during good trading hours)
    if is_good_trading_time():
        confidence_factors.append(0.2)
    else:
        confidence_factors.append(0.0)

    # Volume factor
    volume_ratio = get_volume_ratio(klines)
    volume_confidence = min(volume_ratio / 2.0, 0.25)  # Max 0.25 for volume
    confidence_factors.append(volume_confidence)

    # Price movement strength
    open_price = float(klines[0][1])
    close_price = float(klines[-1][4])
    price_change_pct = abs(((close_price - open_price) / open_price) * 100)
    movement_confidence = min(price_change_pct / 10.0, 0.25)  # Max 0.25 for movement
    confidence_factors.append(movement_confidence)

    # Market structure factor
    market_structure = analyze_market_structure(klines)
    if market_structure in ["UPTREND", "DOWNTREND"]:
        confidence_factors.append(0.15)
    else:
        confidence_factors.append(0.05)

    # RSI factor (higher confidence when RSI is in good range)
    rsi = calculate_rsi(klines)
    if 30 <= rsi <= 70:  # Good range
        confidence_factors.append(0.15)
    elif 20 <= rsi <= 80:  # Acceptable range
        confidence_factors.append(0.1)
    else:  # Extreme range
        confidence_factors.append(0.0)

    return min(sum(confidence_factors), 1.0)


def is_good_trading_time() -> bool:
    """
    Check if current time is good for trading (avoid low volume hours)

    Returns:
        True if good trading time, False otherwise
    """
    utc_now = datetime.now(pytz.UTC)
    current_hour = utc_now.hour

    # Avoid low volume hours: 0-6 UTC (Asian night) and 22-23 UTC (US late evening)
    bad_hours = [0, 1, 2, 3, 4, 5, 22, 23]
    return current_hour not in bad_hours


def calculate_volatility(klines: List, period: int = 20) -> float:
    """
    Calculate price volatility as standard deviation of returns

    Args:
        klines: List of candlestick data
        period: Number of periods for calculation

    Returns:
        Volatility percentage
    """
    if len(klines) < period + 1:
        return 0.0

    prices = [float(kline[4]) for kline in klines[-period - 1 :]]  # Closing prices
    returns = []

    for i in range(1, len(prices)):
        return_pct = ((prices[i] - prices[i - 1]) / prices[i - 1]) * 100
        returns.append(return_pct)

    if len(returns) < 2:
        return 0.0

    return statistics.stdev(returns)


def analyze_market_structure(klines: List) -> str:
    """
    Analyze market structure using higher highs/lows

    Args:
        klines: List of candlestick data

    Returns:
        "UPTREND", "DOWNTREND", or "SIDEWAYS"
    """
    if len(klines) < 20:
        return "SIDEWAYS"

    # Use last 20 candles for structure analysis
    recent_klines = klines[-20:]
    highs = [float(kline[2]) for kline in recent_klines]
    lows = [float(kline[3]) for kline in recent_klines]

    # Find peaks and troughs
    peaks = []
    troughs = []

    for i in range(1, len(highs) - 1):
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
            peaks.append(highs[i])
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
            troughs.append(lows[i])

    # Need at least 2 peaks and troughs for analysis
    if len(peaks) < 2 or len(troughs) < 2:
        return "SIDEWAYS"

    # Check for higher highs and higher lows (uptrend)
    higher_highs = peaks[-1] > peaks[-2]
    higher_lows = troughs[-1] > troughs[-2]

    # Check for lower highs and lower lows (downtrend)
    lower_highs = peaks[-1] < peaks[-2]
    lower_lows = troughs[-1] < troughs[-2]

    if higher_highs and higher_lows:
        return "UPTREND"
    elif lower_highs and lower_lows:
        return "DOWNTREND"
    else:
        return "SIDEWAYS"


def calculate_rsi(klines: List, period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI)

    Args:
        klines: List of candlestick data
        period: RSI calculation period

    Returns:
        RSI value (0-100)
    """
    if len(klines) < period + 1:
        return 50.0  # Neutral RSI if insufficient data

    prices = [float(kline[4]) for kline in klines[-(period + 1) :]]  # Closing prices
    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    if len(gains) < period:
        return 50.0

    avg_gain = sum(gains) / len(gains)
    avg_loss = sum(losses) / len(losses)

    if avg_loss == 0:
        return 100.0  # All gains, maximum RSI

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def has_volume_confirmation(klines: List) -> bool:
    """
    Check if current volume is at least 1.5x average volume

    Args:
        klines: List of candlestick data

    Returns:
        True if volume is confirmed, False otherwise
    """
    if len(klines) < 20:
        return False

    # Calculate average volume over last 20 periods
    volumes = [float(kline[5]) for kline in klines[-20:]]
    avg_volume = sum(volumes[:-1]) / len(volumes[:-1])  # Exclude current candle
    current_volume = volumes[-1]

    return current_volume >= (avg_volume * 1.5)


def get_volume_ratio(klines: List) -> float:
    """
    Get current volume ratio compared to average

    Args:
        klines: List of candlestick data

    Returns:
        Volume ratio (current/average)
    """
    if len(klines) < 20:
        return 1.0

    volumes = [float(kline[5]) for kline in klines[-20:]]
    avg_volume = sum(volumes[:-1]) / len(volumes[:-1])
    current_volume = volumes[-1]

    if avg_volume == 0:
        return 1.0

    return current_volume / avg_volume


# Legacy compatibility functions
def check_breakout(klines: List) -> str:
    """Legacy function for backwards compatibility"""
    return check_breakout_enhanced(klines)


# Example usage and testing
if __name__ == "__main__":
    # Example test with mock data
    mock_klines = []
    base_price = 50000
    base_volume = 1000

    # Generate 120 mock candles with a 5% upward move
    for i in range(120):
        price_factor = 1 + (i * 0.05 / 120)  # Gradual 5% increase
        current_price = base_price * price_factor
        volume = base_volume * (1.6 if i > 100 else 1.0)  # Volume spike at end

        mock_klines.append(
            [
                0,  # Open time
                str(current_price),  # Open price
                str(current_price * 1.001),  # High price
                str(current_price * 0.999),  # Low price
                str(current_price),  # Close price
                str(volume),  # Volume
                0,
                0,
                0,
                0,
                0,
                0,  # Other fields
            ]
        )

    result = check_breakout_enhanced(mock_klines)
    confidence = get_strategy_confidence(mock_klines)

    print(f"Strategy Result: {result}")
    print(f"Confidence Score: {confidence:.2f}")
    print(f"Market Structure: {analyze_market_structure(mock_klines)}")
    print(f"Volatility: {calculate_volatility(mock_klines):.2f}%")
    print(f"RSI: {calculate_rsi(mock_klines):.1f}")
    print(f"Volume Confirmed: {has_volume_confirmation(mock_klines)}")
    print(f"Good Trading Time: {is_good_trading_time()}")
