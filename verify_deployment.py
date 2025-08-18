#!/usr/bin/env python3
"""
Verify that the CORS fix deployment is working correctly
"""

import requests
import json
import time

def test_cors_fix():
    """Test if the CORS fix is working"""
    
    print("🔍 Testing CORS Fix Deployment")
    print("=" * 50)
    
    # Test the main site
    sites_to_test = [
        "https://sntax.netlify.app",
        "https://dancing-figolla-978034.netlify.app"
    ]
    
    for site_url in sites_to_test:
        print(f"\n🌐 Testing: {site_url}")
        
        try:
            # Test if the site loads
            response = requests.get(site_url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Site loads successfully (Status: {response.status_code})")
                
                # Check if our fixed reports.js is present
                if 'v2024-01-17-fallback' in response.text:
                    print("✅ CORS fix version detected in HTML")
                else:
                    print("⚠️  CORS fix version not found - may need to deploy")
                    
            else:
                print(f"❌ Site returned status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect: {e}")
            continue
    
    print(f"\n🔧 Backend API Test")
    print("-" * 30)
    
    # Test the backend API directly
    backend_url = "https://bottie-1.onrender.com"
    endpoints_to_test = [
        "/health",
        "/api/trades", 
        "/api/ml/status",
        "/status"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            url = f"{backend_url}{endpoint}"
            response = requests.get(url, timeout=10)
            print(f"{'✅' if response.status_code == 200 else '⚠️'} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Failed - {e}")
    
    print(f"\n📋 Summary")
    print("-" * 30)
    print("If you see ✅ for site loading and backend endpoints, the CORS fix should work!")
    print("If you see ⚠️ for 'CORS fix version not found', please deploy the files.")
    print("\n🚀 To deploy: Go to Netlify Dashboard → sntax.netlify.app → Deploys → Drag /workspace/reports-deploy-clean/")

if __name__ == "__main__":
    test_cors_fix()