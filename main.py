 -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Single-Pair Crypto Trading Bot
Simple version for testing API connectivity
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_api_connection():
    """Test Binance API connection"""
    try:
        from binance.client import Client

        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        use_testnet = os.getenv("USE_TESTNET", "True").lower() == "true"

        if not api_key or not api_secret:
            print("âŒ API credentials not found in environment")
            return False

        # Initialize client
        client = Client(api_key, api_secret)

        if use_testnet:
            client.API_URL = "https://testnet.binance.vision/api"
            print("ðŸ§ª Using Binance Testnet")
        else:
            print("âš ï¸ Using LIVE Binance API")

        # Test connection
        account = client.get_account()
        print(f"âœ… API Connection Successful!")
        print(f"ðŸ“Š Account Type: {account.get('accountType', 'Unknown')}")
        print(f"ðŸ’° Can Trade: {account.get('canTrade', False)}")

        # Test market data
        ticker = client.get_symbol_ticker(symbol="BTCUSDT")
        print(f"ðŸ“ˆ BTC Price: ${float(ticker['price']):,.2f}")

        return True

    except Exception as e:
        print(f"âŒ API Connection Failed: {e}")
        return False


def simple_trading_loop():
    """Simple trading loop for demonstration"""
    print("ðŸ¤– Simple Trading Bot Started")
    print("=" * 50)

    # Test API first
    if not test_api_connection():
        print("ðŸ›‘ Stopping bot due to API issues")
        return

    print("\nðŸ”„ Starting trading loop...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"â° {current_time} - Bot running... (monitoring markets)")

            # Add your trading logic here
            # For now, just sleep and show status
            time.sleep(30)

    except KeyboardInterrupt:
        print("\nðŸ›‘ Bot stopped by user")
    except Exception as e:
        print(f"\nâŒ Bot error: {e}")


if __name__ == "__main__":
    simple_trading_loop()

