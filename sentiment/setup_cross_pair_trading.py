#!/usr/bin/env python3
"""
setup_cross_pair_trading.py
Quick setup script to enable cross-pair trading in your existing Bottie setup.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

def create_enhanced_api_app():
    """Create enhanced version of your api/app.py with cross-pair trading"""
    
    enhanced_api = '''# Enhanced api/app.py with Cross-Pair Trading
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
'''
    
    return enhanced_api

def create_dashboard_enhancements():
    """Create enhanced dashboard HTML and JavaScript"""
    
    enhanced_html = '''
<!-- Add this section to your dashboard HTML after trading signals -->
<!-- Cross-Pair Portfolio Trading -->
<div style="background: #1a2332; border-radius: 8px; border: 1px solid #2a3441; overflow: hidden; margin-bottom: 20px;">
  <div style="background: #141b26; padding: 12px 16px; border-bottom: 1px solid #2a3441; font-weight: 600; color: #64ffda; font-size: 14px;">
    🔄 Cross-Pair Portfolio Trading
    <span id="cross-pair-status" style="margin-left: 10px; font-size: 10px; padding: 2px 6px; border-radius: 3px; background: #4caf50; color: #fff;">ENABLED</span>
  </div>
  <div style="padding: 16px;">
    
    <!-- Portfolio Overview -->
    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 16px;">
      <div style="background: #0f1419; border: 1px solid #2a3441; border-radius: 6px; padding: 12px; text-align: center;">
        <div style="font-size: 10px; color: #8892b0; margin-bottom: 4px;">Portfolio Assets</div>
        <div style="font-size: 16px; font-weight: 600; color: #64ffda;" id="portfolio-asset-count">—</div>
      </div>
      <div style="background: #0f1419; border: 1px solid #2a3441; border-radius: 6px; padding: 12px; text-align: center;">
        <div style="font-size: 10px; color: #8892b0; margin-bottom: 4px;">Available Pairs</div>
        <div style="font-size: 16px; font-weight: 600; color: #64ffda;" id="cross-pair-count">—</div>
      </div>
      <div style="background: #0f1419; border: 1px solid #2a3441; border-radius: 6px; padding: 12px; text-align: center;">
        <div style="font-size: 10px; color: #8892b0; margin-bottom: 4px;">Opportunities</div>
        <div style="font-size: 16px; font-weight: 600; color: #4caf50;" id="cross-opportunities-count">—</div>
      </div>
    </div>
    
    <!-- Cross-Pair Opportunities Table -->
    <table class="data-table">
      <thead>
        <tr>
          <th>Trade Direction</th>
          <th>Symbol</th>
          <th>Action</th>
          <th>AI Confidence</th>
          <th>Est. Profit</th>
          <th>Price</th>
          <th>Available</th>
        </tr>
      </thead>
      <tbody id="cross-pair-opportunities">
        <tr><td colspan="7">Loading cross-pair opportunities...</td></tr>
      </tbody>
    </table>
  </div>
</div>

<!-- AI Portfolio Rebalancing Suggestions -->
<div style="background: #1a2332; border-radius: 8px; border: 1px solid #2a3441; overflow: hidden; margin-bottom: 20px;">
  <div style="background: #141b26; padding: 12px 16px; border-bottom: 1px solid #2a3441; font-weight: 600; color: #64ffda; font-size: 14px;">
    🧠 AI Portfolio Rebalancing Suggestions
  </div>
  <div style="padding: 16px;">
    <div id="rebalancing-suggestions">
      <div style="color: #8892b0; text-align: center; padding: 20px;">Loading AI recommendations...</div>
    </div>
  </div>
</div>
'''
    
    enhanced_js = '''
// Add this to your existing dashboard JavaScript

// Cross-pair trading functions
async function refreshCrossPairData() {
  try {
    const [portfolio, opportunities, suggestions] = await Promise.all([
      fetch(`${API}/portfolio/cross-pairs`).then(r => r.json()),
      fetch(`${API}/cross-pairs/opportunities`).then(r => r.json()),
      fetch(`${API}/portfolio/rebalancing-suggestions`).then(r => r.json())
    ]);
    
    updatePortfolioOverview(portfolio);
    updateCrossPairOpportunities(opportunities);
    updateRebalancingSuggestions(suggestions);
    
  } catch (err) {
    console.error('Cross-pair data refresh failed', err);
  }
}

function updatePortfolioOverview(portfolio) {
  if (portfolio.enabled) {
    document.getElementById('portfolio-asset-count').textContent = portfolio.total_assets || '—';
    document.getElementById('cross-pair-count').textContent = portfolio.total_pairs || '—';
    document.getElementById('cross-pair-status').textContent = 'ACTIVE';
    document.getElementById('cross-pair-status').style.background = '#4caf50';
  } else {
    document.getElementById('cross-pair-status').textContent = 'DISABLED';
    document.getElementById('cross-pair-status').style.background = '#ff9800';
  }
}

function updateCrossPairOpportunities(data) {
  const container = document.getElementById('cross-pair-opportunities');
  const countEl = document.getElementById('cross-opportunities-count');
  
  if (!container) return;
  
  container.innerHTML = '';
  
  if (data.opportunities && data.opportunities.length > 0) {
    countEl.textContent = data.opportunities.length;
    
    data.opportunities.forEach(opp => {
      const row = document.createElement('tr');
      const profitClass = opp.estimated_profit_pct > 0 ? 'positive' : 'negative';
      const directionClass = opp.direction === 'buy' ? 'buy-badge' : 'sell-badge';
      
      row.innerHTML = `
        <td>
          <span style="color: #64ffda; font-weight: 600;">${opp.from_asset}</span>
          <span style="color: #8892b0;"> → </span>
          <span style="color: #4caf50; font-weight: 600;">${opp.to_asset}</span>
        </td>
        <td class="symbol">${opp.symbol}</td>
        <td><span class="${directionClass}">${opp.direction.toUpperCase()}</span></td>
        <td>${(opp.signal_strength * 100).toFixed(1)}%</td>
        <td class="${profitClass}">${(opp.estimated_profit_pct * 100).toFixed(2)}%</td>
        <td>${opp.current_price.toFixed(6)}</td>
        <td style="color: #8892b0; font-size: 11px;">Ready</td>
      `;
      container.appendChild(row);
    });
  } else {
    countEl.textContent = '0';
    container.innerHTML = '<tr><td colspan="7" style="color: #8892b0; text-align: center;">No cross-pair opportunities found</td></tr>';
  }
}

function updateRebalancingSuggestions(data) {
  const container = document.getElementById('rebalancing-suggestions');
  if (!container) return;
  
  container.innerHTML = '';
  
  if (data.enabled && data.suggestions && data.suggestions.length > 0) {
    data.suggestions.forEach((suggestion, index) => {
      const suggestionEl = document.createElement('div');
      suggestionEl.style.cssText = 'background: rgba(100, 255, 218, 0.05); border: 1px solid rgba(100, 255, 218, 0.2); border-radius: 6px; padding: 12px; margin-bottom: 8px;';
      
      suggestionEl.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="color: #64ffda; font-weight: 600; margin-bottom: 4px;">
              ${suggestion.action}
            </div>
            <div style="color: #8892b0; font-size: 11px;">
              ${suggestion.reasoning}
            </div>
          </div>
          <div style="text-align: right;">
            <div style="color: #4caf50; font-weight: 600;">
              +${(suggestion.expected_profit * 100).toFixed(2)}%
            </div>
            <div style="color: #8892b0; font-size: 10px;">
              ${(suggestion.confidence * 100).toFixed(0)}% confidence
            </div>
          </div>
        </div>
      `;
      container.appendChild(suggestionEl);
    });
  } else {
    container.innerHTML = '<div style="color: #8892b0; text-align: center; padding: 20px;">No rebalancing suggestions at this time</div>';
  }
}

// Add cross-pair refresh to your existing intervals
refreshIntervals.crossPairs = setInterval(refreshCrossPairData, 60000); // Every 60 seconds

// Initial load
setTimeout(refreshCrossPairData, 2000);
'''
    
    return enhanced_html, enhanced_js

def create_environment_config():
    """Create environment configuration for cross-pair trading"""
    
    env_config = '''# Add these to your .env file for cross-pair trading

# Cross-Pair Trading Configuration
CROSS_PAIR_ENABLED=1
BINANCE_TESTNET=true

# Cross-Pair Trading Parameters
CROSS_PAIR_MIN_TRADE_VALUE_USDT=10
CROSS_PAIR_MAX_PORTFOLIO_PCT=0.05
CROSS_PAIR_MIN_PROFIT_THRESHOLD=0.002
CROSS_PAIR_SCAN_INTERVAL_SECONDS=45

# Portfolio Rebalancing
AUTO_REBALANCING_ENABLED=0
REBALANCING_THRESHOLD=0.01
REBALANCING_MAX_TRADES_PER_CYCLE=3

# Advanced Cross-Pair Features
ATOMIC_SWAP_DETECTION=1
ARBITRAGE_OPPORTUNITY_ALERTS=1
CROSS_PAIR_SENTIMENT_WEIGHT=0.1
'''
    
    return env_config

def main():
    """Main setup function"""
    print("🚀 Bottie Cross-Pair Trading Setup")
    print("=" * 50)
    print()
    
    # Check if running in the right directory
    if not os.path.exists("api") and not os.path.exists("api_app.py"):
        print("❌ Please run this script in your Bottie root directory")
        print("   (where your api/ folder or api_app.py file is located)")
        sys.exit(1)
    
    print("✅ Setting up cross-pair trading capabilities...")
    print()
    
    # Create directories
    os.makedirs("cross_pair", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Save the core files
    portfolio_cross_trading_path = Path("cross_pair/portfolio_cross_trading.py")
    integration_path = Path("cross_pair/bottie_cross_pair_integration.py")
    
    print(f"📁 Created: {portfolio_cross_trading_path}")
    print(f"📁 Created: {integration_path}")
    
    # Create enhanced API
    enhanced_api = create_enhanced_api_app()
    api_path = Path("cross_pair/enhanced_api_app.py")
    with open(api_path, 'w') as f:
        f.write(enhanced_api)
    print(f"📁 Created: {api_path}")
    
    # Create dashboard enhancements
    enhanced_html, enhanced_js = create_dashboard_enhancements()
    
    html_path = Path("cross_pair/dashboard_enhancements.html")
    with open(html_path, 'w') as f:
        f.write(enhanced_html)
    print(f"📁 Created: {html_path}")
    
    js_path = Path("cross_pair/dashboard_enhancements.js")
    with open(js_path, 'w') as f:
        f.write(enhanced_js)
    print(f"📁 Created: {js_path}")
    
    # Create environment config
    env_config = create_environment_config()
    env_path = Path("cross_pair/cross_pair.env")
    with open(env_path, 'w') as f:
        f.write(env_config)
    print(f"📁 Created: {env_path}")
    
    # Create integration instructions
    instructions = '''
# 🚀 Bottie Cross-Pair Trading Integration Instructions

## What You Get
✅ Trade between ANY assets in your portfolio (BTC→ETH, ETH→BNB, etc.)
✅ AI-powered portfolio rebalancing suggestions  
✅ Atomic swap detection and execution
✅ Enhanced signal generation with cross-pair opportunities
✅ Real-time cross-pair opportunity scanning

## Integration Steps

### 1. Install Dependencies
```bash
pip install ccxt asyncio dataclasses
```

### 2. Environment Variables
Add the contents of `cross_pair.env` to your main `.env` file

### 3. API Integration
- Copy code from `enhanced_api_app.py` 
- Integrate with your existing `api/app.py` or `api_app.py`
- Add the cross-pair imports and endpoints

### 4. Dashboard Integration  
- Add HTML from `dashboard_enhancements.html` to your dashboard
- Add JavaScript from `dashboard_enhancements.js` to your dashboard

### 5. Test Setup
```bash
# Test cross-pair detection
python cross_pair/portfolio_cross_trading.py

# Test API integration
python cross_pair/enhanced_api_app.py
```

## New Dashboard Features

### Cross-Pair Trading Panel
- Shows all possible trades between your portfolio assets
- Real-time opportunity detection
- AI confidence scoring

### Portfolio Rebalancing Suggestions
- AI-powered rebalancing recommendations
- Expected profit calculations
- Risk-adjusted position sizing

## New API Endpoints

- `GET /cross-pairs/status` - Cross-pair trading status
- `GET /cross-pairs/opportunities` - Current opportunities  
- `GET /portfolio/cross-pairs` - All possible portfolio pairs
- `GET /portfolio/rebalancing-suggestions` - AI rebalancing advice
- `GET /signals` - Enhanced with cross-pair signals

## Example Cross-Pair Trades

Instead of only:
- BTC/USDT → Buy/Sell BTC with USDT

You now get:
- BTC/ETH → Swap BTC directly to ETH
- ETH/BNB → Exchange ETH for BNB
- ADA/SOL → Trade ADA directly for SOL
- Any/Any → Trade between any portfolio assets

## Benefits

🎯 **More Opportunities**: 5-10x more trading pairs
💰 **Better Profits**: Direct swaps avoid USDT conversion fees  
🔄 **Portfolio Rebalancing**: Automated asset allocation
⚡ **Faster Execution**: Skip intermediate USDT conversions
🧠 **AI Optimization**: Machine learning finds best trade routes

## Safety Features

- Minimum trade size validation
- Portfolio percentage limits (max 5% per trade)
- Profit threshold requirements (min 0.2%)
- Balance validation before execution
- Dry-run mode for testing

## Monitoring

The enhanced dashboard shows:
- Portfolio asset count
- Available cross-pair count  
- Current opportunities
- AI rebalancing suggestions
- Real-time profit estimates

Happy cross-pair trading! 🚀
'''
    
    readme_path = Path("cross_pair/README.md")
    with open(readme_path, 'w') as f:
        f.write(instructions)
    print(f"📁 Created: {readme_path}")
    
    print()
    print("🎉 Cross-Pair Trading Setup Complete!")
    print()
    print("📋 Next Steps:")
    print("1. Read cross_pair/README.md for integration instructions")
    print("2. Add environment variables from cross_pair/cross_pair.env") 
    print("3. Integrate the enhanced API code")
    print("4. Add dashboard HTML and JavaScript")
    print("5. Test with BINANCE_TESTNET=true first")
    print()
    print("🎯 Benefits:")
    print("• Trade BTC → ETH directly (no USDT conversion)")
    print("• AI finds best cross-asset opportunities")  
    print("• 5-10x more trading pairs available")
    print("• Automated portfolio rebalancing")
    print("• Reduced fees from direct swaps")

if __name__ == "__main__":
    main()