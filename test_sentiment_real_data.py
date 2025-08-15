#!/usr/bin/env python3
"""
Test script to verify sentiment analysis data sources
Determines if the system is using real data or demo/empty data
"""
import os
import sys
import time
import requests
sys.path.append('.')

def check_environment_setup():
    """Check current environment and API key configuration"""
    print("🔍 SENTIMENT ANALYSIS DATA SOURCE VERIFICATION")
    print("=" * 60)
    
    print("\n📋 Environment Detection:")
    
    # Check if we're in Render environment
    render_indicators = [
        'RENDER', 'RENDER_EXTERNAL_URL', 'RENDER_INSTANCE_ID', 
        'RENDER_SERVICE_ID', 'RENDER_SERVICE_NAME'
    ]
    
    is_render = any(os.getenv(indicator) for indicator in render_indicators)
    print(f"   Running in Render: {'✅ YES' if is_render else '❌ NO (Local Development)'}")
    
    if is_render:
        print("   Render Service:", os.getenv('RENDER_SERVICE_NAME', 'Unknown'))
        print("   Render URL:", os.getenv('RENDER_EXTERNAL_URL', 'Unknown'))
    
    print("\n🔑 API Key Configuration:")
    
    # Check for Finnhub API key
    finnhub_key = os.getenv('FINNHUB_API_KEY') or os.getenv('FINNHUB_KEY')
    if finnhub_key:
        print(f"   FINNHUB API KEY: ✅ SET (length: {len(finnhub_key)})")
        print(f"   Key preview: {finnhub_key[:8]}...")
        
        # Check if it looks like a demo key
        if 'demo' in finnhub_key.lower() or 'test' in finnhub_key.lower():
            print("   ⚠️  WARNING: This appears to be a DEMO/TEST key")
        else:
            print("   ✅ Appears to be a REAL API key")
    else:
        print("   FINNHUB API KEY: ❌ NOT SET")
        print("   📝 This means NO REAL DATA will be fetched")
    
    return finnhub_key is not None, is_render

def test_sentiment_analysis():
    """Test the sentiment analysis system"""
    print("\n🧪 Testing Sentiment Analysis System:")
    
    try:
        from sentiment.sentiment_service import (
            run_sentiment_cycle, FINNHUB_API_KEY, SENTIMENT_SOURCE,
            SENTIMENT_ASSETS, SENTIMENT_WINDOW_S, SENTIMENT_POLL_S
        )
        
        print(f"   Source: {SENTIMENT_SOURCE}")
        print(f"   Assets: {', '.join(SENTIMENT_ASSETS[:5])}{'...' if len(SENTIMENT_ASSETS) > 5 else ''}")
        print(f"   Window: {SENTIMENT_WINDOW_S}s ({SENTIMENT_WINDOW_S//60} minutes)")
        print(f"   Poll Interval: {SENTIMENT_POLL_S}s")
        
        print("\n   Running sentiment cycle...")
        result = run_sentiment_cycle()
        
        # Analyze results
        total_articles = sum(item.get('n', 0) for item in result.values())
        assets_with_data = sum(1 for item in result.values() if item.get('n', 0) > 0)
        
        print(f"   Total articles processed: {total_articles}")
        print(f"   Assets with sentiment data: {assets_with_data}/{len(result)}")
        
        if total_articles > 0:
            print("   🎉 USING REAL DATA - Articles are being fetched and processed!")
            print("\n   Sample results:")
            for asset, data in list(result.items())[:3]:
                score = data.get('score', 0)
                count = data.get('n', 0)
                sentiment = "Positive" if score > 0.1 else "Negative" if score < -0.1 else "Neutral"
                print(f"     {asset}: {sentiment} (score: {score:.3f}, articles: {count})")
        else:
            print("   ❌ NO REAL DATA - System is returning empty/neutral results")
            print("   📝 This indicates either:")
            print("      - No API key is configured")
            print("      - API key is invalid/demo")
            print("      - Network issues preventing data fetch")
        
        return total_articles > 0
        
    except Exception as e:
        print(f"   ❌ Error testing sentiment system: {e}")
        return False

