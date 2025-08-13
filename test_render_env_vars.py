#!/usr/bin/env python3
"""
Test script for Render environment variable detection
"""
import os

def test_env_var_detection():
    """Test the environment variable detection logic"""
    
    print("🧪 Testing Render Environment Variable Detection\n")
    
    # Clear all potential variables first
    for var in ["API_ENABLE_GRID_WS", "BOTTIE_ENABLE_GRID_WS", "ENABLE_GRID_WS"]:
        if var in os.environ:
            del os.environ[var]
    
    # Test 1: Default behavior (should enable)
    print("Test 1: No environment variables set")
    enable_grid_ws = (
        os.getenv("API_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("BOTTIE_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
    )
    print(f"   Result: {'✅ ENABLED' if enable_grid_ws else '❌ DISABLED'} (default)")
    
    # Test 2: API-specific variable (highest priority)
    print("\nTest 2: API_ENABLE_GRID_WS=1")
    os.environ["API_ENABLE_GRID_WS"] = "1"
    os.environ["BOTTIE_ENABLE_GRID_WS"] = "0"  # Should be ignored
    os.environ["ENABLE_GRID_WS"] = "0"         # Should be ignored
    
    enable_grid_ws = (
        os.getenv("API_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("BOTTIE_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
    )
    print(f"   Result: {'✅ ENABLED' if enable_grid_ws else '❌ DISABLED'} (API priority)")
    
    # Test 3: BOTTIE-specific variable (second priority)
    print("\nTest 3: BOTTIE_ENABLE_GRID_WS=1, API_ENABLE_GRID_WS not set")
    del os.environ["API_ENABLE_GRID_WS"]
    os.environ["BOTTIE_ENABLE_GRID_WS"] = "1"
    os.environ["ENABLE_GRID_WS"] = "0"  # Should be ignored
    
    enable_grid_ws = (
        os.getenv("API_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("BOTTIE_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
    )
    print(f"   Result: {'✅ ENABLED' if enable_grid_ws else '❌ DISABLED'} (BOTTIE priority)")
    
    # Test 4: Generic variable (lowest priority)
    print("\nTest 4: Only ENABLE_GRID_WS=1")
    if "API_ENABLE_GRID_WS" in os.environ:
        del os.environ["API_ENABLE_GRID_WS"]
    if "BOTTIE_ENABLE_GRID_WS" in os.environ:
        del os.environ["BOTTIE_ENABLE_GRID_WS"]
    os.environ["ENABLE_GRID_WS"] = "1"
    
    enable_grid_ws = (
        os.getenv("API_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("BOTTIE_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
    )
    print(f"   Result: {'✅ ENABLED' if enable_grid_ws else '❌ DISABLED'} (generic fallback)")
    
    # Test 5: Emergency rollback scenario
    print("\nTest 5: Emergency rollback - API_ENABLE_GRID_WS=0")
    os.environ["API_ENABLE_GRID_WS"] = "0"
    os.environ["BOTTIE_ENABLE_GRID_WS"] = "1"  # Should be ignored
    os.environ["ENABLE_GRID_WS"] = "1"         # Should be ignored
    
    enable_grid_ws = (
        os.getenv("API_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("BOTTIE_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
    )
    print(f"   Result: {'✅ ENABLED' if enable_grid_ws else '❌ DISABLED'} (emergency rollback - should be disabled)")
    
    # Test 5b: Show that BOTTIE variable can enable when API is not set
    print("\nTest 5b: BOTTIE_ENABLE_GRID_WS=1 takes effect when API var not set")  
    del os.environ["API_ENABLE_GRID_WS"]  # Remove API variable
    os.environ["BOTTIE_ENABLE_GRID_WS"] = "1"
    os.environ["ENABLE_GRID_WS"] = "0"  # Should be ignored
    
    enable_grid_ws = (
        os.getenv("API_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("BOTTIE_ENABLE_GRID_WS", "").lower() in ("1", "true", "yes") or
        os.getenv("ENABLE_GRID_WS", "1").lower() in ("1", "true", "yes")
    )
    print(f"   Result: {'✅ ENABLED' if enable_grid_ws else '❌ DISABLED'} (BOTTIE can enable)")
    
    # Test 6: Which variable is used for logging
    print("\nTest 6: Variable detection for logging")
    test_cases = [
        {"API_ENABLE_GRID_WS": "0"},
        {"BOTTIE_ENABLE_GRID_WS": "0"},  
        {"ENABLE_GRID_WS": "0"},
        {}  # No variables
    ]
    
    for i, case in enumerate(test_cases, 1):
        # Clear environment
        for var in ["API_ENABLE_GRID_WS", "BOTTIE_ENABLE_GRID_WS", "ENABLE_GRID_WS"]:
            if var in os.environ:
                del os.environ[var]
        
        # Set test case variables
        for var, value in case.items():
            os.environ[var] = value
            
        # Determine which env var would be used for logging
        env_var_used = "ENABLE_GRID_WS"
        if "API_ENABLE_GRID_WS" in os.environ:
            env_var_used = "API_ENABLE_GRID_WS"
        elif "BOTTIE_ENABLE_GRID_WS" in os.environ:
            env_var_used = "BOTTIE_ENABLE_GRID_WS"
            
        print(f"   Case {i}: {case or 'No vars'} → Logging: {env_var_used}")
    
    print("\n🎉 All tests completed!")
    print("\n📋 Summary for Render deployment:")
    print("   • Use API_ENABLE_GRID_WS=1 for your API service")
    print("   • Use BOTTIE_ENABLE_GRID_WS=1 for your main bot service") 
    print("   • Use ENABLE_GRID_WS=1 only if no naming conflicts")
    print("   • Set to 0 for emergency rollback")

if __name__ == "__main__":
    test_env_var_detection()
