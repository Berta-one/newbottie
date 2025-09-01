#!/usr/bin/env python3
"""
Critical Dashboard Fix Script
Addresses the most important issues:
1. WebSocket OHLCV failures 
2. Missing Brier score display
3. Cross-pair Maxi-grid not working
4. ML Performance Over Time empty
"""

import requests
import json

def test_current_api_responses():
    """Check what data our APIs are actually returning"""
    base_url = "http://localhost:8000"
    
    print("🔍 CHECKING CURRENT API RESPONSES")
    print("=" * 60)
    
    # Check ML status structure
    try:
        response = requests.get(f"{base_url}/ml/status")
        if response.status_code == 200:
            data = response.json()
            print("\n📊 ML STATUS STRUCTURE:")
            print("Keys available:", list(data.keys()))
            print("Brier score:", data.get("brier_score"))
            print("Interpretation:", data.get("interpretation", {}).get("description"))
            print("Sample count:", data.get("sample_count"))
            print("Feature importance:", data.get("feature_importance", {}))
        else:
            print(f"❌ ML Status failed: {response.status_code}")
    except Exception as e:
        print(f"❌ ML Status error: {e}")
    
    # Check ML performance
    try:
        response = requests.get(f"{base_url}/ml/performance?timeframe=1h")
        if response.status_code == 200:
            data = response.json()
            print("\n📈 ML PERFORMANCE STRUCTURE:")
            print("Current timeframe keys:", list(data.get("current_timeframe", {}).keys()))
            accuracy_data = data.get("current_timeframe", {}).get("accuracy", [])
            print(f"Accuracy data points: {len(accuracy_data)}")
            if accuracy_data:
                print("Sample accuracy point:", accuracy_data[0])
        else:
            print(f"❌ ML Performance failed: {response.status_code}")
    except Exception as e:
        print(f"❌ ML Performance error: {e}")
    
    # Check signals for cross-pair trading
    try:
        response = requests.get(f"{base_url}/signals")
        if response.status_code == 200:
            data = response.json()
            signals = data.get("signals", [])
            print(f"\n🔄 TRADING SIGNALS ({len(signals)} total):")
            symbols = [s.get("symbol") for s in signals]
            print("Active symbols:", symbols)
            
            # Check for cross-pairs (non-USDT)
            cross_pairs = [s for s in symbols if not s.endswith("/USDT")]
            usdt_pairs = [s for s in symbols if s.endswith("/USDT")]
            print(f"USDT pairs: {len(usdt_pairs)} - {usdt_pairs}")
            print(f"Cross pairs: {len(cross_pairs)} - {cross_pairs}")
            
            if len(cross_pairs) == 0:
                print("⚠️  NO CROSS-PAIRS FOUND - This is the main issue!")
        else:
            print(f"❌ Signals failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Signals error: {e}")
    
    # Check cross-pair grid endpoint
    try:
        response = requests.get(f"{base_url}/grid/matrix")
        if response.status_code == 200:
            data = response.json()
            print(f"\n🔲 GRID MATRIX:")
            print("Matrix keys:", list(data.keys()))
            rows = data.get("rows", [])
            cols = data.get("cols", [])
            matrix = data.get("matrix", {})
            print(f"Grid dimensions: {len(rows)} rows x {len(cols)} cols")
            print("Rows (bases):", rows)
            print("Cols (quotes):", cols)
            print(f"Matrix entries: {len(matrix)}")
        else:
            print(f"❌ Grid Matrix failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Grid Matrix error: {e}")

if __name__ == "__main__":
    test_current_api_responses()
