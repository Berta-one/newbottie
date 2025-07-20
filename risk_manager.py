#!/usr/bin/env python3
"""
Advanced Risk Management System - risk_manager.py
=================================================

Comprehensive risk management module for the modular crypto trading bot.
Handles position sizing, risk validation, exposure limits, and portfolio protection.

Features:
- Dynamic position sizing based on volatility and confidence
- Portfolio exposure limits and correlation analysis
- Risk validation for all trade executions
- Multiple risk profiles (Conservative, Balanced, Aggressive)
- Real-time risk monitoring and alerts
- Drawdown protection and circuit breakers
"""

import os
import json
import math
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RiskProfile:
    """Risk profile configuration"""
    name: str
    max_position_size: float  # Max % of portfolio per position
    max_portfolio_risk: float  # Max % portfolio at risk
    max_open_positions: int
    max_correlation_exposure: float  # Max exposure to correlated assets
    stop_loss_atr_mult: float
    take_profit_atr_mult: float
    trailing_stop_atr_mult: float
    max_hold_hours: int
    confidence_threshold: float
    volatility_adjustment: bool

@dataclass
class TradeValidation:
    """Trade validation result"""
    is_valid: bool
    reason: str
    recommended_size: float
    risk_score: float
    warnings: List[str]

class RiskManager:
    """
    Advanced Risk Management System
    
    Handles all risk-related calculations and validations for the trading system.
    """
    
    def __init__(self, profile_name: str = "BALANCED"):
        """Initialize with specified risk profile"""
        self.profile_name = profile_name
        self.risk_profiles = self._initialize_risk_profiles()
        self.current_profile = self.risk_profiles.get(profile_name, self.risk_profiles["BALANCED"])
        
        # Risk monitoring
        self.daily_loss_limit = float(os.getenv("DAILY_LOSS_LIMIT", "5.0"))  # % of portfolio
        self.max_consecutive_losses = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "5"))
        self.circuit_breaker_enabled = os.getenv("CIRCUIT_BREAKER", "true").lower() == "true"
        
        # Portfolio state
        self.active_positions = {}
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.last_reset_date = datetime.now().date()
        
        logger.info(f"RiskManager initialized with profile: {profile_name}")
    
    def _initialize_risk_profiles(self) -> Dict[str, RiskProfile]:
        """Initialize predefined risk profiles"""
        return {
            "CONSERVATIVE": RiskProfile(
                name="Conservative",
                max_position_size=2.0,      # 2% max per position
                max_portfolio_risk=10.0,    # 10% total portfolio risk
                max_open_positions=3,
                max_correlation_exposure=15.0,
                stop_loss_atr_mult=2.0,
                take_profit_atr_mult=4.0,
                trailing_stop_atr_mult=1.5,
                max_hold_hours=8,
                confidence_threshold=0.75,
                volatility_adjustment=True
            ),
            "BALANCED": RiskProfile(
                name="Balanced",
                max_position_size=3.0,      # 3% max per position
                max_portfolio_risk=15.0,    # 15% total portfolio risk
                max_open_positions=5,
                max_correlation_exposure=25.0,
                stop_loss_atr_mult=2.5,
                take_profit_atr_mult=5.0,
                trailing_stop_atr_mult=2.0,
                max_hold_hours=12,
                confidence_threshold=0.65,
                volatility_adjustment=True
            ),
            "AGGRESSIVE": RiskProfile(
                name="Aggressive",
                max_position_size=5.0,      # 5% max per position
                max_portfolio_risk=25.0,    # 25% total portfolio risk
                max_open_positions=8,
                max_correlation_exposure=40.0,
                stop_loss_atr_mult=3.0,
                take_profit_atr_mult=6.0,
                trailing_stop_atr_mult=2.5,
                max_hold_hours=24,
                confidence_threshold=0.55,
                volatility_adjustment=True
            ),
            "SCALPING": RiskProfile(
                name="Scalping",
                max_position_size=1.5,      # 1.5% max per position
                max_portfolio_risk=8.0,     # 8% total portfolio risk
                max_open_positions=10,
                max_correlation_exposure=20.0,
                stop_loss_atr_mult=1.0,
                take_profit_atr_mult=2.0,
                trailing_stop_atr_mult=0.8,
                max_hold_hours=2,
                confidence_threshold=0.70,
                volatility_adjustment=False
            )
        }
    
    def calculate_position_size(
        self, 
        symbol: str,
        account_balance: float,
        price: float,
        confidence: float,
        volatility: float = 0.0,
        atr: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size based on risk parameters
        
        Args:
            symbol: Trading symbol
            account_balance: Current account balance
            price: Current price
            confidence: Strategy confidence (0.0-1.0)
            volatility: Asset volatility
            atr: Average True Range
            
        Returns:
            Dictionary with position sizing details
        """
        try:
            # Base position size from risk profile
            base_risk_amount = account_balance * (self.current_profile.max_position_size / 100)
            
            # Confidence adjustment
            confidence_multiplier = min(confidence / self.current_profile.confidence_threshold, 1.5)
            adjusted_risk_amount = base_risk_amount * confidence_multiplier
            
            # Volatility adjustment if enabled
            if self.current_profile.volatility_adjustment and volatility > 0:
                # Reduce size for high volatility assets
                volatility_multiplier = max(0.5, 1.0 - (volatility - 0.02) * 5)  # Reduce if vol > 2%
                adjusted_risk_amount *= volatility_multiplier
            
            # Calculate quantity based on stop loss
            if atr > 0:
                stop_distance = atr * self.current_profile.stop_loss_atr_mult
                stop_price = price - stop_distance
                max_loss = price - stop_price
                
                if max_loss > 0:
                    quantity = adjusted_risk_amount / max_loss
                else:
                    quantity = adjusted_risk_amount / (price * 0.05)  # 5% fallback
            else:
                # Fallback: 5% stop loss
                quantity = adjusted_risk_amount / (price * 0.05)
            
            # Portfolio limits check
            current_exposure = self._calculate_portfolio_exposure()
            max_exposure = account_balance * (self.current_profile.max_portfolio_risk / 100)
            
            if current_exposure + adjusted_risk_amount > max_exposure:
                # Reduce size to fit within portfolio limits
                available_exposure = max_exposure - current_exposure
                if available_exposure > 0:
                    quantity = quantity * (available_exposure / adjusted_risk_amount)
                else:
                    quantity = 0
            
            # Calculate trade value
            trade_value = quantity * price
            
            return {
                "quantity": round(quantity, 8),
                "trade_value": round(trade_value, 2),
                "risk_amount": round(adjusted_risk_amount, 2),
                "confidence_multiplier": round(confidence_multiplier, 3),
                "volatility_multiplier": round(volatility_multiplier, 3) if self.current_profile.volatility_adjustment else 1.0,
                "portfolio_risk_pct": round((adjusted_risk_amount / account_balance) * 100, 2),
                "stop_loss_price": round(price - (atr * self.current_profile.stop_loss_atr_mult), 6) if atr > 0 else None,
                "take_profit_price": round(price + (atr * self.current_profile.take_profit_atr_mult), 6) if atr > 0 else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {
                "quantity": 0,
                "trade_value": 0,
                "risk_amount": 0,
                "error": str(e)
            }
    
    def validate_trade(
        self,
        symbol: str,
        quantity: float,
        price: float,
        account_balance: float,
        open_positions: int,
        trade_type: str = "BUY"
    ) -> TradeValidation:
        """
        Comprehensive trade validation
        
        Args:
            symbol: Trading symbol
            quantity: Proposed quantity
            price: Current price
            account_balance: Account balance
            open_positions: Number of open positions
            trade_type: BUY or SELL
            
        Returns:
            TradeValidation object
        """
        warnings = []
        
        # Check circuit breaker
        if self._is_circuit_breaker_triggered():
            return TradeValidation(
                is_valid=False,
                reason="Circuit breaker triggered - daily loss limit exceeded",
                recommended_size=0,
                risk_score=1.0,
                warnings=["Trading suspended due to excessive losses"]
            )
        
        # Check consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            return TradeValidation(
                is_valid=False,
                reason=f"Maximum consecutive losses ({self.max_consecutive_losses}) reached",
                recommended_size=0,
                risk_score=1.0,
                warnings=["Consider reviewing strategy before continuing"]
            )
        
        # Check maximum positions
        if open_positions >= self.current_profile.max_open_positions:
            return TradeValidation(
                is_valid=False,
                reason=f"Maximum positions ({self.current_profile.max_open_positions}) reached",
                recommended_size=0,
                risk_score=0.8,
                warnings=["Close existing positions before opening new ones"]
            )
        
        # Calculate trade value and risk
        trade_value = quantity * price
        position_risk_pct = (trade_value / account_balance) * 100
        
        # Check position size limits
        if position_risk_pct > self.current_profile.max_position_size:
            recommended_quantity = (account_balance * self.current_profile.max_position_size / 100) / price
            warnings.append(f"Position size reduced from {position_risk_pct:.2f}% to {self.current_profile.max_position_size}%")
            
            return TradeValidation(
                is_valid=True,
                reason="Position size adjusted to fit risk limits",
                recommended_size=recommended_quantity,
                risk_score=position_risk_pct / 100,
                warnings=warnings
            )
        
        # Check minimum trade size
        min_trade_value = float(os.getenv("MIN_TRADE_VALUE", "10.0"))
        if trade_value < min_trade_value:
            return TradeValidation(
                is_valid=False,
                reason=f"Trade value ${trade_value:.2f} below minimum ${min_trade_value}",
                recommended_size=min_trade_value / price,
                risk_score=0.1,
                warnings=["Increase position size or choose different asset"]
            )
        
        # Check account balance
        required_balance = trade_value * 1.1  # 10% buffer for fees
        if required_balance > account_balance:
            return TradeValidation(
                is_valid=False,
                reason="Insufficient account balance",
                recommended_size=(account_balance * 0.9) / price,
                risk_score=0.9,
                warnings=["Reduce position size or add funds"]
            )
        
        # Risk score calculation
        risk_score = min(position_risk_pct / self.current_profile.max_position_size, 1.0)
        
        # Add performance warnings
        if risk_score > 0.7:
            warnings.append("High risk trade - consider reducing size")
        
        return TradeValidation(
            is_valid=True,
            reason="Trade validated successfully",
            recommended_size=quantity,
            risk_score=risk_score,
            warnings=warnings
        )
    
    def update_position(self, symbol: str, position_data: Dict[str, Any]):
        """Update active position data"""
        self.active_positions[symbol] = {
            **position_data,
            "last_update": datetime.now()
        }
    
    def close_position(self, symbol: str, pnl: float):
        """Close position and update risk metrics"""
        if symbol in self.active_positions:
            del self.active_positions[symbol]
        
        # Update daily P&L
        self.daily_pnl += pnl
        
        # Update consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Check daily reset
        self._check_daily_reset()
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        return {
            "profile": self.current_profile.name,
            "active_positions": len(self.active_positions),
            "max_positions": self.current_profile.max_open_positions,
            "daily_pnl": self.daily_pnl,
            "daily_loss_limit": self.daily_loss_limit,
            "consecutive_losses": self.consecutive_losses,
            "max_consecutive_losses": self.max_consecutive_losses,
            "circuit_breaker_active": self._is_circuit_breaker_triggered(),
            "portfolio_exposure": self._calculate_portfolio_exposure(),
            "risk_score": self._calculate_overall_risk_score()
        }
    
    def get_stop_take_levels(self, entry_price: float, atr: float, trade_type: str = "BUY") -> Dict[str, float]:
        """Calculate stop loss and take profit levels"""
        if trade_type.upper() == "BUY":
            stop_loss = entry_price - (atr * self.current_profile.stop_loss_atr_mult)
            take_profit = entry_price + (atr * self.current_profile.take_profit_atr_mult)
            trailing_stop = atr * self.current_profile.trailing_stop_atr_mult
        else:  # SELL
            stop_loss = entry_price + (atr * self.current_profile.stop_loss_atr_mult)
            take_profit = entry_price - (atr * self.current_profile.take_profit_atr_mult)
            trailing_stop = atr * self.current_profile.trailing_stop_atr_mult
        
        return {
            "stop_loss": round(stop_loss, 8),
            "take_profit": round(take_profit, 8),
            "trailing_stop_distance": round(trailing_stop, 8)
        }
    
    def _calculate_portfolio_exposure(self) -> float:
        """Calculate current portfolio exposure"""
        total_exposure = 0.0
        for position in self.active_positions.values():
            total_exposure += position.get("risk_amount", 0.0)
        return total_exposure
    
    def _calculate_overall_risk_score(self) -> float:
        """Calculate overall portfolio risk score (0.0-1.0)"""
        factors = []
        
        # Position count factor
        position_factor = len(self.active_positions) / self.current_profile.max_open_positions
        factors.append(position_factor)
        
        # Daily P&L factor
        if self.daily_pnl < 0:
            pnl_factor = abs(self.daily_pnl) / (self.daily_loss_limit * 100)  # Normalize to account balance
            factors.append(min(pnl_factor, 1.0))
        
        # Consecutive losses factor
        loss_factor = self.consecutive_losses / self.max_consecutive_losses
        factors.append(loss_factor)
        
        return min(statistics.mean(factors) if factors else 0.0, 1.0)
    
    def _is_circuit_breaker_triggered(self) -> bool:
        """Check if circuit breaker should be triggered"""
        if not self.circuit_breaker_enabled:
            return False
        
        daily_loss_pct = abs(self.daily_pnl) / 1000  # Normalize to percentage (assuming 1000 base)
        return daily_loss_pct >= self.daily_loss_limit
    
    def _check_daily_reset(self):
        """Reset daily counters if new day"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
            logger.info("Daily risk metrics reset")
    
    def switch_profile(self, profile_name: str) -> bool:
        """Switch to different risk profile"""
        if profile_name in self.risk_profiles:
            self.current_profile = self.risk_profiles[profile_name]
            self.profile_name = profile_name
            logger.info(f"Switched to risk profile: {profile_name}")
            return True
        else:
            logger.error(f"Unknown risk profile: {profile_name}")
            return False
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available risk profiles"""
        return list(self.risk_profiles.keys())

# Global instance for easy access
_risk_manager = None

def get_risk_manager(profile: str = "BALANCED") -> RiskManager:
    """Get global risk manager instance"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager(profile)
    return _risk_manager

# Convenience functions
def calculate_position_size(symbol: str, balance: float, price: float, confidence: float, volatility: float = 0.0, atr: float = 0.0) -> Dict[str, Any]:
    """Calculate position size using global risk manager"""
    return get_risk_manager().calculate_position_size(symbol, balance, price, confidence, volatility, atr)

def validate_trade(symbol: str, quantity: float, price: float, balance: float, open_positions: int) -> TradeValidation:
    """Validate trade using global risk manager"""
    return get_risk_manager().validate_trade(symbol, quantity, price, balance, open_positions)

if __name__ == "__main__":
    # Example usage
    rm = RiskManager("BALANCED")
    
    # Test position sizing
    position_info = rm.calculate_position_size(
        symbol="BTCUSDT",
        account_balance=10000.0,
        price=45000.0,
        confidence=0.75,
        volatility=0.03,
        atr=500.0
    )
    
    print("Position Sizing Result:")
    for key, value in position_info.items():
        print(f"  {key}: {value}")
    
    # Test trade validation
    validation = rm.validate_trade(
        symbol="BTCUSDT",
        quantity=position_info["quantity"],
        price=45000.0,
        account_balance=10000.0,
        open_positions=2
    )
    
    print(f"\nTrade Validation:")
    print(f"  Valid: {validation.is_valid}")
    print(f"  Reason: {validation.reason}")
    print(f"  Risk Score: {validation.risk_score}")
    print(f"  Warnings: {validation.warnings}")