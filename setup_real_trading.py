#!/usr/bin/env python3
"""
Real Trading Setup Script for Bottie
Configures live trading with your actual Binance account
"""

import os
import sys
import json
import time
import ccxt
from typing import Dict, Any

def print_banner():
    print("\n" + "="*60)
    print("🚀 BOTTIE REAL TRADING SETUP")
    print("="*60)
    print("⚠️  WARNING: This configures LIVE trading with real money!")
    print("🔒 Ensure you understand the risks before proceeding")
    print("="*60 + "\n")

def check_prerequisites():
    """Check if all required packages are installed"""
    try:
        import ccxt
        import pandas as pd
        import numpy as np
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Run: pip install ccxt pandas numpy")
        return False

def setup_binance_connection():
    """Set up and test Binance connection"""
    print("\n🔑 BINANCE API SETUP")
    print("You need to create API keys from your Binance account:")
    print("1. Go to https://www.binance.com/en/my/settings/api-management")
    print("2. Create a new API key")
    print("3. Enable 'Spot & Margin Trading' (for trading)")
    print("4. Enable 'Futures Trading' (if you want futures)")
    print("5. Restrict to specific IPs for security")
    
    api_key = input("\nEnter your Binance API Key: ").strip()
    secret = input("Enter your Binance Secret: ").strip()
    
    if not api_key or not secret:
        print("❌ API key and secret are required")
        return None, None
    
    # Test connection
    try:
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'sandbox': True,  # Start with testnet
            'enableRateLimit': True,
        })
        
        exchange.load_markets()
        account = exchange.fetch_balance()
        
        print("✅ Connection successful!")
        print(f"📊 Account type: {account.get('info', {}).get('accountType', 'Unknown')}")
        
        return api_key, secret
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None, None

def check_account_balance(api_key, secret):
    """Check account balance and positions"""
    try:
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret,
            'sandbox': False,  # Check real account
            'enableRateLimit': True,
        })
        
        balance = exchange.fetch_balance()
        total_usdt = 0
        
        print("\n💰 ACCOUNT BALANCE:")
        for currency, amount in balance['total'].items():
            if amount > 0:
                try:
                    # Convert to USDT value
                    if currency == 'USDT':
                        usdt_value = amount
                    else:
                        ticker = exchange.fetch_ticker(f"{currency}/USDT")
                        usdt_value = amount * ticker['last']
                    
                    total_usdt += usdt_value
                    print(f"  {currency}: {amount:.6f} (≈ ${usdt_value:.2f})")
                    
                except:
                    print(f"  {currency}: {amount:.6f}")
        
        print(f"\n💵 Total Portfolio Value: ≈ ${total_usdt:.2f}")
        
        # Check open positions
        open_orders = exchange.fetch_open_orders()
        if open_orders:
            print(f"\n📈 Open Orders: {len(open_orders)}")
            for order in open_orders[:5]:  # Show first 5
                print(f"  {order['symbol']}: {order['side']} {order['amount']} @ {order['price']}")
        else:
            print("\n📈 No open orders")
            
        return total_usdt
        
    except Exception as e:
        print(f"❌ Could not fetch account data: {e}")
        return 0

def create_env_file(api_key, secret, live_trading=False):
    """Create environment configuration file"""
    env_content = f"""# BOTTIE REAL TRADING CONFIGURATION
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

# Exchange API Keys
BINANCE_API_KEY={api_key}
BINANCE_SECRET={secret}

# Trading Mode
LIVE_TRADING_ENABLED={'true' if live_trading else 'false'}
USE_TESTNET={'false' if live_trading else 'true'}

# Portfolio Configuration
RISK_PER_TRADE=0.01        # 1% risk per trade (conservative)
MAX_POSITIONS=3            # Maximum 3 concurrent positions
STOP_LOSS_PERCENT=0.03     # 3% stop loss
TAKE_PROFIT_PERCENT=0.06   # 6% take profit

# Safety Features
MAX_DAILY_LOSS=0.05        # 5% maximum daily loss
ENABLE_AUTO_TRADING=false  # Manual trading only initially
REQUIRE_CONFIRMATION=true  # Require confirmation for trades

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security
ADMIN_PASSWORD=Diego1234!
JWT_SECRET=real_trading_jwt_secret_{int(time.time())}

# Logging
LOG_LEVEL=INFO
LOG_TRADES=true
"""
    
    with open('.env.real', 'w') as f:
        f.write(env_content)
    
    print(f"✅ Configuration saved to .env.real")

def display_setup_summary(total_value, live_mode=False):
    """Display setup summary"""
    mode = "LIVE TRADING" if live_mode else "TESTNET"
    print(f"\n" + "="*60)
    print("🎯 SETUP COMPLETE")
    print("="*60)
    print(f"Mode: {mode}")
    print(f"Portfolio Value: ≈ ${total_value:.2f}")
    print(f"Risk Management: Conservative (1% per trade)")
    print(f"Auto Trading: Disabled (manual only)")
    print("\n📋 NEXT STEPS:")
    if not live_mode:
        print("1. Test with testnet mode first")
        print("2. Run: python api_real_trading.py")
        print("3. Verify dashboard shows real data")
        print("4. When ready, set LIVE_TRADING_ENABLED=true")
    else:
        print("1. Run: python api_real_trading.py")
        print("2. Monitor your dashboard carefully")
        print("3. Start with small test trades")
    print("\n⚠️  IMPORTANT:")
    print("- Always monitor your positions")
    print("- Never risk more than you can afford to lose")
    print("- Start with small amounts for testing")
    print("="*60 + "\n")

def main():
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Setup API keys
    api_key, secret = setup_binance_connection()
    if not api_key:
        return
    
    # Check real account (optional)
    print("\n🔍 Checking your real account...")
    total_value = check_account_balance(api_key, secret)
    
    # Ask about live trading mode
    print("\n⚠️  TRADING MODE SELECTION:")
    print("1. TESTNET mode (recommended for testing)")
    print("2. LIVE trading mode (real money)")
    
    mode_choice = input("\nChoose mode (1 or 2): ").strip()
    live_trading = mode_choice == "2"
    
    if live_trading:
        confirm = input("\n⚠️  CONFIRM: You want to enable LIVE trading with real money? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Switching to testnet mode for safety")
            live_trading = False
    
    # Create configuration
    create_env_file(api_key, secret, live_trading)
    
    # Show summary
    display_setup_summary(total_value, live_trading)
    
    print("🚀 Ready to start real trading with Bottie!")

if __name__ == "__main__":
    main()
