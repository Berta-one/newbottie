#!/usr/bin/env python3
"""
portfolio_cross_trading.py
Core cross-pair trading engine for direct asset-to-asset trading
"""

import os
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import ccxt
except ImportError:
    raise RuntimeError("ccxt required: pip install ccxt")

@dataclass
class CrossPairOpportunity:
    """Represents a cross-pair trading opportunity"""
    symbol: str
    from_asset: str
    to_asset: str
    direction: str  # 'buy' or 'sell'
    current_price: float
    signal_strength: float
    estimated_profit_pct: float
    volume_24h: float
    timestamp: float

class PortfolioCrossPairEngine:
    """Engine for discovering and executing cross-pair trades"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.testnet = testnet
        
        self.exchange = None
        self.portfolio_assets = set()
        self.available_pairs = {}
        self.cross_opportunities = []
        
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize the exchange and discover portfolio"""
        try:
            # Initialize exchange
            if self.testnet:
                self.exchange = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'sandbox': True,
                    'enableRateLimit': True,
                })
            else:
                self.exchange = ccxt.binance({
                    'apiKey': self.api_key,
                    'secret': self.api_secret,
                    'enableRateLimit': True,
                })
            
            # Discover portfolio assets
            await self.discover_portfolio()
            
            # Find available cross-pairs
            await self.discover_cross_pairs()
            
            self.logger.info(f"Initialized cross-pair engine with {len(self.portfolio_assets)} assets and {len(self.available_pairs)} pairs")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cross-pair engine: {e}")
            raise
    
    async def discover_portfolio(self):
        """Discover all assets in the portfolio with non-zero balance"""
        try:
            balance = await self.exchange.fetch_balance()
            
            self.portfolio_assets = set()
            for asset, amount in balance['total'].items():
                if amount > 0:
                    self.portfolio_assets.add(asset)
            
            self.logger.info(f"Discovered {len(self.portfolio_assets)} portfolio assets: {list(self.portfolio_assets)}")
            
        except Exception as e:
            self.logger.error(f"Failed to discover portfolio: {e}")
            # Fallback to common assets for demo
            self.portfolio_assets = {'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'USDT'}
    
    async def discover_cross_pairs(self):
        """Discover all possible cross-pair combinations from portfolio"""
        try:
            markets = await self.exchange.load_markets()
            
            self.available_pairs = {}
            
            # Find all possible cross-pairs between portfolio assets
            for asset1 in self.portfolio_assets:
                for asset2 in self.portfolio_assets:
                    if asset1 != asset2:
                        # Check if direct pair exists
                        symbol1 = f"{asset1}/{asset2}"
                        symbol2 = f"{asset2}/{asset1}"
                        
                        if symbol1 in markets:
                            self.available_pairs[symbol1] = {
                                'from_asset': asset1,
                                'to_asset': asset2,
                                'symbol': symbol1,
                                'market': markets[symbol1]
                            }
                        elif symbol2 in markets:
                            self.available_pairs[symbol2] = {
                                'from_asset': asset2,
                                'to_asset': asset1,
                                'symbol': symbol2,
                                'market': markets[symbol2]
                            }
            
            self.logger.info(f"Found {len(self.available_pairs)} available cross-pairs")
            
        except Exception as e:
            self.logger.error(f"Failed to discover cross-pairs: {e}")
            self.available_pairs = {}
    
    async def scan_cross_opportunities(self) -> List[CrossPairOpportunity]:
        """Scan for cross-pair trading opportunities"""
        opportunities = []
        
        try:
            if not self.available_pairs:
                await self.discover_cross_pairs()
            
            # Get tickers for all available pairs
            symbols = list(self.available_pairs.keys())
            if not symbols:
                return opportunities
            
            tickers = await self.exchange.fetch_tickers(symbols)
            
            for symbol, pair_info in self.available_pairs.items():
                if symbol not in tickers:
                    continue
                
                ticker = tickers[symbol]
                
                # Calculate basic signals
                price = ticker['last']
                volume_24h = ticker['quoteVolume'] or 0
                
                # Simple momentum signal (can be enhanced with ML)
                signal_strength = self._calculate_signal_strength(ticker)
                
                # Estimate profit potential
                profit_pct = self._estimate_profit_potential(ticker)
                
                # Determine direction
                direction = 'buy' if signal_strength > 0.5 else 'sell'
                
                opportunity = CrossPairOpportunity(
                    symbol=symbol,
                    from_asset=pair_info['from_asset'],
                    to_asset=pair_info['to_asset'],
                    direction=direction,
                    current_price=price,
                    signal_strength=signal_strength,
                    estimated_profit_pct=profit_pct,
                    volume_24h=volume_24h,
                    timestamp=time.time()
                )
                
                opportunities.append(opportunity)
            
            # Sort by signal strength and profit potential
            opportunities.sort(key=lambda x: x.signal_strength * x.estimated_profit_pct, reverse=True)
            
            self.cross_opportunities = opportunities
            self.logger.info(f"Found {len(opportunities)} cross-pair opportunities")
            
        except Exception as e:
            self.logger.error(f"Failed to scan cross-pair opportunities: {e}")
        
        return opportunities
    
    def _calculate_signal_strength(self, ticker: Dict[str, Any]) -> float:
        """Calculate signal strength from ticker data"""
        try:
            # Simple momentum-based signal
            if not ticker.get('percentage'):
                return 0.5
            
            change_pct = ticker['percentage'] / 100.0
            
            # Normalize to 0-1 range
            # Strong positive momentum = high signal
            signal = 0.5 + (change_pct * 2)  # Amplify signal
            signal = max(0.0, min(1.0, signal))  # Clamp to 0-1
            
            return signal
            
        except Exception:
            return 0.5
    
    def _estimate_profit_potential(self, ticker: Dict[str, Any]) -> float:
        """Estimate profit potential from ticker data"""
        try:
            # Simple spread-based profit estimation
            bid = ticker.get('bid', 0)
            ask = ticker.get('ask', 0)
            
            if bid > 0 and ask > 0:
                spread_pct = (ask - bid) / bid
                # Invert spread as profit opportunity (tighter spread = better)
                return max(0.001, 0.01 - spread_pct)  # Min 0.1% profit
            
            # Fallback to volume-based estimation
            volume = ticker.get('quoteVolume', 0)
            if volume > 1000000:  # High volume
                return 0.005  # 0.5% potential
            elif volume > 100000:  # Medium volume
                return 0.003  # 0.3% potential
            else:
                return 0.001  # 0.1% potential
            
        except Exception:
            return 0.001
    
    async def execute_cross_trade(self, opportunity: CrossPairOpportunity, amount: float) -> Dict[str, Any]:
        """Execute a cross-pair trade"""
        try:
            # Validate trade parameters
            min_trade_value = float(os.getenv("CROSS_PAIR_MIN_TRADE_VALUE_USDT", "10"))
            
            if amount * opportunity.current_price < min_trade_value:
                return {
                    "success": False,
                    "error": f"Trade value too small. Minimum: ${min_trade_value}"
                }
            
            # Check balance
            balance = await self.exchange.fetch_balance()
            available_balance = balance['free'].get(opportunity.from_asset, 0)
            
            if amount > available_balance:
                return {
                    "success": False,
                    "error": f"Insufficient balance. Available: {available_balance} {opportunity.from_asset}"
                }
            
            # Execute trade
            if opportunity.direction == 'buy':
                order = await self.exchange.create_market_buy_order(
                    opportunity.symbol, 
                    amount
                )
            else:
                order = await self.exchange.create_market_sell_order(
                    opportunity.symbol, 
                    amount
                )
            
            self.logger.info(f"Executed cross-pair trade: {order['id']}")
            
            return {
                "success": True,
                "order_id": order['id'],
                "symbol": opportunity.symbol,
                "side": opportunity.direction,
                "amount": amount,
                "price": order.get('price'),
                "cost": order.get('cost'),
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute cross-pair trade: {e}")
            return {
                "success": False,
                "error": str(e)
            }

async def main():
    """Test the cross-pair engine"""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize engine
    engine = PortfolioCrossPairEngine(testnet=True)
    await engine.initialize()
    
    # Scan for opportunities
    opportunities = await engine.scan_cross_opportunities()
    
    print(f"\n🔄 Found {len(opportunities)} cross-pair opportunities:")
    print("-" * 60)
    
    for i, opp in enumerate(opportunities[:10], 1):  # Top 10
        print(f"{i:2d}. {opp.from_asset} → {opp.to_asset}")
        print(f"    Symbol: {opp.symbol}")
        print(f"    Direction: {opp.direction}")
        print(f"    Price: {opp.current_price:.8f}")
        print(f"    Signal: {opp.signal_strength:.1%}")
        print(f"    Profit: {opp.estimated_profit_pct:.2%}")
        print(f"    Volume: ${opp.volume_24h:,.0f}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
