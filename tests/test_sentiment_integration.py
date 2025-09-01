#!/usr/bin/env python3
"""
Test integration of new sentiment service with API imports
"""

import os
import sys
sys.path.append('.')

def test_api_imports():
    """Test that API can import required sentiment functions"""
    print("🧪 Testing API imports...")
    
    try:
        from sentiment.sentiment_service import (
            start_background as sentiment_start_background,
            snapshot as sentiment_snapshot,
            aggregate_probs as sentiment_latest_probs,
            set_keywords as sentiment_set_keywords,
        )
        
        print("✅ All required functions imported successfully")
        
        # Test function signatures
        print("📋 Testing function signatures...")
        
        # Test snapshot function
        snapshot_result = sentiment_snapshot()
        print(f"  snapshot() -> {type(snapshot_result)}")
        assert isinstance(snapshot_result, dict)
        assert "source" in snapshot_result
        
        # Test aggregate_probs function
        probs_result = sentiment_latest_probs()
        print(f"  aggregate_probs() -> {type(probs_result)}")
        assert isinstance(probs_result, dict)
        
        # Test set_keywords function (should not crash)
        sentiment_set_keywords("BTC", ["bitcoin", "btc"])
        print("  set_keywords() -> works (compatibility mode)")
        
        # Test start_background function
        sentiment_start_background()
        print("  start_background() -> started")
        
        print("✅ All function signatures work correctly")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Function error: {e}")
        return False
    
    return True

def test_backwards_compatibility():
    """Test backwards compatibility with old function names"""
    print("🧪 Testing backwards compatibility...")
    
    try:
        # Test old import pattern
        from sentiment.sentiment_service import snapshot as sentiment_snapshot, latest_probs as sentiment_latest_probs
        
        # These should work the same way
        snapshot1 = sentiment_snapshot()
        probs1 = sentiment_latest_probs()
        
        # Test new import pattern
        from sentiment.sentiment_service import snapshot, aggregate_probs
        
        snapshot2 = snapshot()
        probs2 = aggregate_probs()
        
        # Results should be the same
        assert snapshot1["source"] == snapshot2["source"]
        assert len(probs1) == len(probs2)
        
        print("✅ Backwards compatibility maintained")
        
    except Exception as e:
        print(f"❌ Compatibility error: {e}")
        return False
    
    return True

def test_environment_integration():
    """Test environment variable integration"""
    print("🧪 Testing environment integration...")
    
    # Set some test environment variables
    os.environ["SENTIMENT_ENABLED"] = "1"
    os.environ["SENTIMENT_SOURCE"] = "finnhub"
    os.environ["SENTIMENT_WINDOW_S"] = "600"
    
    try:
        # Re-import to pick up environment changes
        import importlib
        import sentiment.sentiment_service
        importlib.reload(sentiment.sentiment_service)
        
        from sentiment.sentiment_service import SENTIMENT_ENABLED, SENTIMENT_SOURCE, SENTIMENT_WINDOW_S
        
        assert SENTIMENT_ENABLED == True
        assert SENTIMENT_SOURCE == "finnhub"
        assert SENTIMENT_WINDOW_S == 600
        
        print("✅ Environment integration works")
        
    except Exception as e:
        print(f"❌ Environment error: {e}")
        return False
    
    return True

def main():
    print("🚀 Testing Sentiment Service API Integration")
    print("=" * 55)
    
    success = True
    
    success &= test_api_imports()
    print()
    success &= test_backwards_compatibility()
    print()
    success &= test_environment_integration()
    
    print("\n" + "=" * 55)
    if success:
        print("✅ All integration tests passed!")
        print("\n🔧 Integration summary:")
        print("• API imports work without modification")
        print("• Function signatures are compatible")
        print("• Backwards compatibility maintained")
        print("• Environment variables properly handled")
        print("• Ready to replace old sentiment service")
    else:
        print("❌ Some integration tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
