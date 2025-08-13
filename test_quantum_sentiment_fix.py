#!/usr/bin/env python3
"""Test script to verify quantum and sentiment are now properly enabled"""

import requests
import os
import sys
from datetime import datetime

def test_environment_variables():
    """Test environment variable parsing"""
    print("🔧 Environment Variable Status:")
    print(f"   QUANTUM_ENABLED (env): {os.getenv('QUANTUM_ENABLED', 'NOT_SET')}")
    print(f"   SENTIMENT_ENABLED (env): {os.getenv('SENTIMENT_ENABLED', 'NOT_SET')}")
    
    # Test with local import
    try:
        from api.app import QUANTUM_ENABLED, SENTIMENT_ENABLED, QUANTUM_BACKEND
        print(f"   QUANTUM_ENABLED (parsed): {QUANTUM_ENABLED}")
        print(f"   SENTIMENT_ENABLED (parsed): {SENTIMENT_ENABLED}")
        print(f"   QUANTUM_BACKEND: {QUANTUM_BACKEND}")
        return True
    except Exception as e:
        print(f"   ❌ Error importing config: {e}")
        return False

def test_quantum_endpoint():
    """Test quantum analysis endpoint"""
    print("\n🔬 Quantum Analysis Test:")
    try:
        response = requests.get("http://localhost:8000/quantum/analysis", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ Enabled: {data.get('enabled', False)}")
            print(f"   ✅ Status: {data.get('status', 'unknown')}")
            print(f"   ✅ Backend: {data.get('backend', 'unknown')}")
            
            if data.get('enabled'):
                circuit_info = data.get('circuit_info', {})
                print(f"   ✅ Circuit Info: {len(circuit_info)} parameters")
                if circuit_info:
                    print(f"      - Qubits: {circuit_info.get('qubits_count', 'N/A')}")
                    print(f"      - Depth: {circuit_info.get('depth', 'N/A')}")
                    print(f"      - Fidelity: {circuit_info.get('fidelity', 'N/A')}")
            
            return data.get('enabled', False)
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Request Error: {e}")
        return False

def test_sentiment_endpoint():
    """Test sentiment articles endpoint"""
    print("\n📰 Sentiment Analysis Test:")
    try:
        response = requests.get("http://localhost:8000/sentiment/articles", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ Enabled: {data.get('enabled', False)}")
            
            articles = data.get('articles', [])
            print(f"   ✅ Articles Available: {len(articles)}")
            
            summary = data.get('summary', {})
            print(f"   ✅ Summary Keys: {list(summary.keys())}")
            
            # Test regular sentiment endpoint too
            response2 = requests.get("http://localhost:8000/sentiment", timeout=10)
            if response2.status_code == 200:
                sentiment_data = response2.json()
                print(f"   ✅ Main Sentiment Endpoint: {sentiment_data.get('enabled', False)}")
            
            return data.get('enabled', False)
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Request Error: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint to see overall system status"""
    print("\n🏥 Health Endpoint Test:")
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ✅ Service Status: {data.get('status', 'unknown')}")
            
            quantum_health = data.get('quantum', {})
            sentiment_health = data.get('sentiment', {})
            
            print(f"   ✅ Quantum Health: {quantum_health}")
            print(f"   ✅ Sentiment Health: {sentiment_health}")
            
            return True
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Request Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 QUANTUM & SENTIMENT ENABLEMENT TEST")
    print("=" * 60)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    env_ok = test_environment_variables()
    quantum_ok = test_quantum_endpoint() 
    sentiment_ok = test_sentiment_endpoint()
    health_ok = test_health_endpoint()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print("=" * 60)
    
    results = [
        ("Environment Variables", env_ok),
        ("Quantum Analysis", quantum_ok),
        ("Sentiment Analysis", sentiment_ok),  
        ("Health Endpoint", health_ok)
    ]
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name:.<30} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Quantum and Sentiment are now properly enabled!")
        print("🚀 Dashboard should now show both features as active when deployed to Render")
    else:
        print("\n⚠️  Some tests failed. Check the details above.")
        
    print("\n💡 Next Steps:")
    print("   1. Deploy to Render with QUANTUM_ENABLED=1 and SENTIMENT_ENABLED=1")
    print("   2. Verify dashboard shows both features as enabled")
    print("   3. Check quantum circuit analysis displays properly")
    print("   4. Confirm sentiment articles are being processed")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
