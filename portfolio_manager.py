#!/usr/bin/env python3
"""
Portfolio Management System - portfolio_manager.py
==================================================

Comprehensive portfolio tracking and management for the modular crypto trading bot.
Configured for LIVE TRADING - handles real portfolio balances and P&L.

Features:
- Real-time live portfolio balance tracking
- P&L calculation with real USD values
- Asset allocation analysis and rebalancing
- Portfolio risk assessment and diversification metrics
- Historical performance tracking
- Multi-currency support with USDT base
- Live trade position monitoring
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics
import math

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    import requests
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AssetPosition:
    """Individual asset position for live trading"""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    allocation_pct: float
    free_balance: float
    locked_balance: float
    last_updated: datetime

@dataclass
class PortfolioSnapshot:
    """Portfolio snapshot at a point in time"""
    timestamp: datetime
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    asset_count: int
    largest_position_pct: float
    risk_score: float
    free_usdt: float

class PortfolioManager:
    """
    Live Trading Portfolio Management System
    
    Tracks real portfolio performance, asset allocation, and provides analytics
    for the live trading bot system.
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None, binance_client: Optional[Client] = None):
        """Initialize portfolio manager for LIVE trading"""
        
        # Initialize Binance client for LIVE trading
        if binance_client:
            self.client = binance_client
        elif api_key and api_secret:
            self.client = Client(api_key, api_secret)
            # LIVE API URL (not testnet)
            self.client.API_URL = 'https://api.binance.com/api'
        else:
            # Try from environment
            api_key = os.getenv('BINANCE_API_KEY')
            api_secret = os.getenv('BINANCE_API_SECRET')
            if api_key and api_secret:
                self.client = Client(api_key, api_secret)
                self.client.API_URL = 'https://api.binance.com/api'
            else:
                self.client = None
        
        self.base_currency = "USDT"
        
        # Portfolio state
        self.positions: Dict[str, AssetPosition] = {}
        self.historical_snapshots: List[PortfolioSnapshot] = []
        self.initial_balance = float(os.getenv("INITIAL_BALANCE", "1000.0"))
        self.last_update = datetime.now()
        
        # Portfolio files
        os.makedirs("logs", exist_ok=True)
        self.portfolio_file = "logs/live_portfolio_state.json"
        self.snapshots_file = "logs/live_portfolio_snapshots.json"
        self.trades_file = "logs/live_trades.json"
        
        # Performance tracking
        self.daily_snapshots = {}
        self.performance_cache = {}
        self.min_balance_usd = float(os.getenv("MIN_BALANCE_USD", "10.0"))
        
        # Load existing data
        self._load_portfolio_state()
        self._load_historical_snapshots()
        
        logger.info("PortfolioManager initialized for LIVE TRADING")
    
    def get_real_portfolio(self) -> Tuple[Dict[str, Any], float]:
        """
        Get real portfolio from live Binance account
        
        Returns:
            Tuple of (portfolio_dict, gbp_exchange_rate)
        """
        try:
            if not self.client:
                logger.error("Binance client not initialized")
                return {}, 1.30
            
            # Get account information
            account_info = self.client.get_account()
            balances = account_info['balances']
            
            # Get GBP exchange rate
            gbp_rate = self._get_gbp_exchange_rate()
            
            portfolio = {}
            
            for balance in balances:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total_balance = free + locked
                
                # Only include assets with meaningful balances
                if total_balance > 0.0000001:
                    # Get USD price for asset
                    price_usd = self._get_asset_price_usd(asset)
                    usd_value = total_balance * price_usd
                    
                    # Only include if USD value meets minimum threshold
                    if usd_value >= self.min_balance_usd or asset == 'USDT':
                        # Get 24h price change
                        change_24h = self._get_24h_change(asset)
                        
                        portfolio[asset] = {
                            'symbol': f"{asset}USDT" if asset != 'USDT' else 'USDT',
                            'balance': total_balance,
                            'free': free,
                            'locked': locked,
                            'price_usd': price_usd,
                            'usd_value': usd_value,
                            'gbp_value': usd_value * gbp_rate,
                            'change_24h': change_24h
                        }
            
            return portfolio, gbp_rate
            
        except Exception as e:
            logger.error(f"Error getting real portfolio: {e}")
            return {}, 1.30
    
    def update_portfolio(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Update complete portfolio from live exchange
        
        Args:
            force_update: Force update even if recently updated
            
        Returns:
            Updated portfolio summary
        """
        try:
            # Check if update needed
            if not force_update:
                time_since_update = datetime.now() - self.last_update
                if time_since_update.total_seconds() < 30:  # 30 second cache
                    return self.get_portfolio_summary()
            
            if not self.client:
                return self._get_demo_portfolio()
            
            # Get live account information
            portfolio, gbp_rate = self.get_real_portfolio()
            
            # Clear existing positions
            self.positions.clear()
            
            # Process all portfolio assets
            total_value_usdt = 0.0
            
            for asset, data in portfolio.items():
                # Calculate position metrics
                current_price = data['price_usd']
                total_quantity = data['balance']
                market_value = data['usd_value']
                
                # Get average cost (requires trade history tracking)
                avg_cost = self._get_avg_cost(asset, current_price)
                unrealized_pnl = (current_price - avg_cost) * total_quantity if avg_cost > 0 else 0
                unrealized_pnl_pct = ((current_price - avg_cost) / avg_cost) * 100 if avg_cost > 0 else 0
                
                # Create position
                position = AssetPosition(
                    symbol=asset,
                    quantity=total_quantity,
                    avg_cost=avg_cost,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_pct=unrealized_pnl_pct,
                    allocation_pct=0.0,  # Will be calculated after total
                    free_balance=data['free'],
                    locked_balance=data['locked'],
                    last_updated=datetime.now()
                )
                
                self.positions[asset] = position
                total_value_usdt += market_value
            
            # Calculate allocation percentages
            for position in self.positions.values():
                position.allocation_pct = (position.market_value / total_value_usdt) * 100 if total_value_usdt > 0 else 0
            
            # Get free USDT balance
            free_usdt = self.positions.get('USDT', AssetPosition('USDT', 0, 1, 1, 0, 0, 0, 0, 0, 0, datetime.now())).free_balance
            
            # Create portfolio snapshot
            snapshot = self._create_portfolio_snapshot(total_value_usdt, free_usdt)
            self.historical_snapshots.append(snapshot)
            
            # Limit snapshot history
            if len(self.historical_snapshots) > 10000:
                self.historical_snapshots = self.historical_snapshots[-5000:]
            
            self.last_update = datetime.now()
            
            # Save state
            self._save_portfolio_state()
            self._save_historical_snapshots()
            
            return self.get_portfolio_summary()
            
        except Exception as e:
            logger.error(f"Error updating live portfolio: {e}")
            return self._get_demo_portfolio()
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive live portfolio summary"""
        try:
            total_value = sum(pos.market_value for pos in self.positions.values())
            total_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            total_pnl_pct = ((total_value - self.initial_balance) / self.initial_balance) * 100 if self.initial_balance > 0 else 0
            
            # Get free USDT for trading
            usdt_position = self.positions.get('USDT')
            free_usdt = usdt_position.free_balance if usdt_position else 0.0
            
            # Asset allocation
            allocation = {pos.symbol: pos.allocation_pct for pos in self.positions.values()}
            sorted_allocation = dict(sorted(allocation.items(), key=lambda x: x[1], reverse=True))
            
            # Top positions
            top_positions = sorted(self.positions.values(), key=lambda x: x.market_value, reverse=True)[:5]
            
            # Risk metrics
            risk_metrics = self._calculate_risk_metrics()
            
            # Trading capacity
            trading_capacity = self._calculate_trading_capacity()
            
            return {
                "total_value": round(total_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_pct": round(total_pnl_pct, 2),
                "free_usdt": round(free_usdt, 2),
                "trading_capacity": trading_capacity,
                "asset_count": len(self.positions),
                "largest_position_pct": max([pos.allocation_pct for pos in self.positions.values()], default=0),
                "base_currency": self.base_currency,
                "last_update": self.last_update.isoformat(),
                "allocation": sorted_allocation,
                "top_positions": [
                    {
                        "symbol": pos.symbol,
                        "value": round(pos.market_value, 2),
                        "pnl_pct": round(pos.unrealized_pnl_pct, 2),
                        "allocation": round(pos.allocation_pct, 2),
                        "free": round(pos.free_balance, 8),
                        "locked": round(pos.locked_balance, 8)
                    } for pos in top_positions
                ],
                "risk_metrics": risk_metrics,
                "daily_change": self._get_daily_change(),
                "performance_metrics": self._get_performance_metrics(),
                "mode": "LIVE_TRADING"
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return self._get_demo_portfolio()
    
    def _get_asset_price_usd(self, asset: str) -> float:
        """Get current USD price for asset"""
        try:
            if asset == 'USDT' or asset == 'USD':
                return 1.0
            
            # Try direct USDT pair first
            symbol = f"{asset}USDT"
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
            
        except:
            try:
                # Try BTC conversion if direct USDT pair fails
                if asset == 'BTC':
                    return float(self.client.get_symbol_ticker(symbol="BTCUSDT")['price'])
                
                # Get asset/BTC price and BTC/USDT price
                btc_pair = f"{asset}BTC"
                btc_price = float(self.client.get_symbol_ticker(symbol=btc_pair)['price'])
                btc_usdt = float(self.client.get_symbol_ticker(symbol="BTCUSDT")['price'])
                return btc_price * btc_usdt
                
            except:
                logger.warning(f"Could not get price for {asset}, using 0")
                return 0.0
    
    def _get_24h_change(self, asset: str) -> float:
        """Get 24h price change percentage"""
        try:
            if asset == 'USDT':
                return 0.0
            
            symbol = f"{asset}USDT"
            ticker = self.client.get_24hr_ticker(symbol=symbol)
            return float(ticker['priceChangePercent'])
            
        except:
            return 0.0
    
    def _get_gbp_exchange_rate(self) -> float:
        """Get USD to GBP exchange rate"""
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
            data = response.json()
            return data['rates']['GBP']
        except:
            return 1.30  # Fallback rate
    
    def _calculate_trading_capacity(self) -> Dict[str, float]:
        """Calculate available trading capacity"""
        usdt_position = self.positions.get('USDT')
        free_usdt = usdt_position.free_balance if usdt_position else 0.0
        
        # Calculate recommended trade sizes based on risk management
        max_trade_1_percent = free_usdt * 0.01  # 1% risk
        max_trade_2_percent = free_usdt * 0.02  # 2% risk
        max_trade_5_percent = free_usdt * 0.05  # 5% risk
        
        return {
            "free_usdt": free_usdt,
            "max_trade_1pct": max_trade_1_percent,
            "max_trade_2pct": max_trade_2_percent,
            "max_trade_5pct": max_trade_5_percent,
            "conservative_size": min(50.0, free_usdt * 0.01),
            "aggressive_size": min(200.0, free_usdt * 0.05)
        }
    
    def get_asset_position(self, symbol: str) -> Optional[AssetPosition]:
        """Get specific asset position"""
        return self.positions.get(symbol)
    
    def get_portfolio_dict(self) -> Dict[str, float]:
        """Get simple portfolio dict for compatibility"""
        return {pos.symbol: pos.quantity for pos in self.positions.values()}
    
    def total_value(self) -> float:
        """Get total portfolio value in base currency"""
        return sum(pos.market_value for pos in self.positions.values())
    
    def get_tradeable_balance(self, asset: str = 'USDT') -> float:
        """Get available balance for trading"""
        position = self.positions.get(asset)
        return position.free_balance if position else 0.0
    
    def record_trade(self, trade_data: Dict[str, Any]) -> None:
        """Record a completed trade for performance tracking"""
        try:
            trade_record = {
                "timestamp": datetime.now().isoformat(),
                "symbol": trade_data.get("symbol"),
                "side": trade_data.get("side"),
                "quantity": trade_data.get("quantity"),
                "price": trade_data.get("price"),
                "value": trade_data.get("value"),
                "fee": trade_data.get("fee", 0),
                "pnl": trade_data.get("pnl", 0),
                "portfolio_value_before": self.total_value()
            }
            
            # Save to trades file
            self._save_trade_record(trade_record)
            
            # Update cost basis tracking
            self._update_cost_basis(trade_data)
            
        except Exception as e:
            logger.error(f"Error recording trade: {e}")
    
    def _create_portfolio_snapshot(self, total_value: float, free_usdt: float) -> PortfolioSnapshot:
        """Create portfolio snapshot"""
        total_pnl = total_value - self.initial_balance
        total_pnl_pct = (total_pnl / self.initial_balance) * 100 if self.initial_balance > 0 else 0
        asset_count = len(self.positions)
        largest_position_pct = max([pos.allocation_pct for pos in self.positions.values()], default=0)
        
        # Simple risk score based on concentration and volatility
        risk_score = min(100, largest_position_pct + (asset_count * 5))
        
        return PortfolioSnapshot(
            timestamp=datetime.now(),
            total_value=total_value,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            asset_count=asset_count,
            largest_position_pct=largest_position_pct,
            risk_score=risk_score,
            free_usdt=free_usdt
        )
    
    def _calculate_risk_metrics(self) -> Dict[str, float]:
        """Calculate portfolio risk metrics"""
        try:
            allocations = [pos.allocation_pct for pos in self.positions.values()]
            
            # Concentration risk (largest position)
            concentration_risk = max(allocations, default=0)
            
            # Diversification score (inverse of concentration)
            diversification_score = 100 - concentration_risk
            
            # Volatility estimate based on 24h changes
            volatilities = []
            for pos in self.positions.values():
                if pos.symbol != 'USDT':
                    change_24h = self._get_24h_change(pos.symbol)
                    volatilities.append(abs(change_24h))
            
            avg_volatility = statistics.mean(volatilities) if volatilities else 0
            
            return {
                "concentration_risk": round(concentration_risk, 2),
                "diversification_score": round(diversification_score, 2),
                "avg_volatility_24h": round(avg_volatility, 2),
                "total_assets": len(self.positions),
                "risk_score": round(min(100, concentration_risk + avg_volatility), 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {"error": str(e)}
    
    def _get_daily_change(self) -> Dict[str, float]:
        """Get daily portfolio change"""
        try:
            if len(self.historical_snapshots) < 2:
                return {"daily_change_usd": 0, "daily_change_pct": 0}
            
            # Get snapshots from 24 hours ago
            current = self.historical_snapshots[-1]
            yesterday_time = current.timestamp - timedelta(days=1)
            
            # Find closest snapshot to 24h ago
            yesterday_snapshot = None
            for snapshot in reversed(self.historical_snapshots):
                if snapshot.timestamp <= yesterday_time:
                    yesterday_snapshot = snapshot
                    break
            
            if not yesterday_snapshot:
                yesterday_snapshot = self.historical_snapshots[0]
            
            daily_change_usd = current.total_value - yesterday_snapshot.total_value
            daily_change_pct = (daily_change_usd / yesterday_snapshot.total_value) * 100 if yesterday_snapshot.total_value > 0 else 0
            
            return {
                "daily_change_usd": round(daily_change_usd, 2),
                "daily_change_pct": round(daily_change_pct, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating daily change: {e}")
            return {"daily_change_usd": 0, "daily_change_pct": 0}
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        try:
            if len(self.historical_snapshots) < 2:
                return {"insufficient_data": True}
            
            # Calculate various performance metrics
            values = [s.total_value for s in self.historical_snapshots]
            returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
            
            total_return = (values[-1] - values[0]) / values[0] if values[0] > 0 else 0
            avg_return = statistics.mean(returns) if returns else 0
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0
            
            # Sharpe ratio (assuming 0% risk-free rate)
            sharpe_ratio = avg_return / volatility if volatility > 0 else 0
            
            # Max drawdown
            max_drawdown = 0
            peak = values[0]
            for value in values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return {
                "total_return_pct": round(total_return * 100, 2),
                "avg_daily_return_pct": round(avg_return * 100, 4),
                "volatility_pct": round(volatility * 100, 2),
                "sharpe_ratio": round(sharpe_ratio, 3),
                "max_drawdown_pct": round(max_drawdown * 100, 2),
                "total_snapshots": len(self.historical_snapshots)
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {"error": str(e)}
    
    def _get_avg_cost(self, asset: str, current_price: float) -> float:
        """Get average cost basis for asset (simplified)"""
        try:
            # Load from cost basis file if exists
            cost_file = f"logs/cost_basis_{asset}.json"
            if os.path.exists(cost_file):
                with open(cost_file, 'r') as f:
                    cost_data = json.load(f)
                    return cost_data.get('avg_cost', current_price)
            else:
                return current_price  # Use current price as initial cost
        except:
            return current_price
    
    def _update_cost_basis(self, trade_data: Dict[str, Any]) -> None:
        """Update cost basis tracking after trade"""
        try:
            asset = trade_data.get("symbol", "").replace("USDT", "")
            if not asset:
                return
            
            cost_file = f"logs/cost_basis_{asset}.json"
            
            # Load existing cost basis
            if os.path.exists(cost_file):
                with open(cost_file, 'r') as f:
                    cost_data = json.load(f)
            else:
                cost_data = {"avg_cost": 0, "total_quantity": 0, "total_cost": 0}
            
            # Update based on trade
            price = float(trade_data.get("price", 0))
            quantity = float(trade_data.get("quantity", 0))
            side = trade_data.get("side", "")
            
            if side.upper() == "BUY":
                # Add to position
                new_total_cost = cost_data["total_cost"] + (price * quantity)
                new_total_quantity = cost_data["total_quantity"] + quantity
                new_avg_cost = new_total_cost / new_total_quantity if new_total_quantity > 0 else price
                
                cost_data.update({
                    "avg_cost": new_avg_cost,
                    "total_quantity": new_total_quantity,
                    "total_cost": new_total_cost,
                    "last_updated": datetime.now().isoformat()
                })
            
            # Save updated cost basis
            with open(cost_file, 'w') as f:
                json.dump(cost_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating cost basis: {e}")
    
    def _save_trade_record(self, trade_record: Dict[str, Any]) -> None:
        """Save trade record to file"""
        try:
            trades = []
            if os.path.exists(self.trades_file):
                with open(self.trades_file, 'r') as f:
                    trades = json.load(f)
            
            trades.append(trade_record)
            
            # Keep only last 1000 trades
            if len(trades) > 1000:
                trades = trades[-1000:]
            
            with open(self.trades_file, 'w') as f:
                json.dump(trades, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving trade record: {e}")
    
    def _save_portfolio_state(self) -> None:
        """Save current portfolio state"""
        try:
            state = {
                "last_update": self.last_update.isoformat(),
                "positions": {
                    symbol: asdict(position) for symbol, position in self.positions.items()
                }
            }
            
            # Convert datetime objects to strings
            for pos_data in state["positions"].values():
                pos_data["last_updated"] = pos_data["last_updated"].isoformat() if isinstance(pos_data["last_updated"], datetime) else pos_data["last_updated"]
            
            with open(self.portfolio_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving portfolio state: {e}")
    
    def _load_portfolio_state(self) -> None:
        """Load portfolio state from file"""
        try:
            if os.path.exists(self.portfolio_file):
                with open(self.portfolio_file, 'r') as f:
                    state = json.load(f)
                    
                self.last_update = datetime.fromisoformat(state.get("last_update", datetime.now().isoformat()))
                
                # Load positions
                for symbol, pos_data in state.get("positions", {}).items():
                    pos_data["last_updated"] = datetime.fromisoformat(pos_data["last_updated"])
                    self.positions[symbol] = AssetPosition(**pos_data)
                    
        except Exception as e:
            logger.error(f"Error loading portfolio state: {e}")
    
    def _save_historical_snapshots(self) -> None:
        """Save historical snapshots"""
        try:
            snapshots_data = [asdict(snapshot) for snapshot in self.historical_snapshots]
            
            # Convert datetime objects to strings
            for snapshot in snapshots_data:
                snapshot["timestamp"] = snapshot["timestamp"].isoformat() if isinstance(snapshot["timestamp"], datetime) else snapshot["timestamp"]
            
            with open(self.snapshots_file, 'w') as f:
                json.dump(snapshots_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving snapshots: {e}")
    
    def _load_historical_snapshots(self) -> None:
        """Load historical snapshots from file"""
        try:
            if os.path.exists(self.snapshots_file):
                with open(self.snapshots_file, 'r') as f:
                    snapshots_data = json.load(f)
                    
                self.historical_snapshots = []
                for snapshot_data in snapshots_data:
                    snapshot_data["timestamp"] = datetime.fromisoformat(snapshot_data["timestamp"])
                    self.historical_snapshots.append(PortfolioSnapshot(**snapshot_data))
                    
        except Exception as e:
            logger.error(f"Error loading snapshots: {e}")
    
    def get_connection_status(self) -> str:
        """Get Binance API connection status"""
        try:
            if not self.client:
                return "❌ Not Connected - Missing API credentials"
            
            # Test connection with a simple API call
            account_info = self.client.get_account()
            if account_info:
                # Check if we're on live or testnet
                if 'testnet' in self.client.API_URL.lower():
                    return "🧪 Connected to Binance Testnet"
                else:
                    return "🚀 Connected to Binance Live Trading"
            else:
                return "❌ Connection Failed"
                
        except BinanceAPIException as e:
            if e.code == -2015:
                return "❌ Invalid API Key or Secret"
            elif e.code == -1021:
                return "❌ Timestamp Error - Check system clock"
            else:
                return f"❌ API Error: {e.message}"
        except Exception as e:
            return f"❌ Connection Error: {str(e)}"
    
    def get_api_permissions(self) -> Dict[str, bool]:
        """Check API key permissions"""
        try:
            if not self.client:
                return {"spot": False, "futures": False, "margin": False}
            
            account_info = self.client.get_account()
            permissions = account_info.get('permissions', [])
            
            return {
                "spot": "SPOT" in permissions,
                "futures": "FUTURES" in permissions,
                "margin": "MARGIN" in permissions,
                "can_trade": account_info.get('canTrade', False),
                "can_withdraw": account_info.get('canWithdraw', False),
                "can_deposit": account_info.get('canDeposit', False)
            }
            
        except Exception as e:
            logger.error(f"Error checking API permissions: {e}")
            return {"error": str(e)}
    
    def test_connection(self) -> Dict[str, Any]:
        """Comprehensive connection test"""
        try:
            if not self.client:
                return {
                    "connected": False,
                    "error": "No Binance client initialized",
                    "status": "❌ Not Connected"
                }
            
            # Test server time
            server_time = self.client.get_server_time()
            
            # Test account access
            account_info = self.client.get_account()
            
            # Get permissions
            permissions = self.get_api_permissions()
            
            # Determine trading mode
            is_testnet = 'testnet' in self.client.API_URL.lower()
            
            return {
                "connected": True,
                "server_time": server_time,
                "account_type": account_info.get('accountType', 'UNKNOWN'),
                "can_trade": account_info.get('canTrade', False),
                "permissions": permissions,
                "is_testnet": is_testnet,
                "mode": "Testnet" if is_testnet else "Live Trading",
                "status": "🧪 Testnet Connected" if is_testnet else "🚀 Live Trading Connected",
                "api_url": self.client.API_URL
            }
            
        except BinanceAPIException as e:
            return {
                "connected": False,
                "error": f"Binance API Error: {e.message}",
                "error_code": e.code,
                "status": f"❌ API Error ({e.code})"
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "status": "❌ Connection Failed"
            }
    
    def last_updated(self) -> str:
        """Get formatted last update time"""
        try:
            if hasattr(self, 'last_update') and self.last_update:
                # Format the datetime for display
                return self.last_update.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return "Never"
        except Exception as e:
            logger.error(f"Error formatting last update time: {e}")
            return "Unknown"
    
    def get_last_update_time(self) -> datetime:
        """Get last update time as datetime object"""
        return self.last_update if hasattr(self, 'last_update') else datetime.now()
    
    def time_since_last_update(self) -> str:
        """Get human-readable time since last update"""
        try:
            if not hasattr(self, 'last_update') or not self.last_update:
                return "Never updated"
            
            time_diff = datetime.now() - self.last_update
            
            if time_diff.days > 0:
                return f"{time_diff.days} days ago"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                return f"{hours} hours ago"
            elif time_diff.seconds > 60:
                minutes = time_diff.seconds // 60
                return f"{minutes} minutes ago"
            else:
                return f"{time_diff.seconds} seconds ago"
                
        except Exception as e:
            logger.error(f"Error calculating time since update: {e}")
            return "Unknown"
    
    def _get_demo_portfolio(self) -> Dict[str, Any]:
        """Get demo portfolio data when client unavailable"""
        return {
            "total_value": 1000.0,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "free_usdt": 500.0,
            "asset_count": 0,
            "largest_position_pct": 0,
            "base_currency": "USDT",
            "last_update": datetime.now().isoformat(),
            "allocation": {},
            "top_positions": [],
            "risk_metrics": {"error": "Demo mode"},
            "daily_change": {"daily_change_usd": 0, "daily_change_pct": 0},
            "performance_metrics": {"insufficient_data": True},
            "mode": "DEMO",
            "error": "Binance client not available"
        }

# Utility functions for compatibility
def get_portfolio_manager(api_key: str = None, api_secret: str = None) -> PortfolioManager:
    """Factory function to create portfolio manager"""
    return PortfolioManager(api_key, api_secret)

def get_real_portfolio() -> Tuple[Dict[str, Any], float]:
    """Quick function to get real portfolio"""
    manager = PortfolioManager()
    return manager.get_real_portfolio()

if __name__ == "__main__":
    # Test the portfolio manager
    manager = PortfolioManager()
    summary = manager.update_portfolio(force_update=True)
    print("Portfolio Summary:")
    print(json.dumps(summary, indent=2))