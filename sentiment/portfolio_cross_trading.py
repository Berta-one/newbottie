# portfolio_cross_trading.py
"""
Enhanced Bottie engine that scans ALL possible trading pairs between portfolio assets,
not just USDT pairs. Finds atomic swaps and cross-trading opportunities.
"""

import ccxt
import asyncio
import itertools
import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import time
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CrossPairTrader")

@dataclass
class TradingPair:
    symbol: str
    base: str
    quote: str
    min_notional: float
    min_qty: float
    qty_step: float
    price_step: float
    is_active: bool
    fee_rate: float = 0.001

@dataclass
class CrossPairOpportunity:
    from_asset: str
    to_asset: str
    symbol: str
    direction: str  # 'buy' or 'sell'
    signal_strength: float
    current_price: float
    estimated_profit_pct: float
    min_order_size: float
    available_balance: float

class PortfolioCrossPairEngine:
    """
    Advanced trading engine that:
    1. Scans your entire portfolio 
    2. Finds ALL possible trading pairs on Binance
    3. Generates signals for cross-asset trading
    4. Executes atomic swaps between cryptos
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': testnet,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        self.portfolio_assets: Set[str] = set()
        self.available_pairs: Dict[str, TradingPair] = {}
        self.cross_opportunities: List[CrossPairOpportunity] = []
        self.balances: Dict[str, float] = {}
        self.last_scan_time = 0
        
        # Trading parameters
        self.min_trade_value_usdt = 10.0  # Minimum trade size
        self.max_portfolio_pct_per_trade = 0.05  # Max 5% of asset per trade
        self.min_profit_threshold = 0.002  # 0.2% minimum expected profit
        
    async def initialize(self):
        """Initialize exchange connection and load markets"""
        try:
            await self.exchange.load_markets()
            logger.info(f"Loaded {len(self.exchange.markets)} markets from Binance")
            await self.update_portfolio()
            await self.discover_trading_pairs()
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    async def update_portfolio(self):
        """Scan current portfolio and balances"""
        try:
            balance = await self.exchange.fetch_balance()
            self.balances = {}
            self.portfolio_assets = set()
            
            for asset, amounts in balance.items():
                if asset in ['info', 'free', 'used', 'total']:
                    continue
                    
                total = amounts.get('total', 0)
                free = amounts.get('free', 0)
                
                if total > 0:
                    self.balances[asset] = {
                        'total': total,
                        'free': free,
                        'used': amounts.get('used', 0)
                    }
                    self.portfolio_assets.add(asset)
            
            logger.info(f"Portfolio contains {len(self.portfolio_assets)} assets: {sorted(self.portfolio_assets)}")
            
            # Include major stablecoins even if balance is 0 (for receiving trades)
            stablecoins = {'USDT', 'BUSD', 'USDC', 'DAI'}
            self.portfolio_assets.update(stablecoins)
            
        except Exception as e:
            logger.error(f"Portfolio update failed: {e}")

    async def discover_trading_pairs(self):
        """Find all possible trading pairs between portfolio assets"""
        if len(self.portfolio_assets) < 2:
            logger.warning("Need at least 2 assets in portfolio for cross-pair trading")
            return
        
        self.available_pairs = {}
        portfolio_list = list(self.portfolio_assets)
        
        # Generate all possible combinations of portfolio assets
        for asset1, asset2 in itertools.permutations(portfolio_list, 2):
            # Try both directions: asset1/asset2 and asset2/asset1
            for base, quote in [(asset1, asset2), (asset2, asset1)]:
                symbol = f"{base}/{quote}"
                
                if symbol in self.exchange.markets:
                    market = self.exchange.markets[symbol]
                    
                    if market.get('active', True) and market.get('spot', True):
                        pair = self._create_trading_pair(symbol, market)
                        if pair:
                            self.available_pairs[symbol] = pair
        
        logger.info(f"Found {len(self.available_pairs)} tradeable cross-pairs:")
        for symbol in sorted(self.available_pairs.keys()):
            logger.info(f"  {symbol}")

    def _create_trading_pair(self, symbol: str, market: dict) -> Optional[TradingPair]:
        """Create TradingPair from market info"""
        try:
            # Extract market filters
            min_notional = 10.0  # Default
            min_qty = 0.000001
            qty_step = 0.000001
            price_step = 0.000001
            
            # Parse Binance market filters
            info = market.get('info', {})
            filters = info.get('filters', [])
            
            for filter_item in filters:
                filter_type = filter_item.get('filterType')
                
                if filter_type == 'MIN_NOTIONAL':
                    min_notional = float(filter_item.get('minNotional', min_notional))
                elif filter_type == 'LOT_SIZE':
                    min_qty = float(filter_item.get('minQty', min_qty))
                    qty_step = float(filter_item.get('stepSize', qty_step))
                elif filter_type == 'PRICE_FILTER':
                    price_step = float(filter_item.get('tickSize', price_step))
            
            return TradingPair(
                symbol=symbol,
                base=market['base'],
                quote=market['quote'],
                min_notional=min_notional,
                min_qty=min_qty,
                qty_step=qty_step,
                price_step=price_step,
                is_active=market.get('active', True)
            )
            
        except Exception as e:
            logger.warning(f"Could not create trading pair for {symbol}: {e}")
            return None

    async def scan_cross_opportunities(self):
        """Scan for profitable cross-trading opportunities"""
        if not self.available_pairs:
            await self.discover_trading_pairs()
        
        self.cross_opportunities = []
        current_time = time.time()
        
        # Fetch all tickers at once for efficiency
        try:
            tickers = await self.exchange.fetch_tickers(list(self.available_pairs.keys()))
        except Exception as e:
            logger.error(f"Failed to fetch tickers: {e}")
            return
        
        for symbol, pair in self.available_pairs.items():
            if symbol not in tickers:
                continue
                
            ticker = tickers[symbol]
            opportunity = await self._analyze_pair_opportunity(pair, ticker)
            
            if opportunity and opportunity.signal_strength > 0.5:
                self.cross_opportunities.append(opportunity)
        
        # Sort by signal strength
        self.cross_opportunities.sort(key=lambda x: x.signal_strength, reverse=True)
        
        logger.info(f"Found {len(self.cross_opportunities)} cross-trading opportunities")
        
        # Log top opportunities
        for opp in self.cross_opportunities[:5]:
            logger.info(f"  {opp.from_asset} → {opp.to_asset} via {opp.symbol} "
                       f"(strength: {opp.signal_strength:.3f}, profit est: {opp.estimated_profit_pct:.2%})")

    async def _analyze_pair_opportunity(self, pair: TradingPair, ticker: dict) -> Optional[CrossPairOpportunity]:
        """Analyze a single trading pair for opportunities"""
        try:
            # Get current price and basic metrics
            current_price = ticker.get('last') or ticker.get('close')
            if not current_price:
                return None
            
            bid = ticker.get('bid', current_price)
            ask = ticker.get('ask', current_price)
            spread = (ask - bid) / current_price if current_price > 0 else 0.1
            volume_24h = ticker.get('quoteVolume', 0)
            
            # Calculate which asset we're trading FROM and TO
            base_balance = self.balances.get(pair.base, {}).get('free', 0)
            quote_balance = self.balances.get(pair.quote, {}).get('free', 0)
            
            opportunities = []
            
            # Opportunity 1: Sell base for quote (if we have base)
            if base_balance > pair.min_qty:
                signal_strength = self._calculate_signal_strength(pair.symbol, 'sell')
                profit_est = signal_strength * 0.01 - spread - pair.fee_rate  # Rough estimate
                
                if profit_est > self.min_profit_threshold:
                    opportunities.append(CrossPairOpportunity(
                        from_asset=pair.base,
                        to_asset=pair.quote,
                        symbol=pair.symbol,
                        direction='sell',
                        signal_strength=signal_strength,
                        current_price=current_price,
                        estimated_profit_pct=profit_est,
                        min_order_size=pair.min_qty,
                        available_balance=base_balance
                    ))
            
            # Opportunity 2: Buy base with quote (if we have quote)
            if quote_balance > pair.min_notional:
                signal_strength = self._calculate_signal_strength(pair.symbol, 'buy')
                profit_est = signal_strength * 0.01 - spread - pair.fee_rate
                
                if profit_est > self.min_profit_threshold:
                    opportunities.append(CrossPairOpportunity(
                        from_asset=pair.quote,
                        to_asset=pair.base,
                        symbol=pair.symbol,
                        direction='buy',
                        signal_strength=signal_strength,
                        current_price=current_price,
                        estimated_profit_pct=profit_est,
                        min_order_size=pair.min_notional / current_price,
                        available_balance=quote_balance
                    ))
            
            # Return the best opportunity for this pair
            if opportunities:
                return max(opportunities, key=lambda x: x.signal_strength)
            
        except Exception as e:
            logger.warning(f"Analysis failed for {pair.symbol}: {e}")
        
        return None

    def _calculate_signal_strength(self, symbol: str, direction: str) -> float:
        """
        Calculate trading signal strength for a symbol
        This is where you integrate your ML/Quantum/EMA signals
        """
        try:
            # Placeholder for advanced signal calculation
            # In real implementation, integrate with your existing signal generation:
            # - EMA crossover signals
            # - ML model predictions  
            # - Quantum circuit outputs
            # - Sentiment analysis
            # - Technical indicators
            
            # Mock signal for demonstration
            base_signal = 0.6  # Base confidence
            
            # Add some randomness to simulate real signals
            import random
            momentum_factor = random.uniform(0.8, 1.2)
            volatility_factor = random.uniform(0.9, 1.1)
            
            signal = base_signal * momentum_factor * volatility_factor
            
            # Clamp to [0, 1]
            return max(0.0, min(1.0, signal))
            
        except Exception as e:
            logger.warning(f"Signal calculation failed for {symbol}: {e}")
            return 0.0

    async def execute_cross_trade(self, opportunity: CrossPairOpportunity, dry_run: bool = True):
        """Execute a cross-pair trade"""
        try:
            # Calculate order size
            max_trade_value = self.balances.get(opportunity.from_asset, {}).get('free', 0)
            max_trade_value *= self.max_portfolio_pct_per_trade
            
            if opportunity.direction == 'buy':
                # Buying base with quote
                quote_amount = min(max_trade_value, opportunity.available_balance * 0.95)  # 95% to account for fees
                quantity = quote_amount / opportunity.current_price
            else:
                # Selling base for quote
                quantity = min(max_trade_value, opportunity.available_balance * 0.95)
            
            # Ensure minimum order size
            if quantity < opportunity.min_order_size:
                logger.warning(f"Order size {quantity} below minimum {opportunity.min_order_size}")
                return None
            
            # Round to exchange precision
            pair = self.available_pairs[opportunity.symbol]
            quantity = self._round_to_step(quantity, pair.qty_step)
            
            if dry_run:
                logger.info(f"DRY RUN: {opportunity.direction.upper()} {quantity} {opportunity.symbol} "
                           f"at ~{opportunity.current_price} "
                           f"({opportunity.from_asset} → {opportunity.to_asset})")
                return {'dry_run': True, 'quantity': quantity}
            
            # Execute real order
            order = await self.exchange.create_market_order(
                symbol=opportunity.symbol,
                side=opportunity.direction,
                amount=quantity
            )
            
            logger.info(f"EXECUTED: {opportunity.direction.upper()} {quantity} {opportunity.symbol} "
                       f"({opportunity.from_asset} → {opportunity.to_asset}) - Order ID: {order.get('id')}")
            
            return order
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return None

    def _round_to_step(self, value: float, step: float) -> float:
        """Round value to exchange step size"""
        if step == 0:
            return value
        return round(value / step) * step

    async def run_cross_trading_loop(self, interval_seconds: int = 30):
        """Main trading loop"""
        logger.info("Starting cross-pair trading loop...")
        
        while True:
            try:
                # Update portfolio and discover new pairs
                await self.update_portfolio()
                
                # Scan for opportunities
                await self.scan_cross_opportunities()
                
                # Execute top opportunities (with safety limits)
                executed_count = 0
                max_trades_per_cycle = 3
                
                for opportunity in self.cross_opportunities[:max_trades_per_cycle]:
                    if opportunity.signal_strength > 0.7:  # High confidence only
                        result = await self.execute_cross_trade(opportunity, dry_run=True)  # Set to False for live trading
                        if result:
                            executed_count += 1
                
                logger.info(f"Cycle complete. Executed {executed_count} trades.")
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Trading loop stopped by user")
                break
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(interval_seconds)

    def get_portfolio_summary(self) -> dict:
        """Get current portfolio summary"""
        summary = {
            'total_assets': len(self.portfolio_assets),
            'tradeable_pairs': len(self.available_pairs),
            'current_opportunities': len(self.cross_opportunities),
            'assets': list(self.portfolio_assets),
            'balances': self.balances
        }
        return summary

# Example usage and configuration
async def main():
    """Example usage"""
    
    # Configuration
    API_KEY = "your_binance_api_key"
    API_SECRET = "your_binance_secret"
    TESTNET = True  # Set to False for live trading
    
    # Initialize engine
    engine = PortfolioCrossPairEngine(API_KEY, API_SECRET, TESTNET)
    
    try:
        # Initialize
        await engine.initialize()
        
        # Show portfolio summary
        summary = engine.get_portfolio_summary()
        print(f"Portfolio Summary: {json.dumps(summary, indent=2)}")
        
        # Run one scan manually
        await engine.scan_cross_opportunities()
        
        # Show opportunities
        print(f"\nTop Cross-Trading Opportunities:")
        for i, opp in enumerate(engine.cross_opportunities[:10], 1):
            print(f"{i:2d}. {opp.from_asset:>6} → {opp.to_asset:<6} via {opp.symbol:12} "
                  f"(strength: {opp.signal_strength:.3f}, est profit: {opp.estimated_profit_pct:+.2%})")
        
        # Start continuous trading (uncomment to run)
        # await engine.run_cross_trading_loop(interval_seconds=60)
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
    finally:
        await engine.exchange.close()

if __name__ == "__main__":
    asyncio.run(main())