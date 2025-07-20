#!/usr/bin/env python3
"""
Quick Railway Fix - Add this file to your GitHub repo
Run this before starting your bot to fix API issues
"""

import os
import re

def fix_portfolio_manager():
    """Fix portfolio_manager.py hardcoded testnet"""
    filename = 'portfolio_manager.py'
    if not os.path.exists(filename):
        return
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Remove hardcoded testnet URL
    content = re.sub(
        r'self\._client\.API_URL = "https://testnet\.binance\.vision/api"',
        '# Fixed: Removed hardcoded testnet URL',
        content
    )
    
    # Add proper USE_TESTNET check
    if 'USE_TESTNET' not in content:
        # Add testnet logic after client creation
        testnet_fix = '''
        # Check if we should use testnet
        use_testnet = os.getenv("USE_TESTNET", "false").lower() == "true"
        if use_testnet:
            self._client.API_URL = "https://testnet.binance.vision/api"
            print("🧪 Portfolio Manager using TESTNET")
        else:
            print("🚀 Portfolio Manager using LIVE")'''
        
        content = content.replace(
            'self._client.get_server_time()',
            testnet_fix + '\n                self._client.get_server_time()'
        )
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {filename}")

def fix_hybrid_bot():
    """Fix hybrid_bot.py client setup"""
    filename = 'hybrid_bot.py'
    if not os.path.exists(filename):
        return
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Fix client setup function
    old_setup = '''if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api\''''
    
    new_setup = '''if use_testnet:
            client.API_URL = 'https://testnet.binance.vision/api'
            print("🧪 Dashboard using TESTNET")
        else:
            print("🚀 Dashboard using LIVE")'''
    
    content = content.replace(old_setup, new_setup)
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {filename}")

def fix_other_files():
    """Fix other files with hardcoded testnet"""
    files = ['bot_controller.py', 'app.py', 'adaptive_risk_system.py']
    
    for filename in files:
        if not os.path.exists(filename):
            continue
        
        with open(filename, 'r') as f:
            content = f.read()
        
        original = content
        
        # Remove hardcoded testnet
        content = re.sub(
            r'client\.API_URL = "https://testnet\.binance\.vision/api"',
            '# Fixed: Removed hardcoded testnet',
            content
        )
        
        content = re.sub(
            r'self\.client\.API_URL = "https://testnet\.binance\.vision/api"',
            '# Fixed: Removed hardcoded testnet',
            content
        )
        
        if content != original:
            with open(filename, 'w') as f:
                f.write(content)
            print(f"✅ Fixed {filename}")

def main():
    """Apply all fixes"""
    print("🔧 APPLYING RAILWAY FIXES...")
    print("=" * 40)
    
    # Show current environment
    use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
    api_key = os.getenv('BINANCE_API_KEY', 'MISSING')
    
    print(f"📊 Environment Check:")
    print(f"   USE_TESTNET: {use_testnet}")
    print(f"   API_KEY: {api_key[:8] + '...' if len(api_key) > 8 else 'MISSING'}")
    
    # Apply fixes
    fix_portfolio_manager()
    fix_hybrid_bot()
    fix_other_files()
    
    print("\n✅ ALL FIXES APPLIED!")
    print("🚀 Railway bots should now work correctly")

if __name__ == "__main__":
    main()
