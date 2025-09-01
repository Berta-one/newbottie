#!/usr/bin/env python3
"""
Test script for Bottie ML monitoring endpoints
"""

import requests
import json
import sys

def test_ml_endpoints(api_url="http://localhost:8000"):
    """Test the ML monitoring endpoints"""
    
    print("🧠 Testing Bottie ML Monitoring Endpoints")
    print("=" * 50)
    
    # Test /ml/status endpoint
    print("\n📊 Testing /ml/status endpoint...")
    try:
        response = requests.get(f"{api_url}/ml/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ /ml/status endpoint working!")
            print(f"   Sample Count: {data.get('sample_count', 'N/A')}")
            print(f"   Brier Score: {data.get('brier_score', 'N/A')}")
            print(f"   Accuracy: {data.get('accuracy', 'N/A')}")
            print(f"   Quantum Mode: {data.get('quantum_mode', 'N/A')}")
            print(f"   Quantum Rank: #{data.get('quantum_feature_rank', 'N/A')}")
            
            if data.get('feature_importance'):
                print("   Feature Importance:")
                for feature, importance in data['feature_importance'].items():
                    print(f"     {feature}: {importance:.3f}")
        else:
            print(f"❌ /ml/status endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ /ml/status endpoint error: {e}")
    
    # Test /metrics/components endpoint
    print("\n📈 Testing /metrics/components endpoint...")
    try:
        response = requests.get(f"{api_url}/metrics/components", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ /metrics/components endpoint working!")
            print(f"   Quantum Mode: {data.get('quantum_mode', 'N/A')}")
            
            performance = data.get('performance', {})
            if performance.get('brier_loss'):
                print("   Brier Losses:")
                for component, loss in performance['brier_loss'].items():
                    print(f"     {component}: {loss}")
                    
            if performance.get('sample_counts'):
                print("   Sample Counts:")
                for component, count in performance['sample_counts'].items():
                    print(f"     {component}: {count}")
        else:
            print(f"❌ /metrics/components endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ /metrics/components endpoint error: {e}")
    
    # Test basic health endpoint
    print("\n🏥 Testing /health endpoint...")
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ /health endpoint working!")
        else:
            print(f"❌ /health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ /health endpoint error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test complete! If all endpoints show ✅, you're ready to run the ML monitor.")
    print("🚀 Run: python ml_monitor.py --continuous")

if __name__ == "__main__":
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_ml_endpoints(api_url)
