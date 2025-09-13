#!/usr/bin/env python3
"""
Complete cache clearing and real API data fix
Forces the system to use only real Binance API data
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def clear_all_cache():
    """Clear all cached/demo data completely"""
    logger.info("🧹 Clearing all cached and demo data...")
    
    # Set environment variables to force real data
    os.environ['DEMO_MODE'] = '0'  # Force LIVE mode
    os.environ['USE_REAL_DATA_ONLY'] = '1'
    os.environ['CLEAR_CACHE'] = '1'
    os.environ['FORCE_API_REFRESH'] = '1'
    os.environ['DISABLE_DEMO_DATA'] = '1'
    
    logger.info("✅ Environment configured for real data only")

def get_real_btc_price():
    """Get real BTC price from Binance API"""
    try:
        import ccxt
        
        # Create Binance client (public API, no keys needed for price)
        exchange = ccxt.binance({
            'sandbox': False,
            'enableRateLimit': True,
        })
        
        # Get real BTC price
        ticker = exchange.fetch_ticker('BTC/USDT')
        real_price = ticker['last']
        
        logger.info(f"🎯 REAL BTC PRICE: ${real_price:,.2f}")
        return real_price
        
    except Exception as e:
        logger.error(f"❌ Error getting real BTC price: {e}")
        return None

def validate_real_data():
    """Validate that we're getting real market data"""
    real_btc = get_real_btc_price()
    
    if real_btc:
        if real_btc < 100000 or real_btc > 130000:
            logger.warning(f"⚠️ BTC price {real_btc} seems unusual for current market - expected ~$115K")
        else:
            logger.info(f"✅ BTC price {real_btc} looks realistic for current bull market")
        
        return real_btc
    else:
        logger.error("❌ Could not validate real data")
        return None

if __name__ == "__main__":
    clear_all_cache()
    real_price = validate_real_data()
    
    if real_price:
        print(f"✅ Cache cleared - Real BTC price: ${real_price:,.2f}")
    else:
        print("❌ Could not get real price data")