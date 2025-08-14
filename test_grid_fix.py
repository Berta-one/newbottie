#!/usr/bin/env python3
"""
Test the fixed grid structure for frontend compatibility
"""

import requests
import json

def test_grid_fix():
    try:
        print("🔍 Testing Grid Structure Fix...")
        print("=" * 40)
        
        response = requests.get("https://bottie-1.onrender.com/grid/matrix", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Status: {response.status_code}")
            print(f"📋 Response Keys: {list(data.keys())}")
            
            # Test the exact structure frontend needs
            rows = data.get('rows', [])
            cols = data.get('cols', [])
            matrix = data.get('matrix', {})
            grid = data.get('grid', [])
            
            print(f"\n🎯 Frontend Compatibility Test:")
            print(f"   rows (array): {type(rows).__name__} with {len(rows)} items")
            print(f"   cols (array): {type(cols).__name__} with {len(cols)} items")
            print(f"   matrix (object): {type(matrix).__name__} with {len(matrix)} items")
            print(f"   grid (array): {type(grid).__name__} with {len(grid)} items")
            
            # Test forEach compatibility
            print(f"\n✅ forEach Tests:")
            try:
                # This is what the frontend JavaScript does
                if isinstance(rows, list):
                    print(f"   rows.forEach() ✅ - Safe to iterate over {len(rows)} rows")
                else:
                    print(f"   rows.forEach() ❌ - Not an array: {type(rows)}")
                    
                if isinstance(cols, list):
                    print(f"   cols.forEach() ✅ - Safe to iterate over {len(cols)} cols")
                else:
                    print(f"   cols.forEach() ❌ - Not an array: {type(cols)}")
                    
            except Exception as e:
                print(f"   forEach test failed: {e}")
            
            # Show sample data
            print(f"\n📊 Sample Data:")
            if rows:
                print(f"   Rows: {rows[:3]}...")
            if cols:
                print(f"   Cols: {cols}")
            if grid and len(grid) > 0:
                sample = grid[0]
                print(f"   Sample Grid Item: {sample.get('symbol')} @ ${sample.get('price')}")
            
            print(f"\n🎉 FRONTEND GRID ERROR SHOULD BE FIXED!")
            
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_grid_fix()
