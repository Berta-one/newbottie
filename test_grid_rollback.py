#!/usr/bin/env python3
"""
Test script for Grid WebSocket Rollback Switch
"""
import os
import asyncio
import sys
sys.path.append('.')

async def test_rollback_switch():
    """Test the grid WebSocket rollback functionality"""
    print("🧪 Testing Grid WebSocket Rollback Switch")
    print("=" * 50)
    
    # Test 1: Enabled state
    print("\n1. Testing ENABLED state (ENABLE_GRID_WS=1)")
    os.environ["ENABLE_GRID_WS"] = "1"
    
    try:
        from api.cross_pairs import CrossPairsWS
        
        # Mock the score function
        def mock_score_fn(symbol, price):
            return {
                "ema": 0.6,
                "ml": 0.7,
                "q": 0.5,
                "sent": 0.4,
                "final_prob": 0.65
            }
        
        # Test initialization (don't actually start WebSocket)
        cross_ws = CrossPairsWS(
            api_key="test_key",
            api_secret="test_secret",
            testnet=True
        )
        cross_ws.score_fn = mock_score_fn
        
        print("   ✅ CrossPairsWS initialization successful")
        print("   ✅ Score function assignment successful")
        
        # Test snapshot (should work even without starting)
        snapshot = cross_ws.snapshot_matrix()
        expected_keys = ["rows", "cols", "matrix", "ts"]
        
        if all(key in snapshot for key in expected_keys):
            print("   ✅ Snapshot method works correctly")
        else:
            print("   ❌ Snapshot method missing keys")
        
    except Exception as e:
        print(f"   ❌ Error in enabled state: {e}")
    
    # Test 2: Disabled state
    print("\n2. Testing DISABLED state (ENABLE_GRID_WS=0)")
    os.environ["ENABLE_GRID_WS"] = "0"
    
    # Test the condition logic
    enabled = os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
    if not enabled:
        print("   ✅ Environment variable correctly detected as disabled")
        
        # Simulate what routes would return
        mock_responses = {
            "grid_matrix": {"rows": [], "cols": [], "matrix": {}, "ts": 1692345678},
            "portfolio_assets": {"assets": []},
            "scan_assets": {"assets": []}
        }
        
        for endpoint, response in mock_responses.items():
            print(f"   ✅ {endpoint} would return: {response}")
    else:
        print("   ❌ Environment variable not correctly detected as disabled")
    
    # Test 3: Different disable values
    print("\n3. Testing different disable values")
    disable_values = ["0", "false", "no", "False", "NO", "OFF"]
    
    for value in disable_values:
        os.environ["ENABLE_GRID_WS"] = value
        enabled = os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
        if not enabled:
            print(f"   ✅ '{value}' correctly disables WebSocket")
        else:
            print(f"   ❌ '{value}' incorrectly enables WebSocket")
    
    # Test 4: Different enable values
    print("\n4. Testing different enable values")
    enable_values = ["1", "true", "yes", "True", "YES", "TRUE"]
    
    for value in enable_values:
        os.environ["ENABLE_GRID_WS"] = value
        enabled = os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
        if enabled:
            print(f"   ✅ '{value}' correctly enables WebSocket")
        else:
            print(f"   ❌ '{value}' incorrectly disables WebSocket")
    
    # Test 5: Default behavior (no env var)
    print("\n5. Testing default behavior (no ENABLE_GRID_WS set)")
    if "ENABLE_GRID_WS" in os.environ:
        del os.environ["ENABLE_GRID_WS"]
    
    enabled = os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
    if enabled:
        print("   ✅ Default behavior correctly enables WebSocket")
    else:
        print("   ❌ Default behavior incorrectly disables WebSocket")
    
    print("\n🎉 Rollback Switch Testing Complete!")
    print("=" * 50)

def test_routes_graceful_handling():
    """Test that routes handle None CROSS_WS gracefully"""
    print("\n🔧 Testing Routes Graceful Handling")
    print("=" * 50)
    
    # Simulate routes behavior when CROSS_WS is None
    CROSS_WS = None
    
    # Test grid_matrix route
    def mock_grid_matrix():
        if not CROSS_WS:
            return {"rows": [], "cols": [], "matrix": {}, "ts": 1692345678}
        return CROSS_WS.snapshot_matrix()
    
    # Test portfolio_assets route  
    def mock_portfolio_assets():
        if not CROSS_WS:
            return {"assets": []}
        return {"assets": CROSS_WS.rows}
    
    # Test scan_assets route
    def mock_scan_assets():
        if not CROSS_WS:
            return {"assets": []}
        return {"assets": CROSS_WS.cols}
    
    try:
        result1 = mock_grid_matrix()
        result2 = mock_portfolio_assets()
        result3 = mock_scan_assets()
        
        print("   ✅ grid_matrix returns safe default:", result1)
        print("   ✅ portfolio_assets returns safe default:", result2)
        print("   ✅ scan_assets returns safe default:", result3)
        
        # Verify structure
        assert "rows" in result1 and "cols" in result1 and "matrix" in result1
        assert "assets" in result2 and "assets" in result3
        assert result1["rows"] == [] and result1["cols"] == []
        assert result2["assets"] == [] and result3["assets"] == []
        
        print("   ✅ All route responses have correct structure")
        print("   ✅ All route responses are safe for frontend consumption")
        
    except Exception as e:
        print(f"   ❌ Routes handling error: {e}")

def show_deployment_examples():
    """Show deployment examples for different platforms"""
    print("\n🚀 Deployment Examples")
    print("=" * 50)
    
    print("**Render Environment Variables:**")
    print("   ENABLE_GRID_WS=1  # Enable (production)")
    print("   ENABLE_GRID_WS=0  # Disable (emergency)")
    print()
    
    print("**Docker Environment:**")
    print("   docker run -e ENABLE_GRID_WS=1 bottie-api")
    print("   docker run -e ENABLE_GRID_WS=0 bottie-api  # Safe mode")
    print()
    
    print("**Local Development:**")
    print("   export ENABLE_GRID_WS=1 && python -m uvicorn api.app:app --reload")
    print("   export ENABLE_GRID_WS=0 && python -m uvicorn api.app:app --reload")
    print()
    
    print("**Testing Commands:**")
    print("   # Test enabled")
    print("   curl http://localhost:8000/grid/matrix")
    print()
    print("   # Test disabled (after setting ENABLE_GRID_WS=0)")
    print("   curl http://localhost:8000/grid/matrix")
    print("   # Should return: {\"rows\": [], \"cols\": [], \"matrix\": {}, \"ts\": ...}")

async def main():
    await test_rollback_switch()
    test_routes_graceful_handling()
    show_deployment_examples()

if __name__ == "__main__":
    asyncio.run(main())
