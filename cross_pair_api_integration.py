
# ===== CROSS-PAIR TRADING INTEGRATION =====
# Add this section to your api/app.py file

# Cross-pair trading imports (add near top of file)
CROSS_PAIR_ENABLED = os.getenv("CROSS_PAIR_ENABLED", "1").lower() in ("1", "true")

# Cross-pair trading endpoints (add near your other @app.get endpoints)

@app.get("/cross-pairs/status")
async def cross_pair_status():
    """Get cross-pair trading status"""
    return {
        "enabled": CROSS_PAIR_ENABLED,
        "testnet": os.getenv("BINANCE_TESTNET", "true").lower() == "true",
        "timestamp": time.time()
    }

@app.get("/portfolio/cross-pairs")
async def get_portfolio_cross_pairs():
    """Get all possible cross-trading pairs in portfolio"""
    if not CROSS_PAIR_ENABLED:
        return {"enabled": False, "pairs": []}
    
    try:
        await _ensure_exchange()
        balance = exchange.fetch_balance()
        
        # Get assets with non-zero balance
        portfolio_assets = []
        for asset, amount in balance['total'].items():
            if amount > 0:
                portfolio_assets.append(asset)
        
        # Find available cross-pairs
        markets = exchange.markets
        available_pairs = []
        
        for asset1 in portfolio_assets:
            for asset2 in portfolio_assets:
                if asset1 != asset2:
                    symbol1 = f"{asset1}/{asset2}"
                    symbol2 = f"{asset2}/{asset1}"
                    
                    if symbol1 in markets:
                        available_pairs.append(symbol1)
                    elif symbol2 in markets:
                        available_pairs.append(symbol2)
        
        return {
            "enabled": True,
            "portfolio_assets": portfolio_assets,
            "available_pairs": available_pairs,
            "total_pairs": len(available_pairs),
            "total_assets": len(portfolio_assets)
        }
        
    except Exception as e:
        return {"enabled": False, "error": str(e)}

@app.get("/cross-pairs/opportunities")
async def get_cross_pair_opportunities():
    """Get current cross-pair trading opportunities"""
    if not CROSS_PAIR_ENABLED:
        return {"enabled": False, "opportunities": []}
    
    try:
        await _ensure_exchange()
        balance = exchange.fetch_balance()
        
        # Get portfolio assets
        portfolio_assets = [asset for asset, amount in balance['total'].items() if amount > 0]
        
        # Find cross-pair symbols
        markets = exchange.markets
        cross_symbols = []
        
        for asset1 in portfolio_assets:
            for asset2 in portfolio_assets:
                if asset1 != asset2:
                    symbol1 = f"{asset1}/{asset2}"
                    symbol2 = f"{asset2}/{asset1}"
                    
                    if symbol1 in markets:
                        cross_symbols.append(symbol1)
                    elif symbol2 in markets:
                        cross_symbols.append(symbol2)
        
        if not cross_symbols:
            return {"enabled": True, "opportunities": [], "message": "No cross-pairs available"}
        
        # Get tickers for cross-pairs
        tickers = exchange.fetch_tickers(cross_symbols[:20])  # Limit to 20 pairs
        
        opportunities = []
        for symbol, ticker in tickers.items():
            base, quote = symbol.split('/')
            
            # Simple signal calculation
            change_pct = ticker.get('percentage', 0) or 0
            signal_strength = 0.5 + (change_pct / 100.0 * 2)
            signal_strength = max(0.0, min(1.0, signal_strength))
            
            # Estimate profit potential
            profit_pct = abs(change_pct / 100.0) * 0.1  # Simple estimation
            
            opportunity = {
                "symbol": symbol,
                "from_asset": base,
                "to_asset": quote,
                "direction": "buy" if change_pct > 0 else "sell",
                "current_price": ticker['last'],
                "signal_strength": signal_strength,
                "estimated_profit_pct": profit_pct,
                "volume_24h": ticker.get('quoteVolume', 0),
                "change_24h_pct": change_pct,
                "timestamp": time.time()
            }
            opportunities.append(opportunity)
        
        # Sort by signal strength
        opportunities.sort(key=lambda x: x['signal_strength'], reverse=True)
        
        return {
            "enabled": True,
            "opportunities": opportunities[:10],  # Top 10
            "count": len(opportunities),
            "scan_time": time.time()
        }
        
    except Exception as e:
        return {"enabled": False, "error": str(e)}

@app.get("/portfolio/rebalancing-suggestions")
async def get_rebalancing_suggestions():
    """Get AI-powered portfolio rebalancing suggestions"""
    if not CROSS_PAIR_ENABLED:
        return {"enabled": False, "suggestions": []}
    
    try:
        # Get cross-pair opportunities first
        opportunities_response = await get_cross_pair_opportunities()
        
        if not opportunities_response.get("enabled") or not opportunities_response.get("opportunities"):
            return {"enabled": True, "suggestions": [], "message": "No opportunities available"}
        
        opportunities = opportunities_response["opportunities"]
        suggestions = []
        
        for opp in opportunities[:5]:  # Top 5 opportunities
            if opp["signal_strength"] > 0.6 and opp["estimated_profit_pct"] > 0.005:  # 0.5% min profit
                suggestion = {
                    "action": f"Trade {opp['from_asset']} → {opp['to_asset']}",
                    "symbol": opp["symbol"],
                    "direction": opp["direction"],
                    "confidence": opp["signal_strength"],
                    "expected_profit": opp["estimated_profit_pct"],
                    "reasoning": f"AI detected {opp['signal_strength']:.1%} confidence signal with {opp['change_24h_pct']:+.2f}% momentum",
                    "priority": "high" if opp["signal_strength"] > 0.8 else "medium",
                    "timestamp": time.time()
                }
                suggestions.append(suggestion)
        
        return {
            "enabled": True,
            "suggestions": suggestions,
            "count": len(suggestions),
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {"enabled": False, "error": str(e)}

# ===== END CROSS-PAIR TRADING INTEGRATION =====
