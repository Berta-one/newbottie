#!/usr/bin/env python3
"""
Live Trade Execution Diagnostic Script
Run this to identify exactly where trade execution fails
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

def live_trade_diagnostic():
    print("🚀 LIVE TRADE EXECUTION DIAGNOSTIC")
    print("=" * 60)
    
    load_dotenv()
    
    # Step 1: Environment Check
    print("1️⃣ ENVIRONMENT VALIDATION")
    print("-" * 40)
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    use_testnet = os.getenv('USE_TESTNET', 'False').lower() == 'true'
    
    if not api_key or not api_secret:
        print("❌ CRITICAL: Missing API credentials")
        return False
    
    print(f"✅ API Key: {api_key[:8]}...{api_key[-8:]}")
    print(f"✅ API Secret: {api_secret[:8]}...{api_secret[-8:]}")
    print(f"✅ Testnet Mode: {use_testnet}")
    
    # Step 2: Import and Initialize
    print("\n2️⃣ BINANCE CLIENT INITIALIZATION")
    print("-" * 40)
    
    try:
        from binance.client import Client
        from binance.exceptions import BinanceAPIException
        
        client = Client(api_key, api_secret)
        
        if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api'
            print("🧪 Using Binance Testnet")
        else:
            print("⚠️ Using LIVE Binance")
        
        print("✅ Client initialized successfully")
        
    except ImportError:
        print("❌ CRITICAL: Binance library not installed")
        print("Run: pip install python-binance")
        return False
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False
    
    # Step 3: Connection Test
    print("\n3️⃣ API CONNECTION TEST")
    print("-" * 40)
    
    try:
        account = client.get_account()
        print("✅ API connection successful")
        print(f"📋 Account Type: {account.get('accountType', 'Unknown')}")
        print(f"💰 Can Trade: {account.get('canTrade', False)}")
        
        if not account.get('canTrade'):
            print("❌ CRITICAL: Trading permissions disabled")
            return False
        
    except BinanceAPIException as e:
        print(f"❌ API connection failed: {e}")
        print(f"🔢 Error code: {e.code}")
        
        if e.code == -2015:
            print("🔧 SOLUTION: Enable 'Spot & Margin Trading' in API settings")
        
        return False
    except Exception as e:
        print(f"❌ Unexpected connection error: {e}")
        return False
    
    # Step 4: Account Balance Check
    print("\n4️⃣ ACCOUNT BALANCE VERIFICATION")
    print("-" * 40)
    
    try:
        balances = {b['asset']: float(b['free']) for b in account['balances'] if float(b['free']) > 0}
        
        usdt_balance = balances.get('USDT', 0)
        btc_balance = balances.get('BTC', 0)
        
        print(f"💵 USDT Balance: ${usdt_balance:,.2f}")
        print(f"₿ BTC Balance: {btc_balance:.8f}")
        print(f"📊 Total Assets: {len(balances)}")
        
        if usdt_balance < 10:
            print("⚠️ WARNING: Low USDT balance for trading")
            if usdt_balance == 0:
                print("❌ CRITICAL: No USDT available for trading")
                return False
        
    except Exception as e:
        print(f"❌ Balance check failed: {e}")
        return False
    
    # Step 5: Market Data Test
    print("\n5️⃣ MARKET DATA ACCESS TEST")
    print("-" * 40)
    
    symbol = 'BTCUSDT'
    
    try:
        # Get current price
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        
        # Get recent klines
        klines = client.get_klines(symbol=symbol, interval='1m', limit=5)
        
        print(f"✅ Market data access working")
        print(f"📈 {symbol} Price: ${current_price:,.2f}")
        print(f"📊 Klines retrieved: {len(klines)}")
        
    except Exception as e:
        print(f"❌ Market data access failed: {e}")
        return False
    
    # Step 6: Symbol Information Check
    print("\n6️⃣ SYMBOL TRADING RULES")
    print("-" * 40)
    
    try:
        exchange_info = client.get_exchange_info()
        symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
        
        if not symbol_info:
            print(f"❌ Symbol {symbol} not found")
            return False
        
        print(f"✅ Symbol {symbol} found")
        print(f"📊 Status: {symbol_info['status']}")
        
        # Check trading rules
        for filter_info in symbol_info['filters']:
            if filter_info['filterType'] == 'LOT_SIZE':
                min_qty = float(filter_info['minQty'])
                step_size = float(filter_info['stepSize'])
                print(f"📏 Min Quantity: {min_qty}")
                print(f"📏 Step Size: {step_size}")
                
            elif filter_info['filterType'] == 'MIN_NOTIONAL':
                min_notional = float(filter_info['minNotional'])
                print(f"💰 Min Notional: ${min_notional}")
        
    except Exception as e:
        print(f"❌ Symbol info check failed: {e}")
        return False
    
    # Step 7: TEST ORDER PLACEMENT
    print("\n7️⃣ TEST ORDER PLACEMENT")
    print("-" * 40)
    
    try:
        # Calculate small test quantity
        test_amount_usd = 10.0  # $10 test order
        test_quantity = test_amount_usd / current_price
        test_quantity = round(test_quantity, 8)  # Round to 8 decimal places
        
        print(f"🧪 Test Order Details:")
        print(f"   Symbol: {symbol}")
        print(f"   Side: BUY")
        print(f"   Type: MARKET")
        print(f"   Quantity: {test_quantity:.8f}")
        print(f"   Estimated Cost: ${test_amount_usd:.2f}")
        
        # Use test order first (safe)
        print("\n🧪 Attempting TEST ORDER (no real trade)...")
        
        test_order_result = client.create_test_order(
            symbol=symbol,
            side='BUY',
            type='MARKET',
            quantity=test_quantity
        )
        
        print("✅ TEST ORDER SUCCESSFUL!")
        print("✅ All trading prerequisites met")
        
        # Ask if user wants to place real order
        print("\n" + "=" * 60)
        print("🚀 READY FOR LIVE TRADING!")
        print("All systems check passed. Your setup can execute live trades.")
        print("\n⚠️ IMPORTANT: Test orders don't execute real trades")
        print("To place a REAL trade, we need to use client.order_market() instead")
        
        return True
        
    except BinanceAPIException as e:
        print(f"❌ TEST ORDER FAILED: {e}")
        print(f"🔢 Error code: {e.code}")
        
        # Diagnose specific error codes
        if e.code == -1013:
            print("🔧 SOLUTION: Order quantity too small or violates filters")
            print(f"   Try increasing quantity above {min_qty}")
        elif e.code == -2010:
            print("🔧 SOLUTION: Insufficient balance")
            print(f"   Need at least ${min_notional} USDT")
        elif e.code == -1121:
            print("🔧 SOLUTION: Invalid symbol")
        elif e.code == -2015:
            print("🔧 SOLUTION: API permissions issue")
        else:
            print(f"🔧 Research error code {e.code} in Binance API docs")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected test order error: {e}")
        return False

def execute_live_trade_attempt():
    """Attempt to execute an actual live trade for diagnostic purposes"""
    print("\n" + "=" * 60)
    print("⚠️ LIVE TRADE EXECUTION ATTEMPT")
    print("=" * 60)
    
    response = input("\n🚨 WARNING: This will attempt a REAL trade with REAL money!\nType 'YES' to proceed: ")
    
    if response.upper() != 'YES':
        print("✅ Live trade attempt cancelled - staying safe!")
        return
    
    load_dotenv()
    
    try:
        from binance.client import Client
        from binance.exceptions import BinanceAPIException
        
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        use_testnet = os.getenv('USE_TESTNET', 'False').lower() == 'true'
        
        client = Client(api_key, api_secret)
        
        if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api'
            print("🧪 Using testnet for safety")
        else:
            print("🚨 LIVE TRADING MODE - REAL MONEY!")
        
        # Small live order attempt
        symbol = 'BTCUSDT'
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        
        # Very small order - $10
        trade_amount = 10.0
        quantity = trade_amount / current_price
        quantity = round(quantity, 8)
        
        print(f"\n🎯 Live Order Attempt:")
        print(f"   Symbol: {symbol}")
        print(f"   Quantity: {quantity:.8f}")
        print(f"   Estimated Cost: ${trade_amount:.2f}")
        
        # Execute REAL order
        order = client.order_market_buy(
            symbol=symbol,
            quantity=quantity
        )
        
        print("🎉 LIVE TRADE SUCCESSFUL!")
        print(f"✅ Order ID: {order['orderId']}")
        print(f"✅ Status: {order['status']}")
        print(f"✅ Executed Quantity: {order.get('executedQty', 'N/A')}")
        
        return True
        
    except BinanceAPIException as e:
        print(f"❌ LIVE TRADE FAILED: {e}")
        print(f"🔢 Error code: {e.code}")
        print(f"📄 Message: {e.message}")
        
        # This is the EXACT error your bot is hitting
        print("\n🎯 THIS IS THE ERROR YOUR BOT ENCOUNTERS!")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected live trade error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Starting comprehensive live trade diagnostic...")
    print("This will identify exactly why your trades fail\n")
    
    # Run diagnostic
    diagnostic_passed = live_trade_diagnostic()
    
    if diagnostic_passed:
        print("\n🎉 DIAGNOSTIC COMPLETE - ALL SYSTEMS READY!")
        print("\nYour bot CAN execute trades. If it's failing, the issue is likely:")
        print("1. 🎯 Order size too small/large")
        print("2. 💰 Insufficient balance at trade time")
        print("3. 📊 Symbol trading rules violation")
        print("4. ⏰ Market hours or symbol status")
        print("5. 🔧 Code-level execution errors")
        
        # Offer live trade test
        print("\n" + "=" * 60)
        execute_live_trade_attempt()
        
    else:
        print("\n🛑 DIAGNOSTIC FAILED")
        print("Fix the issues above before attempting live trades")