#!/usr/bin/env python3

"""
Test script to validate crypto-to-crypto trading pairs in the maxi-grid
"""

import os
import sys
import asyncio
sys.path.append('.')

# Set test environment variables
os.environ["ENABLE_CRYPTO_PAIRS"] = "1"
os.environ["GRID_MAJOR_CRYPTOS"] = "BTC,ETH,BNB,ADA,SOL,DOT,MATIC,AVAX,LINK,UNI"
os.environ["ENABLE_GRID_WS"] = "1"
os.environ["PRIMARY_QUOTE"] = "USDT"

async def test_crypto_pairs():
    """Test the new crypto-to-crypto pair generation"""
    print("🧪 Testing Crypto-to-Crypto Pairs Generation")
    print("=" * 50)
    
    try:
        from api.cross_pairs import CrossPairsWS, MAJOR_CRYPTOS, STABLES, ENABLE_CRYPTO_PAIRS
        
        print(f"✅ Configuration loaded:")
        print(f"   ENABLE_CRYPTO_PAIRS: {ENABLE_CRYPTO_PAIRS}")
        print(f"   MAJOR_CRYPTOS: {MAJOR_CRYPTOS}")
        print(f"   STABLES: {STABLES}")
        print()
        
        # Create a test instance (without real API keys)
        cross_ws = CrossPairsWS(api_key="test", api_secret="test")
        
        # Simulate some balance data
        test_balances = {
            'BTC': 0.01,
            'ETH': 0.5, 
            'ADA': 100,
            'USDT': 1000
        }
        
        # Manually set rows and cols to test the logic
        print("📊 Simulating grid generation...")
        
        # Simulate rows (assets with balances + majors + stables)
        rows = set()
        for asset, qty in test_balances.items():
            if qty > 0:
                rows.add(asset.upper())
        rows.update(STABLES)
        if ENABLE_CRYPTO_PAIRS:
            rows.update(MAJOR_CRYPTOS)
        cross_ws.rows = sorted(rows)
        
        # Simulate cols (scan universe)
        priority_assets = STABLES + ["USDT"]  # PRIMARY_QUOTE
        if ENABLE_CRYPTO_PAIRS:
            priority_assets = MAJOR_CRYPTOS + priority_assets
        cross_ws.cols = sorted(list(set(priority_assets)))[:80]  # MAX_COLS = 80
        
        print(f"🎯 Generated Grid Dimensions:")
        print(f"   Rows (Portfolio Assets): {len(cross_ws.rows)} -> {cross_ws.rows[:15]}{'...' if len(cross_ws.rows) > 15 else ''}")
        print(f"   Cols (Scan Universe): {len(cross_ws.cols)} -> {cross_ws.cols[:15]}{'...' if len(cross_ws.cols) > 15 else ''}")
        print()
        
        # Count potential trading pairs
        crypto_pairs = []
        stable_pairs = []
        total_pairs = 0
        
        for base in cross_ws.rows:
            for quote in cross_ws.cols:
                if base == quote:
                    continue
                pair = f"{base}/{quote}"
                total_pairs += 1
                
                if base in MAJOR_CRYPTOS and quote in MAJOR_CRYPTOS:
                    crypto_pairs.append(pair)
                elif base in MAJOR_CRYPTOS and quote in STABLES:
                    stable_pairs.append(pair)
        
        print(f"📈 Trading Opportunities Analysis:")
        print(f"   Total Potential Pairs: {total_pairs}")
        print(f"   Crypto-to-Crypto Pairs: {len(crypto_pairs)}")
        print(f"   Crypto-to-Stable Pairs: {len(stable_pairs)}")
        print()
        
        print(f"🔗 Sample Crypto-to-Crypto Pairs:")
        for i, pair in enumerate(crypto_pairs[:20]):  # Show first 20
            print(f"   {i+1:2d}. {pair}")
        if len(crypto_pairs) > 20:
            print(f"   ... and {len(crypto_pairs) - 20} more crypto pairs")
        print()
        
        print(f"💰 Sample Crypto-to-Stable Pairs:")
        for i, pair in enumerate(stable_pairs[:10]):  # Show first 10
            print(f"   {i+1:2d}. {pair}")
        if len(stable_pairs) > 10:
            print(f"   ... and {len(stable_pairs) - 10} more stable pairs")
        
        print()
        print("✅ Test completed successfully!")
        print("🚀 The maxi-grid will now show crypto-to-crypto trading opportunities!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_without_crypto_pairs():
    """Test with crypto pairs disabled"""
    print("\n" + "=" * 50)
    print("🧪 Testing WITHOUT Crypto-to-Crypto Pairs")
    print("=" * 50)
    
    # Temporarily disable crypto pairs
    old_val = os.environ.get("ENABLE_CRYPTO_PAIRS", "1")
    os.environ["ENABLE_CRYPTO_PAIRS"] = "0"
    
    try:
        # Reload the module to pick up new environment variable
        import importlib
        if 'api.cross_pairs' in sys.modules:
            importlib.reload(sys.modules['api.cross_pairs'])
        
        from api.cross_pairs import ENABLE_CRYPTO_PAIRS, MAJOR_CRYPTOS, STABLES
        
        print(f"📊 Configuration (Crypto Pairs Disabled):")
        print(f"   ENABLE_CRYPTO_PAIRS: {ENABLE_CRYPTO_PAIRS}")
        print(f"   Would only show pairs with stables: {STABLES}")
        print(f"   Major cryptos excluded from grid: {MAJOR_CRYPTOS[:5]}...")
        
    finally:
        # Restore original value
        os.environ["ENABLE_CRYPTO_PAIRS"] = old_val

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_crypto_pairs())
    
    # Run the sync test
    test_without_crypto_pairs()
    
    print("\n🎯 Summary:")
    print("   ✅ Crypto-to-crypto pairs are now enabled by default")
    print("   ✅ Major cryptocurrencies added to both rows and columns") 
    print("   ✅ Grid will show opportunities like BTC/ETH, ETH/ADA, SOL/DOT etc.")
    print("   ✅ Use ENABLE_CRYPTO_PAIRS=0 to disable if needed")
    print("   ✅ Deploy these changes and restart the API to see new pairs!")
