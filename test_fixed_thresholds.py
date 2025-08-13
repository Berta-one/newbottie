# Test the fixed threshold function
import numpy as np
from typing import Tuple

# Mock global variables for testing
TRADE_CONF_ADAPT = True
TRADE_BASE_MIN_CONF = 0.55
TRADE_CONF_FLOOR = 0.50
TRADE_CONF_CEIL = 0.80
_signals = []

def _adaptive_thresholds() -> Tuple[float, float]:
    """
    Dynamic buy/sell thresholds around 0.5 based on recent ensemble dispersion.
    Returns buy_threshold, sell_threshold both in range [0, 1]
    """
    if not TRADE_CONF_ADAPT:
        # Simple fixed thresholds when adaptation is disabled
        # TRADE_BASE_MIN_CONF should be interpreted as the minimum confidence needed
        # Convert to margin around 0.5
        if TRADE_BASE_MIN_CONF > 0.5:
            margin = TRADE_BASE_MIN_CONF - 0.5  # e.g., 0.55 -> 0.05 margin
        else:
            margin = 0.05  # default 5% margin
        
        thr_buy = 0.5 + margin
        thr_sell = 0.5 - margin
        
        # Ensure thresholds stay in valid range [0, 1]
        thr_buy = min(0.95, max(0.51, thr_buy))
        thr_sell = max(0.05, min(0.49, thr_sell))
        
        return float(thr_buy), float(thr_sell)
    
    # Adaptive thresholds based on recent signal history
    window = _signals[-50:]  # Last 50 signals
    if not window:
        # Default margin when no signal history
        margin = 0.05
    else:
        # Calculate volatility of recent predictions
        probs = [s.get("final_prob", 0.5) for s in window if s.get("final_prob") is not None]
        if not probs:
            margin = 0.05
        else:
            volatility = float(np.std(probs))
            
            # Adjust threshold based on volatility
            # High volatility = wider thresholds (more conservative)
            # Low volatility = tighter thresholds (more aggressive)
            base_margin = 0.05
            volatility_factor = min(2.0, max(0.5, volatility * 10))  # Scale volatility
            margin = base_margin * volatility_factor
            
            # Clamp margin to reasonable bounds
            # TRADE_CONF_FLOOR and TRADE_CONF_CEIL should be probabilities, not margins
            min_margin = 0.02  # minimum 2% margin
            max_margin = 0.3   # maximum 30% margin
            
            # If TRADE_CONF_FLOOR/CEIL are set properly, use them
            if TRADE_CONF_FLOOR > 0.5:
                min_margin = max(min_margin, TRADE_CONF_FLOOR - 0.5)
            if TRADE_CONF_CEIL < 1.0 and TRADE_CONF_CEIL > 0.5:
                max_margin = min(max_margin, TRADE_CONF_CEIL - 0.5)
            
            margin = float(np.clip(margin, min_margin, max_margin))
    
    thr_buy = 0.5 + margin
    thr_sell = 0.5 - margin
    
    # Final safety clamps to ensure valid probability range
    thr_buy = min(0.95, max(0.51, thr_buy))
    thr_sell = max(0.05, min(0.49, thr_sell))
    
    return float(thr_buy), float(thr_sell)


def test_fixed_thresholds():
    """Test the fixed threshold function"""
    global TRADE_CONF_ADAPT, TRADE_BASE_MIN_CONF, TRADE_CONF_FLOOR, TRADE_CONF_CEIL, _signals
    
    TRADE_CONF_ADAPT = True  # Test adaptive mode
    TRADE_BASE_MIN_CONF = 0.55
    TRADE_CONF_FLOOR = 0.50
    TRADE_CONF_CEIL = 0.80
    
    # Mock some signals
    _signals = [
        {"final_prob": 0.6}, {"final_prob": 0.4}, {"final_prob": 0.7},
        {"final_prob": 0.3}, {"final_prob": 0.55}, {"final_prob": 0.45}
    ]
    
    print("🧪 Testing fixed threshold function...")
    
    # Test adaptive mode
    thr_buy, thr_sell = _adaptive_thresholds()
    print(f"Adaptive mode:")
    print(f"  Buy threshold: {thr_buy:.4f}")
    print(f"  Sell threshold: {thr_sell:.4f}")
    print(f"  Margin: {(thr_buy - 0.5):.4f}")
    
    # Validate thresholds are in valid range
    if 0 <= thr_sell < 0.5 < thr_buy <= 1.0:
        print("✅ Thresholds are in valid range")
    else:
        print("❌ Thresholds are out of valid range!")
        return False
    
    # Test non-adaptive mode
    TRADE_CONF_ADAPT = False
    thr_buy_fixed, thr_sell_fixed = _adaptive_thresholds()
    print(f"\nFixed mode:")
    print(f"  Buy threshold: {thr_buy_fixed:.4f}")
    print(f"  Sell threshold: {thr_sell_fixed:.4f}")
    print(f"  Margin: {(thr_buy_fixed - 0.5):.4f}")
    
    # Validate fixed thresholds
    if 0 <= thr_sell_fixed < 0.5 < thr_buy_fixed <= 1.0:
        print("✅ Fixed thresholds are in valid range")
        return True
    else:
        print("❌ Fixed thresholds are out of valid range!")
        return False

if __name__ == "__main__":
    test_fixed_thresholds()
