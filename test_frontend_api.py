import os
import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_api():
    print("🔍 Testing API components...")
    
    # Set environment
    os.environ["ENVIRONMENT"] = "production"
    os.environ["TRADE_ENABLED"] = "1"
    
    try:
        # Test basic imports
        print("📦 Testing imports...")
        from api.app import app
        print("✅ API app imported")
        
        # Test FastAPI directly
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        print("🔍 Testing status endpoint...")
        response = client.get("/status")
        print(f"Status response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Real equity: ${data.get('equity', 0):.2f}")
            print(f"✅ Mode: {data.get('mode', 'Unknown')}")
            print(f"✅ Exchange: {data.get('exchange', 'Unknown')}")
        else:
            print(f"❌ Status error: {response.text}")
            
        print("🔍 Testing positions endpoint...")
        response = client.get("/account/positions")
        print(f"Positions response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            positions = data.get('positions', [])
            print(f"✅ Found {len(positions)} real positions")
            for pos in positions[:3]:  # Show first 3
                print(f"  - {pos.get('symbol')}: ${pos.get('market_value', 0):.2f}")
        else:
            print(f"❌ Positions error: {response.text}")
            
        print("🔍 Testing quantum endpoint...")
        response = client.get("/quantum/details")
        print(f"Quantum response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Quantum backend: {data.get('backend', 'Unknown')}")
        else:
            print(f"❌ Quantum error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api())
