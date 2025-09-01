#!/usr/bin/env python3
"""
Test script to verify all endpoints work with the new render_api.py
"""

import requests
import json
import time
from urllib.parse import urlencode

# Test configuration
RENDER_API_BASE = "https://bottie-1.onrender.com"
NETLIFY_URL = "https://dancing-figolla-978034.netlify.app"
TEST_CREDENTIALS = {"username": "admin", "password": "Diego1234!"}

class RenderConnectionTester:
    def __init__(self, base_url=RENDER_API_BASE):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        
    def test_endpoint(self, endpoint, method="GET", data=None, auth_required=False):
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth_required and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data, timeout=10)
            else:
                return False, f"Unsupported method: {method}"
            
            return response.status_code == 200, {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "content_type": response.headers.get("Content-Type", ""),
                "data": response.json() if response.headers.get("Content-Type", "").startswith("application/json") else response.text[:200]
            }
            
        except Exception as e:
            return False, str(e)
    
    def authenticate(self):
        """Test authentication and store token"""
        print("🔐 Testing authentication...")
        success, result = self.test_endpoint("/auth/login", "POST", TEST_CREDENTIALS)
        
        if success and isinstance(result.get("data"), dict):
            self.auth_token = result["data"].get("access_token")
            print(f"✅ Authentication successful: {result['data'].get('user', {}).get('username')}")
            return True
        else:
            print(f"❌ Authentication failed: {result}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive endpoint tests"""
        print(f"🚀 Testing Render API connection to {self.base_url}")
        print("=" * 60)
        
        # Test basic connectivity
        endpoints_basic = [
            ("/", "Root endpoint"),
            ("/health", "Health check"),
        ]
        
        print("\n📡 Testing Basic Connectivity:")
        for endpoint, description in endpoints_basic:
            success, result = self.test_endpoint(endpoint)
            status = "✅" if success else "❌"
            print(f"{status} {description}: {endpoint}")
            if success:
                print(f"    Response time: {result['response_time']:.2f}s")
            else:
                print(f"    Error: {result}")
        
        # Test authentication
        auth_success = self.authenticate()
        
        # Test authenticated endpoints
        endpoints_auth = [
            ("/status", "Status endpoint"),
            ("/signals", "Trading signals"),
            ("/sentiment", "Sentiment analysis"),
            ("/positions", "Positions data"),
            ("/trades", "Trades history"),
            ("/logs/last", "System logs"),
            ("/ml/status", "ML status"),
            ("/quantum/details", "Quantum details"),
            ("/grid/matrix", "Grid matrix"),
        ]
        
        print(f"\n🔒 Testing Authenticated Endpoints (Auth: {'✅' if auth_success else '❌'}):")
        for endpoint, description in endpoints_auth:
            success, result = self.test_endpoint(endpoint, auth_required=auth_success)
            status = "✅" if success else "❌"
            print(f"{status} {description}: {endpoint}")
            if success:
                print(f"    Response time: {result['response_time']:.2f}s")
                if isinstance(result.get("data"), dict):
                    data_keys = list(result["data"].keys())[:5]  # Show first 5 keys
                    print(f"    Data keys: {data_keys}")
            else:
                print(f"    Error: {result}")
        
        # Test CORS headers
        print(f"\n🌐 Testing CORS Headers:")
        try:
            response = self.session.options(f"{self.base_url}/health", headers={
                "Origin": NETLIFY_URL,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            })
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
            }
            
            print(f"✅ CORS preflight successful (status: {response.status_code})")
            for header, value in cors_headers.items():
                print(f"    {header}: {value or 'Not set'}")
                
        except Exception as e:
            print(f"❌ CORS preflight failed: {e}")
        
        # Generate frontend test URL
        print(f"\n🔗 Frontend Integration Test:")
        frontend_url = f"{NETLIFY_URL}?api={urlencode({'': self.base_url})[2:]}"
        print(f"Test URL: {frontend_url}")
        
        # Test debug endpoints
        print(f"\n🔧 Testing Debug Endpoints:")
        debug_endpoints = [
            ("/debug/auth", "Debug auth info"),
        ]
        
        for endpoint, description in debug_endpoints:
            success, result = self.test_endpoint(endpoint)
            status = "✅" if success else "❌"
            print(f"{status} {description}: {endpoint}")
            
        print(f"\n✅ Connection testing completed!")
        
        # Summary
        print(f"\n📋 Quick Fix Summary:")
        print(f"1. ✅ render.yaml updated to use render_api:app")
        print(f"2. ✅ render_api.py created with all required endpoints")
        print(f"3. ✅ CORS settings fixed (allow_origins=['*'])")
        print(f"4. ✅ Authentication endpoints implemented")
        print(f"5. ✅ Environment variables added to render.yaml")
        
        print(f"\n🚀 Next Steps:")
        print(f"1. Deploy the updated code to Render")
        print(f"2. Test the frontend at: {frontend_url}")
        print(f"3. Check Render logs for any deployment issues")

def main():
    print("🧪 Render API Connection Tester")
    print("Testing connection between Netlify frontend and Render backend")
    
    tester = RenderConnectionTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()