#!/usr/bin/env python3
"""
Example usage of the Finnhub Provider
"""

import os
import logging
from sentiment.providers.finnhub_provider import filter_news_by_assets, _kw_for

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG)

def demo_finnhub_provider():
    """Demonstrate the Finnhub provider functionality"""
    print("🚀 Finnhub Provider Demo")
    print("=" * 50)
    
    # 1. Show default keywords
    print("📋 Default Keywords:")
    for asset in ["BTC", "ETH", "BNB", "ADA", "XRP", "SOL"]:
        keywords = _kw_for(asset)
        print(f"  {asset}: {keywords}")
    
    # 2. Show custom keyword override
    print(f"\n🔧 Custom Keywords (via environment variables):")
    os.environ["SENTIMENT_KW_DOGE"] = "dogecoin, doge, shiba inu, doge coin"
    print(f"  DOGE: {_kw_for('DOGE')}")
    
    # 3. Test with demo API key (will fail but show structure)
    print(f"\n📰 News Filtering Test:")
    print("Setting demo API key (replace with real key for actual use)...")
    os.environ["FINNHUB_API_KEY"] = "demo_key_12345"
    
    # Test the filtering function
    assets = ["BTC", "ETH", "DOGE"]
    result = filter_news_by_assets(assets)
    
    print(f"Result structure: {type(result)}")
    for asset, news_list in result.items():
        print(f"  {asset}: {len(news_list)} news items")
    
    # 4. Show configuration options
    print(f"\n⚙️  Configuration Options:")
    print(f"  FINNHUB_API_KEY: Set your Finnhub API key")
    print(f"  FINNHUB_NEWS_LIMIT: Max news items to fetch (default: 50)")
    print(f"  SENTIMENT_KW_<ASSET>: Custom keywords for specific assets")
    print(f"  Example: SENTIMENT_KW_BTC='bitcoin,btc,bitcoin price,btc price'")
    
    # 5. Integration example
    print(f"\n🔗 Integration Example:")
    print("""
# In your sentiment service:
from sentiment.providers.finnhub_provider import filter_news_by_assets

# Get news for your trading assets
assets = ["BTC", "ETH", "BNB", "ADA"]
news_by_asset = filter_news_by_assets(assets)

# Process with VADER sentiment analysis
for asset, news_texts in news_by_asset.items():
    sentiment_scores = []
    for text in news_texts:
        score = vader_analyzer.polarity_scores(text)
        sentiment_scores.append(score['compound'])
    
    # Calculate average sentiment
    if sentiment_scores:
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        print(f"{asset} sentiment: {avg_sentiment:.3f}")
""")

def setup_instructions():
    """Show setup instructions"""
    print("\n" + "=" * 50)
    print("🛠️  Setup Instructions")
    print("=" * 50)
    print("1. Get Finnhub API Key:")
    print("   - Sign up at https://finnhub.io/")
    print("   - Get your free API key")
    print("   - Set environment variable: FINNHUB_API_KEY=your_key_here")
    
    print("\n2. Install Dependencies:")
    print("   pip install requests")
    
    print("\n3. Configure Keywords (Optional):")
    print("   export SENTIMENT_KW_BTC='bitcoin,btc,bitcoin price'")
    print("   export SENTIMENT_KW_ETH='ethereum,eth,ether'")
    
    print("\n4. Configure News Limits (Optional):")
    print("   export FINNHUB_NEWS_LIMIT=100  # Default: 50")
    
    print("\n5. Test the Provider:")
    print("   python test_finnhub_provider.py")

if __name__ == "__main__":
    demo_finnhub_provider()
    setup_instructions()
