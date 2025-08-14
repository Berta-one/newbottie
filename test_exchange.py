import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment
os.environ["ENVIRONMENT"] = "production"
os.environ["TRADE_ENABLED"] = "1"

def test_exchange_connection():
    """Test exchange connection with proper error handling"""
    print("🔍 Testing exchange connection...")
    
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment loaded")
        
        # Check credentials
        api_key = os.getenv('BINANCE_API_KEY', '')
        api_secret = os.getenv('BINANCE_API_SECRET', '')
        
        print(f"API Key length: {len(api_key) if api_key else 0}")
        print(f"API Secret length: {len(api_secret) if api_secret else 0}")
        
        if not api_key or not api_secret:
            print("❌ Missing API credentials!")
            return False
            
        # Test ccxt
        import ccxt
        print("✅ CCXT imported")
        
        # Initialize exchange
        trade_enabled = os.getenv('TRADE_ENABLED', '0') == '1'
        use_live_trading = trade_enabled and os.getenv('ENVIRONMENT', '') == 'production'
        
        print(f"Trade enabled: {trade_enabled}")
        print(f"Use live trading: {use_live_trading}")
        
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': not use_live_trading,
            'enableRateLimit': True,
        })
        
        print("✅ Exchange client created")
        
        # Test connection
        print("🔍 Testing connection...")
        markets = exchange.load_markets()
        print(f"✅ Markets loaded: {len(markets)} markets")
        
        # Test balance
        print("🔍 Testing balance fetch...")
        balance = exchange.fetch_balance()
        print(f"✅ Balance fetched successfully")
        
        # Show actual balance
        total_usdt = balance['total'].get('USDT', 0)
        
        # Add crypto values converted to USDT
        crypto_value = 0
        for symbol, amount in balance['total'].items():
            if symbol != 'USDT' and amount > 0:
                print(f"  - {symbol}: {amount}")
                try:
                    ticker = exchange.fetch_ticker(f"{symbol}/USDT")
                    value = amount * ticker['last']
                    crypto_value += value
                    print(f"    Value: ${value:.2f}")
                except Exception as e:
                    print(f"    Price error: {e}")
        
        total_value = total_usdt + crypto_value
        print(f"💰 Total Portfolio Value: ${total_value:.2f}")
        print(f"   - USDT: ${total_usdt:.2f}")
        print(f"   - Crypto: ${crypto_value:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Exchange connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_exchange_connection()
