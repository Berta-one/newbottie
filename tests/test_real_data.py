#!/usr/bin/env python3
"""
Test script to verify real data endpoints
"""

import sys
import os
import asyncio

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment 
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment")

# Test the functions directly
from api.app import initialize_real_exchange, get_real_balance, get_real_positions

def test_real_data():
    print("🧪 Testing Real Trading Data")
    print("="*50)
    
    # Initialize exchange
    print("\n1. Initializing exchange connection...")
    if initialize_real_exchange():
        print("✅ Exchange connected successfully")
    else:
        print("❌ Exchange connection failed")
        return
    
    # Test balance
    print("\n2. Testing real balance...")
    try:
        balance = get_real_balance()
        print(f"✅ Real Balance: {balance}")
        print(f"   Total USDT Value: ${balance.get('total_usdt', 'ERROR'):.2f}")
    except Exception as e:
        print(f"❌ Balance error: {e}")
    
    # Test positions
    print("\n3. Testing real positions...")
    try:
        positions = get_real_positions()
        print(f"✅ Real Positions: {len(positions)} found")
        for symbol, pos in positions.items():
            if pos.get('balance', 0) > 0:
                print(f"   {symbol}: {pos.get('balance', 0)} = ${pos.get('market_value', 0):.2f}")
    except Exception as e:
        print(f"❌ Positions error: {e}")

if __name__ == "__main__":
    test_real_data()
