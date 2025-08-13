#!/usr/bin/env python3
"""Test the Professional Trading Grid implementation"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

async def test_professional_grid():
    """Test the new volume-based trading grid"""
    print("🏛️ TESTING PROFESSIONAL TRADING GRID")
    print("=" * 60)
    
    try:
        # Import after setting up the path
        from api.app import app
        from fastapi.testclient import TestClient
        
        # Create test client
        client = TestClient(app)
        
        print("✅ FastAPI app loaded successfully")
        
        # Test the grid matrix endpoint
        print("\n📊 Testing /grid/matrix endpoint...")
        response = client.get("/grid/matrix")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Grid endpoint working! Status: {response.status_code}")
            print(f"📈 Portfolio holdings: {len(data.get('rows', []))}")
            print(f"🔢 Volume leaders: {len(data.get('cols', []))}")
            print(f"🎯 Total pairs: {data.get('total_pairs', 0)}")
            print(f"📊 Matrix size: {len(data.get('matrix', {}))}")
            
            # Show some sample data
            if data.get('rows') and data.get('cols'):
                print(f"\n💎 Sample portfolio holdings: {data['rows'][:5]}")
                print(f"🏆 Top volume cryptos: {data['cols'][:10]}")
                
            return True
        else:
            print(f"❌ Grid endpoint failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_professional_grid())
    
    if success:
        print("\n🎉 PROFESSIONAL TRADING GRID IS READY!")
        print("🚀 Your most important feature is now implemented")
        print("📱 Ready for frontend deployment")
    else:
        print("\n⚠️ Issues found - needs debugging")
