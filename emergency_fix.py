#!/usr/bin/env python3
"""
EMERGENCY FIX for Railway -2015 API Errors
===========================================
This fixes the hardcoded testnet URLs that are causing your trading failures
"""

import os
import re
import glob

def emergency_fix_all_files():
    """Emergency fix for all Python files with hardcoded testnet URLs"""
    print("🚨 EMERGENCY API FIX STARTING...")
    print("=" * 50)
    
    # Find all Python files
    python_files = glob.glob("*.py")
    
    fixes_applied = 0
    
    for filename in python_files:
        if filename == __file__.split('/')[-1]:  # Skip this script
            continue
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            continue
        
        original_content = content
        
        # Fix 1: Remove ALL hardcoded testnet URLs
        patterns_to_fix = [
            (r'client\.API_URL\s*=\s*["\']https://testnet\.binance\.vision/api["\']', 
             '# EMERGENCY FIX: Removed hardcoded testnet URL'),
            (r'self\.client\.API_URL\s*=\s*["\']https://testnet\.binance\.vision/api["\']',
             '# EMERGENCY FIX: Removed hardcoded testnet URL'),
            (r'self\._client\.API_URL\s*=\s*["\']https://testnet\.binance\.vision/api["\']',
             '# EMERGENCY FIX: Removed hardcoded testnet URL'),
        ]
        
        for pattern, replacement in patterns_to_fix:
            content = re.sub(pattern, replacement, content)
        
        # Fix 2: Add proper testnet logic after Client initialization
        client_patterns = [
            'client = Client(',
            'self.client = Client(',
            'self._client = Client('
        ]
        
        for pattern in client_patterns:
            if pattern in content and 'use_testnet = os.getenv("USE_TESTNET"' not in content:
                # Add USE_TESTNET check
                testnet_logic = f'''
        # EMERGENCY FIX: Proper testnet handling
        use_testnet = os.getenv("USE_TESTNET", "false").lower() == "true"
        {pattern}'''
                
                content = content.replace(pattern, testnet_logic)
                
                # Add URL setting after client creation
                if 'client.get_server_time()' in content:
                    content = content.replace(
                        'client.get_server_time()',
                        '''if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api'
            print(f"🧪 {filename}: Using TESTNET")
        else:
            print(f"🚀 {filename}: Using LIVE")
        client.get_server_time()'''
                    )
                elif 'self.client.get_server_time()' in content:
                    content = content.replace(
                        'self.client.get_server_time()',
                        '''if use_testnet:
            self.client.API_URL = 'https://testnet.binance.vision/api'
            print(f"🧪 {filename}: Using TESTNET")
        else:
            print(f"🚀 {filename}: Using LIVE")
        self.client.get_server_time()'''
                    )
                elif 'self._client.get_server_time()' in content:
                    content = content.replace(
                        'self._client.get_server_time()',
                        '''if use_testnet:
            self._client.API_URL = 'https://testnet.binance.vision/api'
            print(f"🧪 {filename}: Using TESTNET")
        else:
            print(f"🚀 {filename}: Using LIVE")
        self._client.get_server_time()'''
                    )
        
        # Write back if changes were made
        if content != original_content:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ FIXED: {filename}")
                fixes_applied += 1
            except Exception as e:
                print(f"❌ Failed to fix {filename}: {e}")
    
    return fixes_applied

def verify_environment():
    """Verify Railway environment variables"""
    print("\n🔍 RAILWAY ENVIRONMENT CHECK")
    print("-" * 40)
    
    required_vars = {
        'BINANCE_API_KEY': os.getenv('BINANCE_API_KEY'),
        'BINANCE_API_SECRET': os.getenv('BINANCE_API_SECRET'),
        'USE_TESTNET': os.getenv('USE_TESTNET', 'MISSING')
    }
    
    all_good = True
    
    for var, value in required_vars.items():
        if value and value != 'MISSING':
            if 'KEY' in var or 'SECRET' in var:
                print(f"✅ {var}: {value[:8]}...{value[-8:]} ({len(value)} chars)")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: MISSING")
            all_good = False
    
    # Critical check for USE_TESTNET
    use_testnet = os.getenv('USE_TESTNET', 'true').lower() == 'true'
    if use_testnet:
        print(f"⚠️  WARNING: USE_TESTNET=true but you want live trading!")
        print(f"   Set USE_TESTNET=false in Railway environment variables")
        return False
    else:
        print(f"✅ USE_TESTNET=false - Live trading mode enabled")
    
    return all_good

def test_quick_connection():
    """Quick API connection test"""
    print("\n🔌 QUICK CONNECTION TEST")
    print("-" * 40)
    
    try:
        from binance.client import Client
        
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
        
        if not api_key or not api_secret:
            print("❌ API credentials missing")
            return False
        
        print(f"🔑 Using API Key: {api_key[:8]}...{api_key[-8:]}")
        print(f"🌐 Testnet mode: {use_testnet}")
        
        client = Client(api_key, api_secret)
        
        # CRITICAL: Only set testnet URL if USE_TESTNET=true
        if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api'
            print("🧪 Testing with TESTNET URL")
        else:
            print("🚀 Testing with LIVE URL")
        
        # Test connection
        account = client.get_account()
        print(f"✅ Connection successful!")
        print(f"📊 Account type: {account.get('accountType', 'Unknown')}")
        
        # Count balances
        balances = [b for b in account['balances'] if float(b['free']) > 0]
        print(f"💰 Assets with balance: {len(balances)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Main emergency fix"""
    print("🚨 RAILWAY EMERGENCY FIX")
    print("=" * 60)
    print("Fixing hardcoded testnet URLs causing -2015 errors...")
    
    # Step 1: Fix all files
    fixes = emergency_fix_all_files()
    
    # Step 2: Check environment
    env_ok = verify_environment()
    
    # Step 3: Test connection
    connection_ok = test_quick_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 EMERGENCY FIX SUMMARY")
    print("=" * 60)
    print(f"📝 Files fixed: {fixes}")
    print(f"🌐 Environment OK: {'✅' if env_ok else '❌'}")
    print(f"🔌 Connection OK: {'✅' if connection_ok else '❌'}")
    
    if env_ok and connection_ok:
        print("\n✅ SUCCESS! Your bots should now work correctly!")
        print("🚀 -2015 errors should be resolved")
        print("\n📋 If still having issues:")
        print("1. Check Railway logs for any remaining errors")
        print("2. Verify USE_TESTNET=false in Railway variables")
        print("3. Ensure API keys have trading permissions")
    else:
        print("\n❌ ISSUES STILL EXIST:")
        if not env_ok:
            print("   - Fix Railway environment variables")
        if not connection_ok:
            print("   - Check API key permissions")
    
    return env_ok and connection_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
