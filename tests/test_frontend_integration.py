#!/usr/bin/env python3
"""Test script to verify frontend integrates properly with enhanced quantum and sentiment"""

import requests
import sys
from datetime import datetime

def test_frontend_endpoints():
    """Test the API endpoints that the frontend uses"""
    print("🌐 Frontend Integration Test")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        ("/health", "Health Check - Shows quantum and sentiment status"),
        ("/quantum/analysis", "Enhanced Quantum Analysis - Circuit info and metrics"),
        ("/sentiment/articles", "Enhanced Sentiment Articles - Real articles display"),
        ("/ml/status", "ML Status - Dynamic sample counting and Brier scores"),
        ("/trades", "Enhanced Trades - Accurate P&L calculations")
    ]
    
    results = []
    
    for endpoint, description in endpoints_to_test:
        print(f"\n🔍 Testing {endpoint}")
        print(f"   Description: {description}")
        
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Specific checks for each endpoint
                if endpoint == "/health":
                    quantum_enabled = data.get("quantum", {}).get("enabled", False)
                    sentiment_enabled = data.get("sentiment", {}).get("enabled", False)
                    print(f"   ✅ Quantum Enabled: {quantum_enabled}")
                    print(f"   ✅ Sentiment Enabled: {sentiment_enabled}")
                    results.append(("Health Check", True, f"Q:{quantum_enabled}, S:{sentiment_enabled}"))
                
                elif endpoint == "/quantum/analysis":
                    enabled = data.get("enabled", False)
                    status = data.get("status", "unknown")
                    circuit_info = data.get("circuit_info", {})
                    print(f"   ✅ Quantum Enabled: {enabled}")
                    print(f"   ✅ Status: {status}")
                    print(f"   ✅ Circuit Info Keys: {list(circuit_info.keys())}")
                    results.append(("Quantum Analysis", enabled, f"Status: {status}"))
                
                elif endpoint == "/sentiment/articles":
                    enabled = data.get("enabled", False)
                    articles = data.get("articles", [])
                    print(f"   ✅ Sentiment Enabled: {enabled}")
                    print(f"   ✅ Articles Available: {len(articles)}")
                    if articles:
                        print(f"   ✅ First Article: {articles[0].get('headline', 'No headline')[:50]}...")
                    results.append(("Sentiment Articles", enabled, f"{len(articles)} articles"))
                
                elif endpoint == "/ml/status":
                    sample_count = data.get("sample_count", 0)
                    brier_score = data.get("brier_score", None)
                    print(f"   ✅ Sample Count: {sample_count}")
                    print(f"   ✅ Brier Score: {brier_score}")
                    results.append(("ML Status", sample_count > 0, f"Samples: {sample_count}"))
                
                elif endpoint == "/trades":
                    trade_count = data.get("trade_count", 0)
                    net_pnl = data.get("net_pnl", 0)
                    print(f"   ✅ Trade Count: {trade_count}")
                    print(f"   ✅ Net P&L: {net_pnl}")
                    results.append(("Trades API", True, f"Trades: {trade_count}"))
                
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                results.append((endpoint, False, f"HTTP {response.status_code}"))
                
        except Exception as e:
            print(f"   ❌ Request Failed: {e}")
            results.append((endpoint, False, f"Error: {str(e)[:30]}"))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FRONTEND INTEGRATION SUMMARY")
    print("=" * 50)
    
    for test_name, passed, details in results:
        status = "✅ WORKING" if passed else "❌ FAILED"
        print(f"   {test_name:.<25} {status}")
        print(f"      Details: {details}")
    
    all_passed = all(result[1] for result in results)
    
    print(f"\n🎯 Overall Status: {'✅ ALL SYSTEMS GO' if all_passed else '⚠️ SOME ISSUES DETECTED'}")
    
    print("\n💡 Frontend Integration Notes:")
    print("   • Dashboard should now show quantum and sentiment as enabled")
    print("   • Sentiment section should display actual news articles")
    print("   • Quantum analysis should show circuit information")
    print("   • ML health should show dynamic sample counts")
    print("   • All status chips should reflect the enabled state")
    
    return all_passed

def main():
    print(f"Frontend Integration Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    success = test_frontend_endpoints()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
