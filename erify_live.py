# verify_live.py
import os
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()

def verify_live():
    use_testnet = os.getenv('USE_TESTNET', 'true').lower()
    api_key = os.getenv('BINANCE_API_KEY')
    
    print(f"USE_TESTNET: {use_testnet}")
    print(f"API Key: {'✅ Set' if api_key else '❌ Missing'}")
    
    if use_testnet == 'true':
        print("⚠️ WARNING: Still in TESTNET mode!")
        return False
    
    try:
        client = Client(api_key, os.getenv('BINANCE_API_SECRET'))
        account = client.get_account()
        print(f"✅ Connected to Binance LIVE")
        
        usdt_balance = next(
            (float(b['free']) for b in account['balances'] if b['asset'] == 'USDT'), 0
        )
        print(f"USDT Balance: ${usdt_balance:.2f}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    verify_live()
