#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 ENVIRONMENT VARIABLE CHECK")
print("="*50)
print(f"TRADE_ENABLED: '{os.getenv('TRADE_ENABLED', 'NOT_SET')}'")
print(f"ENVIRONMENT: '{os.getenv('ENVIRONMENT', 'NOT_SET')}'")
print(f"BINANCE_API_KEY: '{os.getenv('BINANCE_API_KEY', 'NOT_SET')[:20]}...'")
print(f"BINANCE_API_SECRET: '{os.getenv('BINANCE_API_SECRET', 'NOT_SET')[:20]}...'")

trade_enabled = os.getenv('TRADE_ENABLED', '0') == '1'
environment_prod = os.getenv('ENVIRONMENT', '') == 'production'
use_live_trading = trade_enabled and environment_prod

print(f"\n🧮 LOGIC CHECK")
print(f"trade_enabled: {trade_enabled}")
print(f"environment_prod: {environment_prod}")
print(f"use_live_trading: {use_live_trading}")
print(f"sandbox mode: {not use_live_trading}")

if use_live_trading:
    print("✅ Should be LIVE TRADING")
else:
    print("❌ Will be TESTNET")
    if not trade_enabled:
        print("   - TRADE_ENABLED is not '1'")
    if not environment_prod:
        print("   - ENVIRONMENT is not 'production'")
