#!/usr/bin/env python3
"""
Integration Guide: Portfolio Scanner with Existing Trading Bot
This shows how to integrate the dynamic portfolio scanner with your existing codebase
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the existing modules to path
sys.path.append('.')
sys.path.append('./engine')
sys.path.append('./ml')
sys.path.append('./quantum')

# Import your existing components
try:
    from engine.trading_core import TradingCore
    from engine.risk_manager import RiskManager
    from engine.portfolio_manager import HybridPortfolioManager
    from ml.decision_engine import DecisionEngine
    from quantum.hybrid_models import HybridQuantumEnsemble
    from sentiment.news_sentiment import fetch_cached_sentiment
    from dashboard.metrics import calculate_equity_curve
except ImportError as e:
    print(f"Some existing modules not found: {e}")
    print("This is normal if running standalone")

# Import our new portfolio scanner
from auto_portfolio_monitor import AutoPortfolioMonitor, Position

class IntegratedTradingSystem:
    """
    Integrated system that combines:
    1. Dynamic portfolio scanning (new)
    2. Existing AI/ML decision engine
    3. Quantum models
    4. Risk management
    5. Real-time execution
    """
    
    def __init__(self):
        # Initialize new portfolio scanner
        self.portfolio_scanner = AutoPortfolioMonitor()
        
        # Initialize existing components (if available)
        try:
            self.decision_engine = DecisionEngine()
            self.risk_manager = RiskManager()
            self.trading_core = TradingCore()
            
            # Get number of assets from portfolio
            num_assets = len(self.portfolio_scanner.positions)
            self.portfolio_manager = HybridPortfolioManager(num_assets) if num_assets > 0 else None
            
            print("✅ Existing trading components loaded")
        except:
            print("⚠️ Some existing components not available - running in scanner-only mode")
            self.decision_engine = None
            self.risk_manager = None
            self.trading_core = None
            self.portfolio_manager = None
        
        # Integration state
        self.last_signals = {}
        self.trade_history = []
        self.running = False
    
    async def start_integrated_system(self):
        """Start the fully integrated trading system"""
        self.running = True
        print("🚀 Starting Integrated Trading System...")
        
        # Start portfolio scanning
        scanner_task = asyncio.create_task(self.portfolio_scanner.start())
        
        # Start trading logic (if components available)
        if self.decision_engine:
            trading_task = asyncio.create_task(self.trading_loop())
            dashboard_task = asyncio.create_task(self.dashboard_updates())
            
            await asyncio.gather(scanner_task, trading_task, dashboard_task)
        else:
            # Run scanner only
            await scanner_task
    
    async def trading_loop(self):
        """Main trading loop that uses live portfolio data"""
        while self.running:
            try:
                # Get current positions from scanner
                positions = self.portfolio_scanner.positions
                price_data = self.portfolio_scanner.price_data
                
                if not positions or not price_data:
                    await asyncio.sleep(60)
                    continue
                
                # Process each position for trading signals