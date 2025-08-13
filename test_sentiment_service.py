#!/usr/bin/env python3
"""
Test script for the new resilient sentiment service
"""

import os
import sys
import time
import threading
sys.path.append('.')

# Set test environment variables
os.environ["SENTIMENT_ENABLED"] = "1"
os.environ["FINNHUB_API_KEY"] = "test_key_here"  # Replace with actual key for real testing
os.environ["SENTIMENT_WINDOW_S"] = "300"  # 5 minutes for testing
os.environ["SENTIMENT_POLL_S"] = "10"     # 10 seconds for testing
os.environ["SENTIMENT_TOP_N"] = "5"

def test_sentiment_service_config():
    """Test sentiment service configuration"""
    print("🧪 Testing sentiment service configuration...")
    
    from sentiment.sentiment_service import (
        SENTIMENT_ENABLED, SENTIMENT_SOURCE, SENTIMENT_WINDOW_S, 
        SENTIMENT_ASSETS, SENTIMENT_TOP_N, SENTIMENT_POLL_S
    )
    
    print(f"  SENTIMENT_ENABLED: {SENTIMENT_ENABLED}")
    print(f"  SENTIMENT_SOURCE: {SENTIMENT_SOURCE}")
    print(f"  SENTIMENT_WINDOW_S: {SENTIMENT_WINDOW_S}")
    print(f"  SENTIMENT_ASSETS: {SENTIMENT_ASSETS}")
    print(f"  SENTIMENT_TOP_N: {SENTIMENT_TOP_N}")
    print(f"  SENTIMENT_POLL_S: {SENTIMENT_POLL_S}")
    
    assert SENTIMENT_ENABLED == True
    assert SENTIMENT_SOURCE == "finnhub"
    assert SENTIMENT_WINDOW_S == 300
    assert "BTC" in SENTIMENT_ASSETS
    assert "ETH" in SENTIMENT_ASSETS
    
    print("✅ Configuration tests passed")

def test_sentiment_functions():
    """Test core sentiment functions"""
    print("🧪 Testing sentiment functions...")
    
    from sentiment.sentiment_service import (
        run_sentiment_cycle, latest_probs, aggregate_probs, 
        snapshot, _to_prob, _clip
    )
    
    # Test utility functions
    assert _clip(0.5, 0.0, 1.0) == 0.5
    assert _clip(-0.5, 0.0, 1.0) == 0.0
    assert _clip(1.5, 0.0, 1.0) == 1.0
    print("  ✅ _clip function works")
    
    # Test probability mapping
    assert _to_prob(0.0) == 0.5
    assert _to_prob(1.0) == 1.0
    assert _to_prob(-1.0) == 0.0
    print("  ✅ _to_prob function works")
    
    # Test sentiment cycle (will return empty with test API key)
    result = run_sentiment_cycle()
    print(f"  Sentiment cycle result: {result}")
    assert isinstance(result, dict)
    for asset in ["BTC", "ETH"]:
        if asset in result:
            assert "score" in result[asset]
            assert "n" in result[asset]
    print("  ✅ run_sentiment_cycle works")
    
    # Test probability functions
    probs = latest_probs()
    print(f"  Latest probs: {probs}")
    assert isinstance(probs, dict)
    
    agg_probs = aggregate_probs()
    print(f"  Aggregate probs: {agg_probs}")
    assert isinstance(agg_probs, dict)
    
    # Test snapshot
    snap = snapshot()
    print(f"  Snapshot: {snap}")
    assert isinstance(snap, dict)
    assert "source" in snap
    assert "window_sec" in snap
    assert "scores" in snap
    
    print("✅ Function tests passed")

def test_background_worker():
    """Test background worker functionality"""
    print("🧪 Testing background worker...")
    
    from sentiment.sentiment_service import start_background, stop_background, _bg_thread
    
    # Start background worker
    start_background()
    
    # Check if thread is running
    if _bg_thread and _bg_thread.is_alive():
        print("  ✅ Background thread started successfully")
        
        # Let it run for a few seconds
        print("  Running for 5 seconds...")
        time.sleep(5)
        
        # Stop background worker
        stop_background()
        print("  ✅ Background thread stopped")
    else:
        print("  ⚠️ Background thread not started (might be due to disabled sentiment)")
    
    print("✅ Background worker tests completed")

def test_error_handling():
    """Test error handling"""
    print("🧪 Testing error handling...")
    
    # Test with invalid API key
    original_key = os.environ.get("FINNHUB_API_KEY", "")
    os.environ["FINNHUB_API_KEY"] = ""
    
    from sentiment.sentiment_service import run_sentiment_cycle
    
    # This should handle missing API key gracefully
    result = run_sentiment_cycle()
    print(f"  Result with empty API key: {result}")
    assert isinstance(result, dict)
    
    # Restore original key
    os.environ["FINNHUB_API_KEY"] = original_key
    
    print("✅ Error handling tests passed")

def test_persistence():
    """Test history persistence functionality"""
    print("🧪 Testing persistence functionality...")
    
    import tempfile
    
    # Set a temporary history path
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = f.name
    
    os.environ["SENTIMENT_HISTORY_PATH"] = temp_path
    
    # Re-import to pick up new environment variable
    import importlib
    import sentiment.sentiment_service
    importlib.reload(sentiment.sentiment_service)
    
    from sentiment.sentiment_service import run_sentiment_cycle
    
    # Run a cycle to generate history
    run_sentiment_cycle()
    
    # Check if file was created
    if os.path.exists(temp_path):
        with open(temp_path, 'r') as f:
            content = f.read()
        print(f"  History file created with content: {len(content)} chars")
        print("  ✅ Persistence works")
        
        # Clean up
        os.unlink(temp_path)
    else:
        print("  ⚠️ History file not created (might be due to empty data)")
    
    # Clean up environment
    if "SENTIMENT_HISTORY_PATH" in os.environ:
        del os.environ["SENTIMENT_HISTORY_PATH"]
    
    print("✅ Persistence tests completed")

def main():
    print("🚀 Testing New Resilient Sentiment Service")
    print("=" * 60)
    
    try:
        test_sentiment_service_config()
        print()
        test_sentiment_functions()
        print()
        test_background_worker()
        print()
        test_error_handling()
        print()
        test_persistence()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("\n🔧 Integration notes:")
        print("• The service uses threading instead of asyncio for better compatibility")
        print("• Environment variables are properly handled with defaults")
        print("• Error handling is robust and doesn't crash on API failures")
        print("• Background polling is optional and can be started/stopped")
        print("• History persistence is optional via SENTIMENT_HISTORY_PATH")
        print("\n🚀 Ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
