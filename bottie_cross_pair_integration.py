#!/usr/bin/env python3
"""
bottie_cross_pair_integration.py
Integration module for adding cross-pair trading to existing Bottie API
"""

import os
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException

try:
    from portfolio_cross_trading import PortfolioCrossPairEngine, CrossPairOpportunity
except ImportError:
    print("Warning: portfolio_cross_trading.py not found. Cross-pair trading disabled.")
    PortfolioCrossPairEngine = None
    CrossPairOpportunity = None

class BottieCrossPairSignalGenerator:
    """Enhanced signal generator with cross-pair trading capabilities"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True):
        self.cross_engine = None
        
        if PortfolioCrossPairEngine:
            self.cross_engine = PortfolioCrossPairEngine(api_key, api_secret, testnet)
        
        self.logger = logging.getLogger(__name__)
        self.last_scan_time = 0
        
    async def initialize(self):
        """Initialize the cross-pair engine"""
        if self.cross_engine:
            try:
                await self.cross_engine.initialize()
                self.logger.info("Cross-pair signal generator initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize cross-pair engine: {e}")
                self.cross_engine = None
    
    async def get_enhanced_signals(self, existing_signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get enhanced signals with cross-pair opportunities"""
        result = {
            "traditional_signals": existing_signals,
            "cross_pair_signals": [],
            "portfolio_rebalancing": [],
            "timestamp": time.time(),
            "cross_pair_enabled": self.cross_engine is not None
        }
        
        if not self.cross_engine:
            return result
        
        try:
            # Scan for cross-pair opportunities
            opportunities = await self.cross_engine.scan_cross_opportunities()
            
            # Convert to signals format
            cross_signals = []
            for opp in opportunities[:20]:  # Top 20 opportunities
                signal = {
                    "symbol": opp.symbol,
                    "direction": opp.direction,
                    "strength": opp.signal_strength,
                    "type": "cross_pair",
                    "from_asset": opp.from_asset,
                    "to_asset": opp.to_asset,
                    "price": opp.current_price,
                    "profit_potential": opp.estimated_profit_pct,
                    "volume_24h": opp.volume_24h,
                    "timestamp": opp.timestamp
                }
                cross_signals.append(signal)
            
            result["cross_pair_signals"] = cross_signals
            
            # Generate portfolio rebalancing suggestions
            rebalancing = await self._generate_rebalancing_suggestions(opportunities)
            result["portfolio_rebalancing"] = rebalancing
            
        except Exception as e:
            self.logger.error(f"Failed to get cross-pair signals: {e}")
        
        return result
    
    async def _generate_rebalancing_suggestions(self, opportunities: List[CrossPairOpportunity]) -> List[Dict[str, Any]]:
        """Generate AI-powered portfolio rebalancing suggestions"""
        suggestions = []
        
        try:
            # Group opportunities by asset pairs
            asset_pairs = {}
            for opp in opportunities:
                pair_key = f"{opp.from_asset}-{opp.to_asset}"
                if pair_key not in asset_pairs:
                    asset_pairs[pair_key] = []
                asset_pairs[pair_key].append(opp)
            
            # Generate suggestions for top opportunities
            for pair_key, pair_opps in list(asset_pairs.items())[:5]:
                best_opp = max(pair_opps, key=lambda x: x.signal_strength * x.estimated_profit_pct)
                
                if best_opp.signal_strength > 0.6 and best_opp.estimated_profit_pct > 0.002:
                    suggestion = {
                        "action": f"Rebalance {best_opp.from_asset} → {best_opp.to_asset}",
                        "from_asset": best_opp.from_asset,
                        "to_asset": best_opp.to_asset,
                        "symbol": best_opp.symbol,
                        "confidence": best_opp.signal_strength,
                        "expected_profit": best_opp.estimated_profit_pct,
                        "reasoning": f"Strong signal ({best_opp.signal_strength:.1%}) with {best_opp.estimated_profit_pct:.2%} profit potential",
                        "recommended_allocation": min(0.05, best_opp.estimated_profit_pct * 10),  # Max 5% of portfolio
                        "priority": "high" if best_opp.signal_strength > 0.8 else "medium",
                        "timestamp": time.time()
                    }
                    suggestions.append(suggestion)
            
        except Exception as e:
            self.logger.error(f"Failed to generate rebalancing suggestions: {e}")
        
        return suggestions

