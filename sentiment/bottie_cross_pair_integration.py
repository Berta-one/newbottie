# bottie_cross_pair_integration.py
"""
Integration module to add cross-pair trading to your existing Bottie API.
Extends your current signal generation to include ALL portfolio pairs.
"""

import asyncio
import logging
from typing import Dict, List, Any
from portfolio_cross_trading import PortfolioCrossPairEngine, CrossPairOpportunity

logger = logging.getLogger("BottieCrossPairIntegration")

class BottieCrossPairSignalGenerator:
    """
    Enhanced signal generator that works with your existing Bottie setup
    but includes cross-pair trading between portfolio assets
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.cross_engine = PortfolioCrossPairEngine(api_key, api_secret, testnet)
        self.initialized = False
        
    async def initialize(self):
        """Initialize the cross-pair engine"""
        if not self.initialized:
            await self.cross_engine.initialize()
            self.initialized = True
            logger.info("Cross-pair signal generator initialized")

    async def generate_enhanced_signals(self, existing_signals: List[Dict] = None) -> List[Dict]:
        """
        Generate signals including both your existing USDT pairs AND cross-pairs
        """
        if not self.initialized:
            await self.initialize()
        
        all_signals = []
        
        # Include existing signals (USDT pairs, etc.)
        if existing_signals:
            all_signals.extend(existing_signals)
        
        # Add cross-pair opportunities
        await self.cross_engine.scan_cross_opportunities()
        
        for opp in self.cross_engine.cross_opportunities:
            # Convert cross-pair opportunity to standard signal format
            signal = self._convert_opportunity_to_signal(opp)
            all_signals.append(signal)
        
        # Sort by signal strength/confidence
        all_signals.sort(key=lambda x: x.get('conf', 0), reverse=True)
        
        return all_signals

    def _convert_opportunity_to_signal(self, opp: CrossPairOpportunity) -> Dict:
        """Convert cross-pair opportunity to standard Bottie signal format"""
        return {
            'symbol': opp.symbol,
            'signal': 'BUY' if opp.direction == 'buy' else 'SELL',
            'conf': opp.signal_strength,
            'ema': 0.5,  # Placeholder - integrate with your EMA calculations
            'ml': 0.5,   # Placeholder - integrate with your ML model
            'q': 0.5,    # Placeholder - integrate with your quantum signals
            'sent': 0.5, # Placeholder - integrate with your sentiment
            'final_prob': opp.signal_strength,
            'thr_buy': 0.6,
            'thr_sell': 0.4,
            't': int(time.time()),
            
            # Cross-pair specific fields
            'from_asset': opp.from_asset,
            'to_asset': opp.to_asset,
            'trade_type': 'cross_pair',
            'estimated_profit': opp.estimated_profit_pct,
            'available_balance': opp.available_balance,
            'min_order_size': opp.min_order_size
        }

    async def get_portfolio_cross_pairs(self) -> Dict[str, Any]:
        """Get current cross-pair trading status for dashboard"""
        if not self.initialized:
            await self.initialize()
        
        return {
            'total_assets': len(self.cross_engine.portfolio_assets),
            'portfolio_assets': list(self.cross_engine.portfolio_assets),
            'available_cross_pairs': len(self.cross_engine.available_pairs),
            'cross_pair_symbols': list(self.cross_engine.available_pairs.keys()),
            'current_opportunities': len(self.cross_engine.cross_opportunities),
            'balances': self.cross_engine.balances
        }

# FastAPI integration for your existing Bottie API
def add_cross_pair_endpoints(app, cross_signal_generator: BottieCrossPairSignalGenerator):
    """
    Add cross-pair endpoints to your existing FastAPI app
    """
    
    @app.get("/cross-pairs/status")
    async def get_cross_pair_status():
        """Get cross-pair trading status"""
        try:
            status = await cross_signal_generator.get_portfolio_cross_pairs()
            return {
                "enabled": True,
                "status": status,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Cross-pair status error: {e}")
            return {"enabled": False, "error": str(e)}
    
    @app.get("/cross-pairs/opportunities")
    async def get_cross_pair_opportunities():
        """Get current cross-pair trading opportunities"""
        try:
            opportunities = []
            for opp in cross_signal_generator.cross_engine.cross_opportunities:
                opportunities.append({
                    'from_asset': opp.from_asset,
                    'to_asset': opp.to_asset,
                    'symbol': opp.symbol,
                    'direction': opp.direction,
                    'signal_strength': opp.signal_strength,
                    'estimated_profit_pct': opp.estimated_profit_pct,
                    'current_price': opp.current_price
                })
            
            return {
                "opportunities": opportunities,
                "count": len(opportunities),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Cross-pair opportunities error: {e}")
            return {"opportunities": [], "error": str(e)}

# Enhanced signals endpoint for your existing API
async def enhanced_signals_endpoint(
    cross_signal_generator: BottieCrossPairSignalGenerator,
    existing_signals: List[Dict] = None
) -> Dict:
    """
    Enhanced version of your /signals endpoint that includes cross-pairs
    """
    try:
        # Generate enhanced signals (existing + cross-pairs)
        all_signals = await cross_signal_generator.generate_enhanced_signals(existing_signals)
        
        # Separate into categories
        usdt_signals = [s for s in all_signals if s.get('trade_type') != 'cross_pair']
        cross_signals = [s for s in all_signals if s.get('trade_type') == 'cross_pair']
        
        return {
            'signals': all_signals,
            'usdt_pairs': usdt_signals,
            'cross_pairs': cross_signals,
            'total_signals': len(all_signals),
            'cross_pair_count': len(cross_signals),
            'timestamp': time.time()
        }
    except Exception as e:
        logger.error(f"Enhanced signals error: {e}")
        return {'signals': [], 'error': str(e)}

# Example modification to your existing api/app.py
"""
# Add this to your existing api/app.py file:

