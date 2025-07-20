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