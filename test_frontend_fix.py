#!/usr/bin/env python3
"""
Test script to verify frontend compatibility fixes
"""

import requests
import json
import time

API_BASE = "https://bottie-1.onrender.com"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    try:
        url = f"{API_BASE}{endpoint}"
        print(f"Testing {method} {url}")
        
        if method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        print(f"✅ Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2)[:200]}...")
        else:
            print(f"❌ Error response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("🔍 Testing Frontend Compatibility...")
    print("=" * 50)
    
    # Test basic endpoints
    test_endpoint("/")
    test_endpoint("/health")
    test_endpoint("/status")
    
    # Test debug endpoints that frontend needs
    test_endpoint("/debug/auth")
    
    # Test authentication with correct password
    test_endpoint("/auth/login", "POST", {"username": "admin", "password": "Diego1234!"})
    
    # Test grid matrix
    test_endpoint("/grid/matrix")
    
    print("\n🔍 Frontend Tests Complete!")

if __name__ == "__main__":
    main()