import time
from bottie_cross_pair_integration import BottieCrossPairSignalGenerator, add_cross_pair_endpoints, enhanced_signals_endpoint

# Initialize cross-pair generator
cross_signal_gen = BottieCrossPairSignalGenerator(
    api_key=os.getenv("BINANCE_API_KEY"),
    api_secret=os.getenv("BINANCE_API_SECRET"),
    testnet=False  # Set to True for testing
)

# Add cross-pair endpoints
add_cross_pair_endpoints(app, cross_signal_gen)

# Modify your existing /signals endpoint
@app.get("/signals")
async def signals():
    # Your existing signal generation logic here...
    existing_signals = []  # Your current signals
    
    # Enhanced with cross-pairs
    enhanced_data = await enhanced_signals_endpoint(cross_signal_gen, existing_signals)
    return enhanced_data

# Background task to continuously scan for cross-pair opportunities
@app.on_event("startup")
async def startup_cross_pair_scanning():
    asyncio.create_task(cross_pair_background_scan())

async def cross_pair_background_scan():
    while True:
        try:
            await cross_signal_gen.initialize()
            await cross_signal_gen.cross_engine.scan_cross_opportunities()
            await asyncio.sleep(30)  # Scan every 30 seconds
        except Exception as e:
            logger.error(f"Background cross-pair scan error: {e}")
            await asyncio.sleep(60)
"""

# Dashboard integration - modify your existing dashboard JavaScript
cross_pair_dashboard_js = """
// Add this to your existing dashboard JavaScript

// Fetch cross-pair status
async function refreshCrossPairs() {
  try {
    const [status, opportunities] = await Promise.all([
      fetch(`${API}/cross-pairs/status`).then(r => r.json()),
      fetch(`${API}/cross-pairs/opportunities`).then(r => r.json())
    ]);
    
    updateCrossPairStatus(status);
    updateCrossPairOpportunities(opportunities);
  } catch (err) {
    console.error('Cross-pair refresh failed', err);
  }
}

function updateCrossPairStatus(status) {
  // Update portfolio assets display
  const assetsEl = document.getElementById('portfolio-assets');
  if (assetsEl && status.status) {
    assetsEl.textContent = `${status.status.total_assets} assets, ${status.status.available_cross_pairs} pairs`;
  }
}

function updateCrossPairOpportunities(data) {
  const container = document.getElementById('cross-pair-opportunities');
  if (!container) return;
  
  container.innerHTML = '';
  
  if (data.opportunities && data.opportunities.length > 0) {
    data.opportunities.forEach(opp => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td class="symbol">${opp.from_asset} → ${opp.to_asset}</td>
        <td>${opp.symbol}</td>
        <td><span class="${opp.direction === 'buy' ? 'buy-badge' : 'sell-badge'}">${opp.direction.toUpperCase()}</span></td>
        <td>${(opp.signal_strength * 100).toFixed(1)}%</td>
        <td class="positive">${(opp.estimated_profit_pct * 100).toFixed(2)}%</td>
        <td>${opp.current_price.toFixed(6)}</td>
      `;
      container.appendChild(row);
    });
  } else {
    container.innerHTML = '<tr><td colspan="6">No cross-pair opportunities found</td></tr>';
  }
}

// Add to your existing refresh intervals
refreshIntervals.crossPairs = setInterval(refreshCrossPairs, 45000); // Every 45 seconds
"""

# HTML modification for dashboard
cross_pair_dashboard_html = """
<!-- Add this section to your dashboard HTML -->

<!-- Cross-Pair Trading Opportunities -->
<div style="background: #1a2332; border-radius: 8px; border: 1px solid #2a3441; overflow: hidden; margin-bottom: 20px;">
  <div style="background: #141b26; padding: 12px 16px; border-bottom: 1px solid #2a3441; font-weight: 600; color: #64ffda; font-size: 14px;">
    Cross-Pair Trading Opportunities (Portfolio → Portfolio)
  </div>
  <div style="padding: 16px;">
    <div style="margin-bottom: 12px; color: #8892b0; font-size: 12px;">
      Portfolio Assets: <span id="portfolio-assets">Loading...</span>
    </div>
    
    <table class="data-table">
      <thead>
        <tr>
          <th>Trade Direction</th>
          <th>Symbol</th>
          <th>Action</th>
          <th>Confidence</th>
          <th>Est. Profit</th>
          <th>Price</th>
        </tr>
      </thead>
      <tbody id="cross-pair-opportunities">
        <tr><td colspan="6">Loading cross-pair opportunities...</td></tr>
      </tbody>
    </table>
  </div>
</div>
"""

if __name__ == "__main__":
    print("Bottie Cross-Pair Trading Integration")
    print("=====================================")
    print()
    print("To integrate with your existing Bottie setup:")
    print("1. Add the imports to your api/app.py")
    print("2. Initialize the cross_signal_gen")
    print("3. Add the cross-pair endpoints")
    print("4. Modify your /signals endpoint")
    print("5. Add the HTML section to your dashboard")
    print("6. Add the JavaScript functions")
    print()
    print("This will enable trading between ANY assets in your portfolio,")
    print("not just USDT pairs. For example:")
    print("• BTC → ETH direct swap")
    print("• ETH → BNB atomic exchange") 
    print("• ADA → SOL cross-pair trade")
    print("• Any crypto → Any crypto (if both are in your portfolio)")
    print()
    print("Benefits:")
    print("✅ More trading opportunities")
    print("✅ Better arbitrage detection")
    print("✅ Reduced dependency on USDT")
    print("✅ Portfolio rebalancing automation")
    print("✅ Cross-asset momentum trading")