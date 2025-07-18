#!/usr/bin/env python3
"""Fix hardcoded testnet settings"""

import os

files_to_fix = [
    'hybrid_bot.py',
    'autonomous_quantum_bot.py', 
    'quantum_trading_integration.py'
]

for filename in files_to_fix:
    if os.path.exists(filename):
        print(f"Fixing {filename}...")
        
        with open(filename, 'r') as f:
            content = f.read()
        
        # Comment out testnet URLs
        content = content.replace(
            'client.API_URL = "https://testnet.binance.vision/api"',
            '# client.API_URL = "https://testnet.binance.vision/api"  # FIXED: Force live mode'
        )
        
        content = content.replace(
            "self.client.API_URL = \"https://testnet.binance.vision/api\"",
            "# self.client.API_URL = \"https://testnet.binance.vision/api\"  # FIXED: Force live mode"
        )
        
        with open(filename, 'w') as f:
            f.write(content)
        
        print(f"✅ Fixed {filename}")

print("🎉 All testnet URLs commented out - trades will now use live mode!")