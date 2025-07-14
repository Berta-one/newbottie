# strategy.py - Enhanced Breakout Strategy with Filters
from datetime import datetime
import pytz
import statistics

def calculate_volume_average(klines, period=20):
    """Calculate average volume over specified period"""
    volumes = [float(candle[5]) for candle in klines[-period:]]
    return sum(volumes) / len(volumes) if volumes else 0

def calculate_volatility(klines, period=20):
    """Calculate price volatility (standard deviation of returns)"""
    closes = [float(candle[4]) for candle in klines[-period:]]
    if len(closes) < 2:
        return 0
    
    returns = [(closes[i] / closes[i-1] - 1) for i in range(1, len(closes))]
    return statistics.stdev(returns) if len(returns) > 1 else 0

def is_good_trading_time():
    """Check if current time is good for trading (avoid low-volume periods)"""
    utc_now = datetime.now(pytz.UTC)
    hour = utc_now.hour
    
    # Avoid low volume hours (0-6 UTC, 22-23 UTC)
    low_volume_hours = [0, 1, 2, 3, 4, 5, 22, 23]
    return hour not in low_volume_hours

def calculate_sma(klines, period):
    """Calculate Simple Moving Average"""
    closes = [float(candle[4]) for candle in klines[-period:]]
    return sum(closes) / len(closes) if closes else 0

def analyze_market_structure(klines):
    """Analyze recent market structure for trend strength"""
    if len(klines) < 10:
        return "SIDEWAYS"
    
    closes = [float(candle[4]) for candle in klines[-10:]]
    highs = [float(candle[2]) for candle in klines[-10:]]
    lows = [float(candle[3]) for candle in klines[-10:]]
    
    # Check for higher highs and higher lows (uptrend)
    recent_high = max(highs[-5:])
    previous_high = max(highs[-10:-5]) if len(highs) >= 10 else recent_high
    recent_low = min(lows[-5:])
    previous_low = min(lows[-10:-5]) if len(lows) >= 10 else recent_low
    
    # Trend analysis
    if recent_high > previous_high and recent_low > previous_low:
        return "UPTREND"
    elif recent_high < previous_high and recent_low < previous_low:
        return "DOWNTREND"
    else:
        return "SIDEWAYS"

def calculate_rsi(klines, period=14):
    """Calculate Relative Strength Index"""
    if len(klines) < period + 1:
        return 50  # Neutral RSI
    
    closes = [float(candle[4]) for candle in klines[-(period+1):]]
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_breakout_enhanced(klines):
    """
    Enhanced breakout strategy with multiple filters
    Returns: BUY_LONG, BUY_SHORT, or HOLD
    """
    if len(klines) < 120:
        return "HOLD"
    
    # 1. TIME FILTER: Only trade during good hours
    if not is_good_trading_time():
        return "HOLD"
    
    # 2. VOLUME FILTER: Require above-average volume
    volume_avg = calculate_volume_average(klines, 20)
    current_volume = float(klines[-1][5])
    
    if volume_avg == 0:
        return "HOLD"
    
    volume_ratio = current_volume / volume_avg
    if volume_ratio < 1.5:  # Require 1.5x average volume
        return "HOLD"
    
    # 3. VOLATILITY FILTER: Adjust breakout threshold
    volatility = calculate_volatility(klines, 20)
    if volatility > 0.05:  # High volatility
        breakout_threshold = 6.0
    elif volatility > 0.03:  # Medium volatility
        breakout_threshold = 5.5
    else:  # Low volatility
        breakout_threshold = 5.0
    
    # 4. MARKET STRUCTURE: Confirm with trend
    market_structure = analyze_market_structure(klines)
    
    # 5. RSI FILTER: Avoid overbought/oversold extremes
    rsi = calculate_rsi(klines, 14)
    
    # 6. BREAKOUT CALCULATION
    open_price = float(klines[0][1])   # 2 hours ago
    close_price = float(klines[-1][4]) # Current price
    change = ((close_price - open_price) / open_price) * 100
    
    # 7. DECISION LOGIC
    if change >= breakout_threshold:
        # Upward breakout
        if market_structure in ["UPTREND", "SIDEWAYS"] and rsi < 80:
            return "BUY_LONG"
        else:
            return "HOLD"
            
    elif change <= -breakout_threshold:
        # Downward breakout  
        if market_structure in ["DOWNTREND", "SIDEWAYS"] and rsi > 20:
            return "BUY_SHORT"
        else:
            return "HOLD"
    else:
        return "HOLD"

def get_strategy_confidence(klines):
    """
    Calculate confidence level for the strategy (0.0 to 1.0)
    Higher confidence = larger position size
    """
    if len(klines) < 120:
        return 0.1
    
    confidence = 0.5  # Base confidence
    
    # Volume confirmation
    volume_avg = calculate_volume_average(klines, 20)
    current_volume = float(klines[-1][5])
    
    if volume_avg > 0:
        volume_ratio = current_volume / volume_avg
        if volume_ratio > 3.0:
            confidence += 0.2
        elif volume_ratio > 2.0:
            confidence += 0.15
        elif volume_ratio > 1.5:
            confidence += 0.1
    
    # Volatility consideration
    volatility = calculate_volatility(klines, 20)
    if volatility > 0.05:
        confidence -= 0.15  # Reduce confidence in high volatility
    elif volatility < 0.02:
        confidence += 0.1   # Increase confidence in stable conditions
    
    # Time of day boost
    if is_good_trading_time():
        confidence += 0.1
    
    # Market structure alignment
    market_structure = analyze_market_structure(klines)
    if market_structure in ["UPTREND", "DOWNTREND"]:
        confidence += 0.1  # Clear trend adds confidence
    
    # RSI confirmation
    rsi = calculate_rsi(klines, 14)
    if 30 < rsi < 70:  # Not in extreme territory
        confidence += 0.05
    
    # Price momentum
    sma_5 = calculate_sma(klines, 5)
    sma_20 = calculate_sma(klines, 20)
    current_price = float(klines[-1][4])
    
    if sma_5 > sma_20 and current_price > sma_5:  # Strong uptrend
        confidence += 0.1
    elif sma_5 < sma_20 and current_price < sma_5:  # Strong downtrend
        confidence += 0.1
    
    # Ensure confidence stays within bounds
    return max(0.1, min(1.0, confidence))

def analyze_pair_strength(klines, symbol):
    """
    Analyze the overall strength/quality of a trading pair
    Returns dict with various metrics
    """
    if len(klines) < 120:
        return None
    
    # Price metrics
    current_price = float(klines[-1][4])
    open_price = float(klines[0][1])
    high_price = max([float(k[2]) for k in klines])
    low_price = min([float(k[3]) for k in klines])
    
    # Volume metrics
    avg_volume = calculate_volume_average(klines, 20)
    current_volume = float(klines[-1][5])
    
    # Technical indicators
    rsi = calculate_rsi(klines, 14)
    volatility = calculate_volatility(klines, 20)
    
    return {
        'symbol': symbol,
        'current_price': current_price,
        'price_change_2h': ((current_price - open_price) / open_price) * 100,
        'high_low_range': ((high_price - low_price) / current_price) * 100,
        'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0,
        'rsi': rsi,
        'volatility': volatility,
        'market_structure': analyze_market_structure(klines),
        'trading_time_quality': is_good_trading_time()
    }

# Backward compatibility functions
def check_breakout(klines):
    """Original function name for compatibility"""
    return check_breakout_enhanced(klines)
