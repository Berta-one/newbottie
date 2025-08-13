#!/usr/bin/env python3
"""Test FINNHUB API key configuration"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

def test_finnhub_config():
    """Test different FINNHUB key configurations"""
    print("🔑 TESTING FINNHUB API KEY CONFIGURATION")
    print("=" * 50)
    
    # Test 1: Check environment variables
    print("1. Environment Variables:")
    api_key = os.getenv("FINNHUB_API_KEY", "")
    key = os.getenv("FINNHUB_KEY", "")
    print(f"   FINNHUB_API_KEY: {api_key[:8] + '...' if api_key else 'NOT SET'}")
    print(f"   FINNHUB_KEY: {key[:8] + '...' if key else 'NOT SET'}")
    
    # Test 2: Import sentiment service
    print("\n2. Sentiment Service Configuration:")
    try:
        from sentiment.sentiment_service import FINNHUB_API_KEY, SENTIMENT_ENABLED
        print(f"   ✅ Sentiment service loaded")
        print(f"   FINNHUB_API_KEY: {FINNHUB_API_KEY[:8] + '...' if FINNHUB_API_KEY else 'NOT SET'}")
        print(f"   SENTIMENT_ENABLED: {SENTIMENT_ENABLED}")
    except Exception as e:
        print(f"   ❌ Sentiment service error: {e}")
    
    # Test 3: Import Finnhub provider
    print("\n3. Finnhub Provider Configuration:")
    try:
        from sentiment.providers.finnhub_provider import API_KEY
        print(f"   ✅ Finnhub provider loaded")
        print(f"   API_KEY: {API_KEY[:8] + '...' if API_KEY else 'NOT SET'}")
    except Exception as e:
        print(f"   ❌ Finnhub provider error: {e}")
    
    # Test 4: Simulate Render environment
    print("\n4. Render Environment Simulation:")
    
    # Backup original values
    orig_api_key = os.environ.get("FINNHUB_API_KEY", "")
    orig_key = os.environ.get("FINNHUB_KEY", "")
    
    # Test with FINNHUB_KEY only (like in Render)
    os.environ["FINNHUB_API_KEY"] = ""
    os.environ["FINNHUB_KEY"] = "test_render_key_12345"
    
    try:
        # Reimport to test fallback
        import importlib
        import sentiment.sentiment_service
        import sentiment.providers.finnhub_provider
        
        importlib.reload(sentiment.sentiment_service)
        importlib.reload(sentiment.providers.finnhub_provider)
        
        from sentiment.sentiment_service import FINNHUB_API_KEY as test_key
        print(f"   ✅ Fallback working: {test_key[:8] + '...' if test_key else 'FAILED'}")
        
    except Exception as e:
        print(f"   ❌ Fallback test failed: {e}")
    finally:
        # Restore original values
        if orig_api_key:
            os.environ["FINNHUB_API_KEY"] = orig_api_key
        if orig_key:
            os.environ["FINNHUB_KEY"] = orig_key
    
    print("\n🎯 CONCLUSION:")
    final_key = api_key or key
    if final_key:
        print("✅ FINNHUB configuration is working")
        print("📰 Real news data will be available")
    else:
        print("⚠️  FINNHUB keys not found locally")
        print("🔧 Render deployment should work if FINNHUB_KEY is set there")

if __name__ == "__main__":
    test_finnhub_config()