def add_cross_pair_endpoints(app: FastAPI, signal_generator: BottieCrossPairSignalGenerator):
    """Add cross-pair trading endpoints to existing FastAPI app"""
    
    @app.get("/cross-pairs/status")
    async def cross_pair_status():
        """Get cross-pair trading status"""
        return {
            "enabled": signal_generator.cross_engine is not None,
            "engine_initialized": signal_generator.cross_engine is not None,
            "last_scan": signal_generator.last_scan_time,
            "timestamp": time.time()
        }
    
    @app.get("/cross-pairs/opportunities")
    async def get_cross_pair_opportunities():
        """Get current cross-pair trading opportunities"""
        if not signal_generator.cross_engine:
            return {
                "enabled": False,
                "opportunities": [],
                "message": "Cross-pair trading not enabled"
            }
        
        try:
            await signal_generator.initialize()
            opportunities = await signal_generator.cross_engine.scan_cross_opportunities()
            
            opportunity_data = []
            for opp in opportunities:
                opportunity_data.append({
                    "symbol": opp.symbol,
                    "from_asset": opp.from_asset,
                    "to_asset": opp.to_asset,
                    "direction": opp.direction,
                    "current_price": opp.current_price,
                    "signal_strength": opp.signal_strength,
                    "estimated_profit_pct": opp.estimated_profit_pct,
                    "volume_24h": opp.volume_24h,
                    "timestamp": opp.timestamp
                })
            
            signal_generator.last_scan_time = time.time()
            
            return {
                "enabled": True,
                "opportunities": opportunity_data,
                "count": len(opportunity_data),
                "scan_time": signal_generator.last_scan_time
            }
            
        except Exception as e:
            logging.error(f"Cross-pair opportunities error: {e}")
            return {
                "enabled": True,
                "opportunities": [],
                "error": str(e)
            }
    
    @app.get("/portfolio/cross-pairs")
    async def get_portfolio_cross_pairs():
        """Get all possible cross-trading pairs in portfolio"""
        if not signal_generator.cross_engine:
            return {
                "enabled": False,
                "pairs": [],
                "message": "Cross-pair trading not enabled"
            }
        
        try:
            await signal_generator.initialize()
            
            pairs = list(signal_generator.cross_engine.available_pairs.keys())
            assets = list(signal_generator.cross_engine.portfolio_assets)
            
            return {
                "enabled": True,
                "portfolio_assets": assets,
                "available_pairs": pairs,
                "total_pairs": len(pairs),
                "total_assets": len(assets),
                "pair_details": signal_generator.cross_engine.available_pairs
            }
            
        except Exception as e:
            logging.error(f"Portfolio cross-pairs error: {e}")
            return {
                "enabled": True,
                "pairs": [],
                "error": str(e)
            }
    
    @app.get("/portfolio/rebalancing-suggestions")
    async def get_rebalancing_suggestions():
        """Get AI-powered portfolio rebalancing suggestions"""
        if not signal_generator.cross_engine:
            return {
                "enabled": False,
                "suggestions": [],
                "message": "Cross-pair trading not enabled"
            }
        
        try:
            await signal_generator.initialize()
            opportunities = await signal_generator.cross_engine.scan_cross_opportunities()
            suggestions = await signal_generator._generate_rebalancing_suggestions(opportunities)
            
            return {
                "enabled": True,
                "suggestions": suggestions,
                "count": len(suggestions),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logging.error(f"Rebalancing suggestions error: {e}")
            return {
                "enabled": True,
                "suggestions": [],
                "error": str(e)
            }

async def enhanced_signals_endpoint(signal_generator: BottieCrossPairSignalGenerator, existing_signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Enhanced signals endpoint that includes cross-pair opportunities"""
    try:
        return await signal_generator.get_enhanced_signals(existing_signals)
    except Exception as e:
        logging.error(f"Enhanced signals error: {e}")
        return {
            "traditional_signals": existing_signals,
            "cross_pair_signals": [],
            "portfolio_rebalancing": [],
            "error": str(e),
            "timestamp": time.time()
        }
