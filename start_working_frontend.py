import os
import asyncio
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
import sys
sys.path.insert(0, str(project_root))

async def start_working_api():
    """Start a working API server with real data"""
    print("🚀 Starting WORKING API server with REAL data...")
    
    # Set environment
    os.environ["ENVIRONMENT"] = "production"
    os.environ["TRADE_ENABLED"] = "1"
    
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment loaded")
        
        # Import and test exchange first
        import ccxt
        
        api_key = os.getenv('BINANCE_API_KEY', '')
        api_secret = os.getenv('BINANCE_API_SECRET', '')
        
        if not api_key or not api_secret:
            print("❌ Missing API credentials!")
            return
            
        # Create exchange client
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,  # LIVE TRADING
            'enableRateLimit': True,
        })
        
        # Test connection
        markets = exchange.load_markets()
        balance = exchange.fetch_balance()
        
        # Calculate total value
        total_usdt = balance['total'].get('USDT', 0)
        crypto_value = 0
        positions = {}
        
        for symbol, amount in balance['total'].items():
            if symbol != 'USDT' and amount > 0:
                try:
                    ticker = exchange.fetch_ticker(f"{symbol}/USDT")
                    value = amount * ticker['last']
                    crypto_value += value
                    
                    positions[f"{symbol}USDT"] = {
                        "symbol": f"{symbol}USDT",
                        "quantity": amount,
                        "current_price": ticker['last'],
                        "market_value": value,
                        "side": "LONG",
                        "type": "SPOT_HOLDING"
                    }
                except:
                    pass
        
        total_value = total_usdt + crypto_value
        
        print(f"✅ Exchange connected: {len(markets)} markets")
        print(f"💰 Total Portfolio: ${total_value:.2f}")
        print(f"🔍 Found {len(positions)} real positions")
        
        # Patch the global exchange client in the API
        from api import app as api_module
        api_module.exchange_client = exchange
        api_module.real_balance = {**balance['total'], 'total_usdt': total_value}
        api_module.real_positions = positions
        
        print("✅ API patched with real exchange client")
        
        # Start the server
        print("🚀 Starting API server on http://127.0.0.1:8000")
        config = uvicorn.Config(
            app="api.app:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Open the local frontend
        import webbrowser
        import time
        
        async def open_frontend():
            await asyncio.sleep(2)  # Wait for server to start
            local_frontend = f"file:///{project_root}/web/index_local.html"
            print(f"🌐 Opening frontend: {local_frontend}")
            webbrowser.open(local_frontend)
        
        # Start both server and frontend
        await asyncio.gather(
            server.serve(),
            open_frontend()
        )
        
    except Exception as e:
        print(f"❌ Error starting API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(start_working_api())
