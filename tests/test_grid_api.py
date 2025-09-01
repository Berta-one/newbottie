#!/usr/bin/env python3
"""
Quick test for the new grid WebSocket API endpoints
"""

import asyncio
import json
import time
import requests

# Test the new grid endpoints
API_BASE = "http://localhost:8000"  # Adjust if different

def test_grid_endpoints():
    """Test the new grid API endpoints"""
    
    print("🧪 Testing Grid API Endpoints")
    print("=" * 50)
    
    endpoints = [
        "/grid/matrix",
        "/portfolio/assets", 
        "/scan/assets"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n📍 Testing {endpoint}")
            response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"📊 Response keys: {list(data.keys())}")
                
                if endpoint == "/grid/matrix":
                    print(f"   📈 Rows: {len(data.get('rows', []))}")
                    print(f"   📊 Cols: {len(data.get('cols', []))}")
                    print(f"   🎯 Matrix symbols: {len(data.get('matrix', {}))}")
                    
                    # Show sample matrix entry if available
                    matrix = data.get('matrix', {})
                    if matrix:
                        for base, quotes in list(matrix.items())[:2]:
                            for quote, signal_data in list(quotes.items())[:2]:
                                print(f"   🔍 Sample {base}/{quote}: {signal_data.get('signal', 'N/A')} @ {signal_data.get('conf', 0):.3f}")
                
                elif endpoint in ["/portfolio/assets", "/scan/assets"]:
                    assets = data.get('assets', [])
                    print(f"   💼 Assets count: {len(assets)}")
                    if assets:
                        print(f"   📋 Sample assets: {assets[:5]}")
                        
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - Is the API server running on {API_BASE}?")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎉 Grid API test complete!")

if __name__ == "__main__":
    test_grid_endpoints()
