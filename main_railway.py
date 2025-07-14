# Simplified Railway bot without ML
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from binance.client import Client
from strategy import check_breakout_enhanced, get_strategy_confidence

load_dotenv()

print("🚀 Railway Trading Bot Starting...")

# Configuration
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET") 
USE_TESTNET = os.getenv("USE_TESTNET", "True").lower() == "true"
TRADE_SYMBOL = os.getenv("TRADE_SYMBOL", "BTCUSDT")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "300"))

try:
    client = Client(API_KEY, API_SECRET)
    if USE_TESTNET:
        client.API_URL = "https://testnet.binance.vision/api"
    
    print("✅ Connected to Binance")
    
    loop_count = 0
    while True:
        try:
            loop_count += 1
            print(f"\n🔄 Loop #{loop_count} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Get market data
            klines = client.get_klines(symbol=TRADE_SYMBOL, interval="1m", limit=120)
            ticker = client.get_symbol_ticker(symbol=TRADE_SYMBOL)
            current_price = float(ticker['price'])
            
            # Analyze
            signal = check_breakout_enhanced(klines)
            confidence = get_strategy_confidence(klines)
            
            print(f"📈 {TRADE_SYMBOL}: ${current_price:.2f}")
            print(f"🎯 Signal: {signal} (confidence: {confidence:.2f})")
            
            time.sleep(SCAN_INTERVAL)
            
        except Exception as e:
            print(f"❌ Loop error: {e}")
            time.sleep(60)
            
except Exception as e:
    print(f"❌ Bot failed: {e}")
