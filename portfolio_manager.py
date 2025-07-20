#!/usr/bin/env python3
"""
Portfolio Management System - portfolio_manager.py
==================================================

Comprehensive portfolio tracking and management for the modular crypto trading bot.
Handles real-time balance tracking, asset allocation, performance analytics, and portfolio optimization.

Features:
- Real-time portfolio balance and asset tracking
- P&L calculation and performance metrics
- Asset allocation analysis and rebalancing
- Portfolio risk assessment and diversification metrics
- Historical performance tracking
- Multi-currency support with USDT base
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AssetPosition:
    """Individual asset position"""
    symbol: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    allocation_pct: float
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

class PortfolioManager:
    """
    Comprehensive Portfolio Management System
    
    Tracks portfolio performance, asset allocation, and provides analytics
    for the trading bot system.
    """
    
    def __init__(self, binance_client: Optional[Client] = None):
        """Initialize portfolio manager"""
        self.client = binance_client
        self.base_currency = "USDT"
        
        # Portfolio state
        self.positions: Dict[str, AssetPosition] = {}
        self.historical_snapshots: List[PortfolioSnapshot] = []
        self.initial_balance = float(os.getenv("INITIAL_BALANCE", "10000.0"))
        self.last_update = datetime.now()
        
        # Portfolio files
        self.portfolio_file = "logs/portfolio_state.json"
        self.snapshots_file = "logs/portfolio_snapshots.json"
        
        # Performance tracking
        self.daily_snapshots = {}
        self.performance_cache = {}
        
        # Load existing data
        self._load_portfolio_state()
        self._load_historical_snapshots()
        
        logger.info("PortfolioManager initialized")
    
    def update_portfolio(self, force_update: bool = False) -> Dict[str, Any]:
        """
        Update complete portfolio from exchange
        
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
            
            # Get account information
            account_info = self.client.get_account()
            balances = account_info['balances']
            
            # Clear existing positions
            self.positions.clear()
            
            # Process all non-zero balances
            total_value_usdt = 0.0
            
            for balance in balances:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total_quantity = free + locked
                
                if total_quantity > 0.0000001:  # Minimum threshold
                    # Get current price in USDT
                    current_price = self._get_asset_price_usdt(asset)
                    market_value = total_quantity * current_price
                    
                    # Calculate P&L (requires cost basis tracking)
                    avg_cost = self._get_avg_cost(asset, current_price)
                    unrealized_pnl = (current_price - avg_cost) * total_quantity
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
                        last_updated=datetime.now()
                    )
                    
                    self.positions[asset] = position
                    total_value_usdt += market_value
            
            # Calculate allocation percentages
            for position in self.positions.values():
                position.allocation_pct = (position.market_value / total_value_usdt) * 100 if total_value_usdt > 0 else 0
            
            # Create portfolio snapshot
            snapshot = self._create_portfolio_snapshot(total_value_usdt)
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
            logger.error(f"Error updating portfolio: {e}")
            return self._get_demo_portfolio()
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        try:
            total_value = sum(pos.market_value for pos in self.positions.values())
            total_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            total_pnl_pct = ((total_value - self.initial_balance) / self.initial_balance) * 100 if self.initial_balance > 0 else 0
            
            # Asset allocation
            allocation = {pos.symbol: pos.allocation_pct for pos in self.positions.values()}
            sorted_allocation = dict(sorted(allocation.items(), key=lambda x: x[1], reverse=True))
            
            # Top positions
            top_positions = sorted(self.positions.values(), key=lambda x: x.market_value, reverse=True)[:5]
            
            # Risk metrics
            risk_metrics = self._calculate_risk_metrics()
            
            return {
                "total_value": round(total_value, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_pct": round(total_pnl_pct, 2),
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
                        "allocation": round(pos.allocation_pct, 2)
                    } for pos in top_positions
                ],
                "risk_metrics": risk_metrics,
                "daily_change": self._get_daily_change(),
                "performance_metrics": self._get_performance_metrics()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return self._get_demo_portfolio()
    
    def get_asset_position(self, symbol: str) -> Optional[AssetPosition]:
        """Get specific asset position"""
        return self.positions.get(symbol)
    
    def get_portfolio(self) -> Dict[str, float]:
        """Get simple portfolio dict for compatibility"""
        return {pos.symbol: pos.quantity for pos in self.positions.values()}
    
    def total_value(self) -> float:
        """Get total portfolio value in base currency"""
        return sum(pos.market_value for pos in self.positions.values())
    
    def get_allocation_analysis(self) -> Dict[str, Any]:
        """Get detailed allocation analysis"""
        total_value = self.total_value()
        
        if total_value == 0:
            return {"error": "No portfolio value"}
        
        # Calculate various allocation metrics
        allocations = [pos.allocation_pct for pos in self.positions.values()]
        
        return {
            "concentration_risk": max(allocations, default=0),
            "diversification_score": self._calculate_diversification_score(),
            "allocation_entropy": self._calculate_allocation_entropy(),
            "rebalancing_needed": self._check_rebalancing_needed(),
            "recommended_actions": self._get_rebalancing_recommendations()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        if len(self