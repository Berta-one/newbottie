#!/usr/bin/env python3
"""
Test deployment configuration locally
"""

import subprocess
import time
import requests
import sys

def test_deployment():
    """Test the deployment configuration"""
    print("🧪 Testing deployment configuration...")
    
    # Test 1: Check if requirements install
    print("\n1. Testing requirements installation...")
    try:
        result = subprocess.run([
            'pip', 'install', '--no-cache-dir', '-r', 'requirements-deploy.txt'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Requirements install successfully")
        else:
            print(f"❌ Requirements install failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Requirements test error: {e}")
        return False
    
    # Test 2: Check if script imports
    print("\n2. Testing script imports...")
    try:
        import deploy_ready
        print("✅ deploy_ready.py imports successfully")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test 3: Test health endpoint simulation
    print("\n3. Testing API endpoints...")
    try:
        from deploy_ready import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ Health endpoint works")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test main endpoint
        response = client.get("/")
        if response.status_code == 200:
            print("✅ Main endpoint works")
        else:
            print(f"❌ Main endpoint failed: {response.status_code}")
            return False
        
        # Test status endpoint
        response = client.get("/status")
        if response.status_code == 200:
            print("✅ Status endpoint works")
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False
    
    print("\n🎉 ALL DEPLOYMENT TESTS PASSED!")
    print("✅ Your deployment configuration is ready for Render!")
    return True

if __name__ == "__main__":
    success = test_deployment()
    sys.exit(0 if success else 1)