def test_finnhub_api_directly():
    """Test Finnhub API directly if key is available"""
    print("\n🌐 Direct Finnhub API Test:")
    
    api_key = os.getenv('FINNHUB_API_KEY') or os.getenv('FINNHUB_KEY')
    if not api_key:
        print("   ❌ No API key available for direct testing")
        return False
    
    try:
        url = f"https://finnhub.io/api/v1/news?category=crypto&token={api_key}"
        print("   Making direct API request...")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"   ✅ SUCCESS: Retrieved {len(data)} news articles")
                
                # Show sample article
                sample = data[0]
                print(f"   Sample headline: {sample.get('headline', 'N/A')[:100]}...")
                print(f"   Sample summary: {sample.get('summary', 'N/A')[:100]}...")
                return True
            else:
                print("   ⚠️  API responded but returned empty data")
                return False
        elif response.status_code == 403:
            print("   ❌ API key is invalid or has no permissions")
            return False
        else:
            print(f"   ❌ API request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Direct API test failed: {e}")
        return False

def provide_setup_instructions(has_api_key, is_render):
    """Provide setup instructions based on current state"""
    print("\n" + "=" * 60)
    print("📋 SETUP INSTRUCTIONS")
    print("=" * 60)
    
    if not has_api_key:
        print("\n❌ ISSUE: No FINNHUB_API_KEY configured")
        print("\n🔧 SOLUTION:")
        
        if is_render:
            print("   1. Go to your Render dashboard")
            print("   2. Select your service (bottie-api)")
            print("   3. Go to Environment tab")
            print("   4. Add environment variable:")
            print("      Key: FINNHUB_API_KEY")
            print("      Value: [your-real-finnhub-api-key]")
            print("   5. Redeploy the service")
        else:
            print("   For LOCAL DEVELOPMENT:")
            print("   1. Get a free Finnhub API key from https://finnhub.io")
            print("   2. Set environment variable:")
            print("      export FINNHUB_API_KEY=your_real_api_key_here")
            print("   3. Or add to your .env file")
            
        print("\n🆓 Getting a FREE Finnhub API Key:")
        print("   1. Go to https://finnhub.io")
        print("   2. Click 'Get Free API Key'")
        print("   3. Sign up with email")
        print("   4. Verify your email")
        print("   5. Copy your API key from the dashboard")
        print("   6. Free tier includes: 60 calls/minute, 1000 calls/day")
        
    else:
        print("\n✅ FINNHUB_API_KEY is configured!")
        print("   The system should be using REAL sentiment data")
        
    print("\n🔍 VERIFICATION:")
    print("   After setting up the API key, run this script again:")
    print("   python3 test_sentiment_real_data.py")
    print("\n   Or test via API endpoint:")
    print("   curl https://your-render-url.onrender.com/sentiment")

def main():
    """Main test function"""
    try:
        # Check environment and API key setup
        has_api_key, is_render = check_environment_setup()
        
        # Test sentiment analysis system
        has_real_data = test_sentiment_analysis()
        
        # Test Finnhub API directly if possible
        if has_api_key:
            api_works = test_finnhub_api_directly()
        else:
            api_works = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        if has_real_data:
            print("🎉 STATUS: Using REAL sentiment analysis data")
            print("✅ Your sentiment analysis is working with live news data!")
        else:
            print("❌ STATUS: Using DEMO/EMPTY data (no real sentiment data)")
            print("📝 The system returns neutral scores because no real data is available")
            
        print(f"\n🔧 Configuration Status:")
        print(f"   API Key Configured: {'✅' if has_api_key else '❌'}")
        print(f"   API Key Working: {'✅' if api_works else '❌'}")
        print(f"   Real Data Active: {'✅' if has_real_data else '❌'}")
        print(f"   Environment: {'Render Production' if is_render else 'Local Development'}")
        
        # Provide setup instructions if needed
        if not has_real_data:
            provide_setup_instructions(has_api_key, is_render)
            
        return has_real_data
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)