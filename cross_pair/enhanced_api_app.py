# Enhanced api/app.py with Cross-Pair Trading
import os
import time
import asyncio
import logging
from typing import Dict, List, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Your existing imports
# ... (keep all your existing imports)

# NEW: Cross-pair trading imports
from portfolio_cross_trading import PortfolioCrossPairEngine
from bottie_cross_pair_integration import (
    BottieCrossPairSignalGenerator, 
    add_cross_pair_endpoints, 
    enhanced_signals_endpoint
)

# Your existing FastAPI app setup
app = FastAPI(title="Bottie API Enhanced", version="2.1.0")
app.add_middleware(CORSMiddleware, ...)  # Your existing CORS setup

# NEW: Initialize cross-pair trading
CROSS_PAIR_ENABLED = os.getenv("CROSS_PAIR_ENABLED", "1").lower() in ("1", "true")

if CROSS_PAIR_ENABLED:
    cross_signal_gen = BottieCrossPairSignalGenerator(
        api_key=os.getenv("BINANCE_API_KEY"),
        api_secret=os.getenv("BINANCE_API_SECRET"),
        testnet=os.getenv("BINANCE_TESTNET", "true").lower() == "true"
    )
    
    # Add cross-pair endpoints to your existing app
    add_cross_pair_endpoints(app, cross_signal_gen)
    
    print("✅ Cross-pair trading enabled")
else:
    cross_signal_gen = None
    print("⚠️ Cross-pair trading disabled")

# Your existing endpoints...
# ... (keep all your existing endpoints)

# ENHANCED: Modify your existing /signals endpoint
@app.get("/signals")
async def signals():
    """Enhanced signals endpoint with cross-pair opportunities"""
    try:
        # Your existing signal generation logic
        existing_signals = []  # Replace with your actual signal generation
        
        if CROSS_PAIR_ENABLED and cross_signal_gen:
            # Enhanced with cross-pairs
            enhanced_data = await enhanced_signals_endpoint(cross_signal_gen, existing_signals)
            return enhanced_data
        else:
            # Fallback to existing signals only
            return {"signals": existing_signals}
            
    except Exception as e:
        logging.error(f"Signals endpoint error: {e}")
        return {"signals": [], "error": str(e)}

# NEW: Cross-pair specific endpoints
@app.get("/portfolio/cross-pairs")
async def get_portfolio_cross_pairs():
    """Get all possible cross-trading pairs in your portfolio"""
    if not CROSS_PAIR_ENABLED or not cross_signal_gen:
        return {"enabled": False, "pairs": []}
    
    try:
        await cross_signal_gen.initialize()
        pairs = list(cross_signal_gen.cross_engine.available_pairs.keys())
        assets = list(cross_signal_gen.cross_engine.portfolio_assets)
        
        return {
            "enabled": True,
            "portfolio_assets": assets,
            "available_pairs": pairs,
            "total_pairs": len(pairs),
            "total_assets": len(assets)
        }
    except Exception as e:
        return {"enabled": False, "error": str(e)}

@app.get("/portfolio/rebalancing-suggestions")
async def get_rebalancing_suggestions():
    """Get AI-powered portfolio rebalancing suggestions"""
    if not CROSS_PAIR_ENABLED or not cross_signal_gen:
        return {"enabled": False, "suggestions": []}
    
    try:
        await cross_signal_gen.initialize()
        opportunities = cross_signal_gen.cross_engine.cross_opportunities
        
        # AI-powered rebalancing logic
        suggestions = []
        for opp in opportunities[:10]:  # Top 10 opportunities
            if opp.signal_strength > 0.6 and opp.estimated_profit_pct > 0.005:  # 0.5% min profit
                suggestions.append({
                    "action": f"Trade {opp.from_asset} → {opp.to_asset}",
                    "symbol": opp.symbol,
                    "direction": opp.direction,
                    "confidence": opp.signal_strength,
                    "expected_profit": opp.estimated_profit_pct,
                    "reasoning": f"AI detected {opp.signal_strength:.1%} confidence signal"
                })
        
        return {
            "enabled": True,
            "suggestions": suggestions,
            "timestamp": time.time()
        }
    except Exception as e:
        return {"enabled": False, "error": str(e)}

# NEW: Background task for cross-pair scanning
async def cross_pair_background_scanner():
    """Background task to continuously scan for cross-pair opportunities"""
    if not CROSS_PAIR_ENABLED or not cross_signal_gen:
        return
    
    while True:
        try:
            await cross_signal_gen.initialize()
            await cross_signal_gen.cross_engine.scan_cross_opportunities()
            await asyncio.sleep(45)  # Scan every 45 seconds
        except Exception as e:
            logging.error(f"Cross-pair background scan error: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_tasks():
    """Enhanced startup with cross-pair scanning"""
    # Your existing startup tasks
    # ...
    
    # NEW: Start cross-pair background scanning
    if CROSS_PAIR_ENABLED:
        asyncio.create_task(cross_pair_background_scanner())

# Your existing endpoints and code...
# ... (keep everything else as-is)
