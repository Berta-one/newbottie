#!/usr/bin/env python3
"""
Test production sentiment analysis via API endpoint
This tests the live Render deployment where FINNHUB_API_KEY is configured
"""
import requests
import json
import time
from datetime import datetime

# Your Render API URL - update this with your actual URL
RENDER_API_URL = "https://bottie-1.onrender.com"  # Update if different

def test_production_sentiment():
    """Test sentiment analysis in production environment"""
    print("🚀 PRODUCTION SENTIMENT ANALYSIS TEST")
    print("=" * 50)
    print(f"Testing: {RENDER_API_URL}")
    print()
    
    try:
        # Test sentiment debug endpoint first
        print("🔍 Testing /sentiment/debug endpoint...")
        debug_response = requests.get(f"{RENDER_API_URL}/sentiment/debug", timeout=30)
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print("✅ Sentiment debug endpoint responded!")
            print(f"   API Key Status: {debug_data.get('api_key_status', 'Unknown')}")
            print(f"   Sentiment Enabled: {debug_data.get('sentiment_enabled', 'Unknown')}")
            print(f"   Using Real Data: {debug_data.get('using_real_data', 'Unknown')}")
            print(f"   Total Articles: {debug_data.get('total_articles', 0)}")
            print(f"   Environment: {debug_data.get('environment', 'Unknown')}")
        else:
            print(f"⚠️  Debug endpoint returned status: {debug_response.status_code}")
        
        print()
        # Test sentiment endpoint
        print("📊 Testing /sentiment endpoint...")
        response = requests.get(f"{RENDER_API_URL}/sentiment", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Sentiment endpoint responded successfully!")
            print()
            
            # Analyze the response
            print("📋 Response Analysis:")
            print(f"   Source: {data.get('source', 'Unknown')}")
            print(f"   Window: {data.get('window_sec', 0)}s")
            
            scores = data.get('scores', {})
            print(f"   Assets tracked: {len(scores)}")
            
            # Check if we have real data
            total_articles = sum(asset_data.get('n', 0) for asset_data in scores.values())
            assets_with_data = sum(1 for asset_data in scores.values() if asset_data.get('n', 0) > 0)
            
            print(f"   Total articles: {total_articles}")
            print(f"   Assets with data: {assets_with_data}/{len(scores)}")
            
            if total_articles > 0:
                print("\n🎉 PRODUCTION IS USING REAL DATA!")
                print("✅ The sentiment analysis is fetching live news articles!")
                
                print("\n📈 Current Sentiment Scores:")
                for asset, asset_data in list(scores.items())[:8]:  # Show first 8
                    score = asset_data.get('score', 0)
                    count = asset_data.get('n', 0)
                    sentiment_label = "Bullish" if score > 0.1 else "Bearish" if score < -0.1 else "Neutral"
                    print(f"   {asset:>4}: {sentiment_label:>8} (score: {score:>6.3f}, articles: {count:>3})")
                
                return True
            else:
                print("\n⚠️  PRODUCTION HAS NO SENTIMENT DATA")
                print("📝 This could mean:")
                print("   - FINNHUB_API_KEY is not set in Render environment")
                print("   - API key is invalid or expired")
                print("   - Temporary API issues")
                print("   - No relevant news articles found recently")
                
                return False
                
        else:
            print(f"❌ Sentiment endpoint failed with status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - the service might be slow or unavailable")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 Connection failed - check if the Render service is running")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_other_endpoints():
    """Test other endpoints to verify the service is working"""
    print("\n🔍 Testing Other Endpoints:")
    
    endpoints_to_test = [
        "/health",
        "/status", 
        "/api/health",
        "/"
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_test:
        try:
            url = f"{RENDER_API_URL}{endpoint}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - Working")
                working_endpoints.append(endpoint)
            else:
                print(f"   ❌ {endpoint} - Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {str(e)[:50]}...")
    
    return len(working_endpoints) > 0

def check_render_environment_vars():
    """Instructions for checking Render environment variables"""
    print("\n🔧 RENDER ENVIRONMENT VARIABLE CHECK")
    print("=" * 50)
    print("To verify your Render environment setup:")
    print()
    print("1. Go to your Render Dashboard")
    print("2. Select your service (bottie-api)")
    print("3. Click on 'Environment' tab")
    print("4. Look for these variables:")
    print("   ✅ FINNHUB_API_KEY (should be set)")
    print("   ✅ SENTIMENT_ENABLED=1")
    print("   ✅ SENTIMENT_SOURCE=finnhub")
    print()
    print("5. If FINNHUB_API_KEY is missing:")
    print("   - Add it with your real Finnhub API key")
    print("   - Get free key from: https://finnhub.io")
    print("   - Redeploy the service after adding")
    print()
    print("6. Check the logs:")
    print("   - Look for sentiment-related messages")
    print("   - Should NOT see 'FINNHUB_API_KEY is missing' warnings")

def main():
    """Main test function"""
    print(f"🧪 Testing Production Sentiment Analysis")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test if service is accessible
    service_working = test_other_endpoints()
    
    if not service_working:
        print("\n❌ Service appears to be down or inaccessible")
        print(f"   Check if {RENDER_API_URL} is correct")
        print("   Verify your Render service is deployed and running")
        return False
    
    # Test sentiment analysis
    has_real_data = test_production_sentiment()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FINAL ASSESSMENT")
    print("=" * 50)
    
    if has_real_data:
        print("🎉 SUCCESS: Your sentiment analysis is using REAL DATA!")
        print("✅ The system is fetching live cryptocurrency news")
        print("✅ Sentiment scores are based on actual market sentiment")
        print("✅ Your Render deployment is properly configured")
    else:
        print("❌ ISSUE: Your sentiment analysis is NOT using real data")
        print("📝 The system is returning neutral/empty sentiment scores")
        print("🔧 This needs to be fixed for accurate trading signals")
        
        # Provide troubleshooting steps
        check_render_environment_vars()
    
    print("\n💡 Next Steps:")
    if has_real_data:
        print("   - Your sentiment analysis is working correctly!")
        print("   - Monitor the sentiment scores in your trading dashboard")
        print("   - Consider adjusting sentiment thresholds if needed")
    else:
        print("   1. Check/add FINNHUB_API_KEY in Render environment")
        print("   2. Redeploy your Render service")
        print("   3. Run this test again to verify")
        print("   4. Check Render logs for any errors")
    
    return has_real_data

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)