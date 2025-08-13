#!/usr/bin/env python3
"""
Test script for the Finnhub provider
"""

import os
import sys
sys.path.append('.')

# Set test environment variables
os.environ["FINNHUB_API_KEY"] = "test_key_here"  # Replace with actual key for testing
os.environ["FINNHUB_NEWS_LIMIT"] = "10"

from sentiment.providers.finnhub_provider import filter_news_by_assets, _kw_for, _norm

def test_keyword_extraction():
    """Test the keyword extraction function"""
    print("🧪 Testing keyword extraction...")
    
    # Test default keywords
    btc_kw = _kw_for("BTC")
    print(f"BTC keywords: {btc_kw}")
    assert "bitcoin" in btc_kw
    assert "btc" in btc_kw
    
    # Test custom keywords from environment
    os.environ["SENTIMENT_KW_TEST"] = "test1, test2, test3"
    test_kw = _kw_for("TEST")
    print(f"TEST keywords: {test_kw}")
    assert test_kw == ["test1", "test2", "test3"]
    
    print("✅ Keyword extraction tests passed")

def test_text_normalization():
    """Test the text normalization function"""
    print("🧪 Testing text normalization...")
    
    test_cases = [
        ("Bitcoin  Price   Rises", "bitcoin price rises"),
        ("BTC/USDT  \n\t Trading", "btc/usdt trading"),
        ("", ""),
        (None, ""),
    ]
    
    for input_text, expected in test_cases:
        result = _norm(input_text)
        print(f"'{input_text}' -> '{result}'")
        assert result == expected, f"Expected '{expected}', got '{result}'"
    
    print("✅ Text normalization tests passed")

def test_news_filtering():
    """Test the news filtering function"""
    print("🧪 Testing news filtering...")
    
    # Test with empty API key (should return empty results)
    os.environ["FINNHUB_API_KEY"] = ""
    result = filter_news_by_assets(["BTC", "ETH"])
    print(f"Empty API key result: {result}")
    assert result == {"BTC": [], "ETH": []}
    
    # Reset API key for potential real testing
    os.environ["FINNHUB_API_KEY"] = "test_key_here"
    
    print("✅ News filtering tests passed")

def test_environment_configuration():
    """Test environment variable configuration"""
    print("🧪 Testing environment configuration...")
    
    # Test custom keywords
    os.environ["SENTIMENT_KW_DOGE"] = "dogecoin, doge, shiba"
    doge_kw = _kw_for("DOGE")
    print(f"DOGE custom keywords: {doge_kw}")
    assert doge_kw == ["dogecoin", "doge", "shiba"]
    
    # Test news limit
    limit = int(os.getenv("FINNHUB_NEWS_LIMIT", "50"))
    print(f"News limit: {limit}")
    assert limit == 10  # We set this to 10 earlier
    
    print("✅ Environment configuration tests passed")

def main():
    print("🚀 Testing Finnhub Provider")
    print("=" * 50)
    
    try:
        test_keyword_extraction()
        print()
        test_text_normalization()
        print()
        test_news_filtering()
        print()
        test_environment_configuration()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("\n🔧 To test with real API:")
        print("1. Set FINNHUB_API_KEY environment variable")
        print("2. Run: from sentiment.providers.finnhub_provider import filter_news_by_assets")
        print("3. Test: filter_news_by_assets(['BTC', 'ETH'])")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
