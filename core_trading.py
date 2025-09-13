#!/usr/bin/env python3
"""
Core Trading System - NO DASHBOARD - Just Trading
Pure trading functionality that actually works
"""

import os
import sys
import time
import json
import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Trading state
trading_data = {
    'balance': 0.0,
    'positions': {},
    'trades': [],
    'signals': [],
    'trading_active': True,
    'last_update': time.time()
}

def log_trade(message):
    """Log trading activity"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    trading_data['trades'].append(log_entry)
    if len(trading_data['trades']) > 100:
        trading_data['trades'] = trading_data['trades'][-50:]
    logger.info(message)

def get_real_data():
    """Get real trading data from Binance"""
    try:
        import ccxt
        
        # Get API keys
        api_key = os.getenv('BINANCE_API_KEY', '')
        api_secret = os.getenv('BINANCE_API_SECRET', '')
        
        if not api_key or not api_secret:
            log_trade("⚠️ No API keys - cannot fetch real data")
            return False
        
        # Create real Binance client
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,
            'enableRateLimit': True,
        })
        
        # Get real balance
        balance = exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('total', 0)
        
        # Get real positions
        positions = {}
        total_position_value = 0
        
        for asset, amount in balance.get('total', {}).items():
            if amount > 0.001 and asset != 'USDT':
                try:
                    symbol = f"{asset}/USDT"
                    ticker = exchange.fetch_ticker(symbol)
                    price = ticker['last']
                    value = amount * price
                    
                    if value > 10:  # Only significant positions
                        positions[symbol] = {
                            'asset': asset,
                            'quantity': amount,
                            'price': price,
                            'value': value
                        }
                        total_position_value += value
                        log_trade(f"💼 {asset}: {amount:.6f} @ ${price:,.2f} = ${value:.2f}")
                
                except Exception as e:
                    log_trade(f"⚠️ Error processing {asset}: {e}")
        
        # Update trading data
        trading_data['balance'] = usdt_balance + total_position_value
        trading_data['positions'] = positions
        trading_data['last_update'] = time.time()
        
        log_trade(f"💰 Total Equity: ${trading_data['balance']:,.2f}")
        log_trade(f"📊 Positions: {len(positions)}")
        
        return True
        
    except Exception as e:
        log_trade(f"❌ Real data fetch error: {e}")
        return False

def generate_trading_signals():
    """Generate real trading signals"""
    try:
        import ccxt
        
        # Public client for price data
        exchange = ccxt.binance({'enableRateLimit': True})
        
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']
        
        for symbol in symbols:
            try:
                ticker = exchange.fetch_ticker(symbol)
                price = ticker['last']
                change_24h = ticker.get('percentage', 0)
                
                # Simple signal logic based on real price movement
                if change_24h > 5:
                    signal = 'SELL'
                    confidence = min(0.9, 0.6 + (change_24h - 5) * 0.02)
                elif change_24h < -5:
                    signal = 'BUY'
                    confidence = min(0.9, 0.6 + abs(change_24h + 5) * 0.02)
                else:
                    signal = 'HOLD'
                    confidence = 0.5
                
                signal_data = {
                    'symbol': symbol,
                    'signal': signal,
                    'confidence': confidence,
                    'price': price,
                    'change_24h': change_24h,
                    'timestamp': time.time()
                }
                
                trading_data['signals'].append(signal_data)
                log_trade(f"🎯 {symbol}: {signal} ({confidence:.0%}) @ ${price:,.2f} ({change_24h:+.1f}%)")
                
            except Exception as e:
                log_trade(f"❌ Signal error for {symbol}: {e}")
        
        # Keep only recent signals
        if len(trading_data['signals']) > 100:
            trading_data['signals'] = trading_data['signals'][-50:]
            
    except Exception as e:
        log_trade(f"❌ Signal generation error: {e}")

async def trading_loop():
    """Core trading loop"""
    log_trade("🚀 Core trading loop started")
    
    while True:
        try:
            if trading_data['trading_active']:
                # Get real data
                if get_real_data():
                    log_trade("✅ Real data updated")
                
                # Generate signals
                generate_trading_signals()
                
                log_trade("🔄 Trading cycle completed")
            
        except Exception as e:
            log_trade(f"❌ Trading loop error: {e}")
        
        await asyncio.sleep(60)  # Update every minute

# Minimal FastAPI app - NO DASHBOARD
app = FastAPI(title="Core Trading System")

@app.get("/")
def root():
    return JSONResponse({
        "system": "Core Trading Bot",
        "status": "operational",
        "balance": trading_data['balance'],
        "positions": len(trading_data['positions']),
        "last_update": trading_data['last_update']
    })

@app.get("/health")
def health():
    return JSONResponse({
        "status": "healthy",
        "balance": trading_data['balance'],
        "positions": len(trading_data['positions']),
        "trading_active": trading_data['trading_active']
    })

@app.get("/status")
def status():
    return JSONResponse({
        "ok": True,
        "balance": trading_data['balance'],
        "positions": trading_data['positions'],
        "signals": trading_data['signals'][-5:],
        "trading_active": trading_data['trading_active']
    })

@app.get("/logs")
def logs():
    return JSONResponse({
        "logs": trading_data['trades'][-20:],
        "count": len(trading_data['trades'])
    })

@app.post("/trading/start")
def start_trading():
    trading_data['trading_active'] = True
    log_trade("🟢 Trading STARTED")
    return JSONResponse({"ok": True, "message": "Trading started"})

@app.post("/trading/stop")
def stop_trading():
    trading_data['trading_active'] = False
    log_trade("🔴 Trading STOPPED")
    return JSONResponse({"ok": True, "message": "Trading stopped"})

@app.on_event("startup")
async def startup():
    log_trade("🚀 Core Trading System starting...")
    
    # Start trading loop
    asyncio.create_task(trading_loop())
    
    log_trade("✅ Core trading system ready")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    log_trade(f"🚀 Starting core trading system on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)