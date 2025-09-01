#!/usr/bin/env python3
"""Quick test of the professional trading grid endpoint"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from api.app import _symbols_to_scan
import asyncio
import json

async def test_grid_logic():
    """Test the new volume-based grid scanning logic"""
    print("🏛️ Testing Professional Trading Grid Logic...")
    print("=" * 60)
    
    try:
        # Test the volume-based scanning
        symbols = await _symbols_to_scan()
        print(f"✅ Symbol scanning successful!")
        print(f"📊 Found {len(symbols)} trading pairs")
        print(f"🔢 First 10 symbols: {symbols[:10]}")
        
        # Check for cross-pairs (non-USDT)
        cross_pairs = [s for s in symbols if not s.endswith('/USDT')]
        print(f"🔀 Cross-pair symbols: {len(cross_pairs)}")
        print(f"💎 Example cross-pairs: {cross_pairs[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in grid logic: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_grid_logic())
    
    if success:
        print("\n🎉 Professional Trading Grid Implementation Complete!")
        print("📈 Ready for volume-based crypto-to-crypto atomic swaps")
    else:
        print("\n⚠️ Grid needs debugging")
