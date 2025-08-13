#!/usr/bin/env python3
"""
Quick test for cross-pair trading endpoints on Render
"""

import requests

def test_render_cross_pairs():
    base_url = "https://bottie-1.onrender.com"
    
    endpoints = [
        "/cross-pairs/status",
        "/portfolio/cross-pairs", 
        "/cross-pairs/opportunities",
        "/portfolio/rebalancing-suggestions"
    ]
    
    print("🔄 Testing Cross-Pair Endpoints on Render...")
    print("=" * 50)
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint} - {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "enabled" in data:
                    enabled = "ON" if data["enabled"] else "OFF"
                    print(f"   Status: {enabled}")
                if "count" in data:
                    print(f"   Count: {data['count']}")
                    
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    print("\n🎯 If all endpoints show ✅, cross-pair trading is deployed!")
    print("🚀 Your Bottie now has advanced cross-pair trading capabilities!")

if __name__ == "__main__":
    test_render_cross_pairs()
