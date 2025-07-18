#!/usr/bin/env python3
"""
Comprehensive Binance API Diagnostic Script
Run this to identify the exact cause of -2015 errors
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

def run_comprehensive_diagnostic():
    print("🔍 COMPREHENSIVE BINANCE API DIAGNOSTIC")
    print("=" * 60)
    
    load_dotenv()
    
    # Environment check
    print("1️⃣ ENVIRONMENT VARIABLES CHECK")
    print("-" * 40)
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    use_testnet = os.getenv('USE_TESTNET', 'True').lower() == 'true'
    
    if not api_key:
        print("❌ BINANCE_API_KEY not found in environment")
        return False
    if not api_secret:
        print("❌ BINANCE_API_SECRET not found in environment")
        return False
    
    print(f"✅ API Key: {api_key[:8]}...{api_key[-8:]} (Length: {len(api_key)})")
    print(f"✅ API Secret: {api_secret[:8]}...{api_secret[-8:]} (Length: {len(api_secret)})")
    print(f"✅ Testnet Mode: {use_testnet}")
    
    # Key format validation
    print("\n2️⃣ API KEY FORMAT VALIDATION")
    print("-" * 40)
    
    if len(api_key) != 64:
        print(f"⚠️ API Key length unusual: {len(api_key)} (expected 64)")
    else:
        print("✅ API Key length correct")
    
    if len(api_secret) != 64:
        print(f"⚠️ API Secret length unusual: {len(api_secret)} (expected 64)")
    else:
        print("✅ API Secret length correct")
    
    # Check for invisible characters
    if api_key != api_key.strip():
        print("⚠️ API Key has leading/trailing whitespace")
        api_key = api_key.strip()
    if api_secret != api_secret.strip():
        print("⚠️ API Secret has leading/trailing whitespace")
        api_secret = api_secret.strip()
    
    try:
        from binance.client import Client
        from binance.exceptions import BinanceAPIException
        
        print("\n3️⃣ BINANCE CLIENT INITIALIZATION")
        print("-" * 40)
        
        # Initialize client
        client = Client(api_key, api_secret)
        
        if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api'
            print("🧪 Using Binance Testnet")
        else:
            print("⚠️ Using LIVE Binance")
        
        print("✅ Client initialized successfully")
        
        # Test connection
        print("\n4️⃣ CONNECTION TEST")
        print("-" * 40)
        
        try:
            server_time = client.get_server_time()
            local_time = int(time.time() * 1000)
            time_diff = abs(server_time['serverTime'] - local_time)
            
            print(f"✅ Server connection successful")
            print(f"📅 Server time: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
            print(f"📅 Local time: {datetime.fromtimestamp(local_time/1000)}")
            print(f"⏰ Time difference: {time_diff}ms")
            
            if time_diff > 5000:
                print("⚠️ Time difference >5s - may cause issues")
        
        except Exception as e:
            print(f"❌ Server connection failed: {e}")
            return False
        
        # Account info test
        print("\n5️⃣ ACCOUNT ACCESS TEST")
        print("-" * 40)
        
        try:
            account = client.get_account()
            print("✅ Account info retrieved successfully")
            
            # Check account status
            account_type = account.get('accountType', 'Unknown')
            can_trade = account.get('canTrade', False)
            can_withdraw = account.get('canWithdraw', False)
            
            print(f"📋 Account Type: {account_type}")
            print(f"💰 Can Trade: {'✅ YES' if can_trade else '❌ NO'}")
            print(f"💸 Can Withdraw: {'✅ YES' if can_withdraw else '❌ NO'}")
            
            if not can_trade:
                print("\n❌ CRITICAL: Trading is disabled on this account!")
                print("🔧 Possible causes:")
                print("   - API permissions not enabled")
                print("   - Account restrictions")
                print("   - Verification issues")
                return False
            
            # Check balances
            balances = {b['asset']: float(b['free']) for b in account['balances'] if float(b['free']) > 0}
            print(f"📊 Assets with balance: {len(balances)}")
            
            if 'USDT' in balances:
                print(f"💵 USDT Balance: ${balances['USDT']:,.2f}")
            else:
                print("⚠️ No USDT balance found")
        
        except BinanceAPIException as e:
            print(f"❌ Account access failed: {e}")
            print(f"🔢 Error code: {e.code}")
            
            if e.code == -2015:
                print("\n🔧 TROUBLESHOOTING -2015 ERROR:")
                print("   1. Check if trading is enabled on your Binance account")
                print("   2. Verify API key has 'Spot & Margin Trading' enabled")
                print("   3. Check if IP restrictions match your current IP")
                print("   4. Ensure account is fully verified")
                print("   5. Try regenerating API keys")
            elif e.code == -2014:
                print("\n🔧 TROUBLESHOOTING -2014 ERROR:")
                print("   1. Check API key format (no spaces, correct length)")
                print("   2. Regenerate API keys if corrupted")
                print("   3. Check .env file encoding")
            
            return False
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        
        # Exchange info test
        print("\n6️⃣ EXCHANGE INFO TEST")
        print("-" * 40)
        
        try:
            exchange_info = client.get_exchange_info()
            symbols = [s['symbol'] for s in exchange_info['symbols'] if s['symbol'].endswith('USDT')]
            print(f"✅ Exchange info retrieved")
            print(f"📈 USDT pairs available: {len(symbols)}")
        except Exception as e:
            print(f"❌ Exchange info failed: {e}")
        
        # Market data test
        print("\n7️⃣ MARKET DATA TEST")
        print("-" * 40)
        
        try:
            ticker = client.get_symbol_ticker(symbol='BTCUSDT')
            klines = client.get_klines(symbol='BTCUSDT', interval='1m', limit=5)
            
            print(f"✅ Market data access working")
            print(f"📈 BTC Price: ${float(ticker['price']):,.2f}")
            print(f"📊 Klines retrieved: {len(klines)}")
        except Exception as e:
            print(f"❌ Market data failed: {e}")
        
        # Test order permissions (testnet only)
        if use_testnet:
            print("\n8️⃣ ORDER PERMISSIONS TEST (TESTNET)")
            print("-" * 40)
            
            try:
                # Test order creation (won't execute)
                result = client.create_test_order(
                    symbol='BTCUSDT',
                    side='BUY',
                    type='MARKET',
                    quoteOrderQty=10
                )
                print("✅ Order permissions working")
                
            except BinanceAPIException as e:
                print(f"❌ Order test failed: {e}")
                print(f"🔢 Error code: {e.code}")
                
                if e.code == -2015:
                    print("\n🔧 ORDER PERMISSION TROUBLESHOOTING:")
                    print("   1. Wait 5 minutes after enabling API permissions")
                    print("   2. Check if account has trading restrictions")
                    print("   3. Verify testnet account has funds")
                    print("   4. Try with different symbol (ETHUSDT)")
                
            except Exception as e:
                print(f"❌ Unexpected order error: {e}")
        
        else:
            print("\n8️⃣ SKIPPING ORDER TEST (LIVE MODE)")
            print("-" * 40)
            print("⚠️ Skipping order test in live mode for safety")
        
        # IP check
        print("\n9️⃣ IP RESTRICTION CHECK")
        print("-" * 40)
        
        try:
            import requests
            ip_response = requests.get('https://ipinfo.io/json', timeout=5)
            current_ip = ip_response.json().get('ip', 'Unknown')
            print(f"🌐 Current IP: {current_ip}")
            print("💡 If using IP restrictions, ensure this IP is whitelisted")
        except:
            print("⚠️ Could not determine current IP")
        
        print("\n🎯 DIAGNOSTIC COMPLETE")
        print("=" * 60)
        
        return True
        
    except ImportError:
        print("❌ Missing python-binance library")
        print("Run: pip install python-binance")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def suggest_solutions():
    print("\n💡 COMMON SOLUTIONS FOR -2015 ERROR:")
    print("=" * 50)
    print("1. 📋 API Permissions:")
    print("   - Go to Binance.com → API Management")
    print("   - Edit restrictions → Enable 'Spot & Margin Trading'")
    print("   - Save and wait 2-5 minutes")
    print()
    print("2. 🌐 IP Restrictions:")
    print("   - Check if IP restrictions are enabled")
    print("   - Add your current IP to whitelist")
    print("   - Or disable IP restrictions temporarily")
    print()
    print("3. 👤 Account Status:")
    print("   - Ensure account is fully verified")
    print("   - Check for any trading restrictions")
    print("   - Contact Binance support if needed")
    print()
    print("4. 🔑 API Key Issues:")
    print("   - Try regenerating API keys")
    print("   - Double-check key format (no spaces)")
    print("   - Ensure keys match the correct environment (testnet/live)")
    print()
    print("5. ⏰ Time Sync:")
    print("   - Ensure system time is accurate")
    print("   - Restart if time difference >5 seconds")

if __name__ == "__main__":
    print("Starting comprehensive Binance API diagnostic...")
    print("This will test all aspects of your API configuration\n")
    
    success = run_comprehensive_diagnostic()
    
    if not success:
        suggest_solutions()
        print("\n🔄 Run this script again after making changes")
    else:
        print("🎉 All tests passed! Your API should be working correctly.")
        print("💡 If you're still getting -2015 errors, the issue might be:")
        print("   - Timing/delay after permission changes")
        print("   - Specific to your bot code")
        print("   - Account-level restrictions")