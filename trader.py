#!/usr/bin/env python3
"""
Enhanced Position Management System - trader.py
==============================================

Comprehensive position management with dynamic sizing, multiple exit strategies,
and enhanced monitoring as specified in GitHub Copilot instructions.

Features:
- Dynamic position sizing based on account balance, confidence, and volatility
- Risk management: limit risk to 1-2% of account per trade
- Enhanced position monitoring with multiple exit strategies:
  * Take profit: 8-15% based on confidence level
  * Stop loss: 8-12% based on confidence level  
  * Trailing stops: 3-4% trail when profitable
  * Time-based exits: maximum 4 hour hold time
  * Emergency exits: >15% moves in either direction
- Account balance tracking for USDT
- Detailed trade execution logging with P&L calculation
"""

import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import threading

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    Client = None

from logger import log_trade

class EnhancedTrader:
    """
    Enhanced trader with dynamic position sizing and comprehensive risk management
    """
    
    def __init__(self, binance_client: Optional[Client] = None):
        self.client = binance_client
        self.active_positions = {}
        self.position_lock = threading.Lock()
        
        # Risk management settings
        self.max_risk_per_trade = 0.02  # 2% maximum risk per trade
        self.max_hold_time_hours = 4
        self.emergency_exit_threshold = 15.0  # 15% emergency exit
        
        # Ensure logs directory
        os.makedirs('logs', exist_ok=True)
    
    def calculate_dynamic_position_size(self, 
                                      account_balance: float,
                                      base_quantity: float,
                                      confidence: float,
                                      volatility: float,
                                      risk_percentage: float = 0.015) -> float:
        """
        Calculate dynamic position size based on multiple factors
        
        Args:
            account_balance: Current account balance in USDT
            base_quantity: Base trade quantity
            confidence: Strategy confidence (0.0-1.0)
            volatility: Market volatility percentage
            risk_percentage: Risk percentage per trade (default 1.5%)
            
        Returns:
            Calculated position size
        """
        # Risk budget calculation
        risk_amount = account_balance * min(risk_percentage, self.max_risk_per_trade)
        
        # Confidence multiplier (0.3x to 2.0x)
        confidence_multiplier = 0.3 + (confidence * 1.7)
        
        # Volatility adjustment (reduce size in high volatility)
        volatility_multiplier = 1.0
        if volatility > 5.0:
            volatility_multiplier = max(0.5, 1.0 - (volatility - 5.0) / 20.0)
        elif volatility < 2.0:
            volatility_multiplier = min(1.5, 1.0 + (2.0 - volatility) / 10.0)
        
        # Calculate final position size
        adjusted_quantity = (base_quantity * 
                           confidence_multiplier * 
                           volatility_multiplier)
        
        # Ensure position doesn't exceed risk budget
        max_quantity_by_risk = risk_amount / (base_quantity * 100)  # Assuming ~1% price move
        final_quantity = min(adjusted_quantity, max_quantity_by_risk)
        
        return max(final_quantity, base_quantity * 0.1)  # Minimum 10% of base
    
    def get_dynamic_exit_levels(self, 
                               confidence: float,
                               volatility: float) -> Dict[str, float]:
        """
        Calculate dynamic take profit and stop loss levels based on confidence and volatility
        
        Args:
            confidence: Strategy confidence (0.0-1.0)
            volatility: Market volatility percentage
            
        Returns:
            Dictionary with exit levels
        """
        # Base levels
        base_take_profit = 10.0
        base_stop_loss = 8.0
        base_trailing_stop = 3.5
        
        # Confidence adjustments
        confidence_factor = 0.5 + confidence  # 0.5 to 1.5
        
        # Volatility adjustments
        volatility_factor = 1.0
        if volatility > 5.0:
            volatility_factor = 1.0 + (volatility - 5.0) / 10.0  # Increase levels in high vol
        
        # Calculate dynamic levels
        take_profit = base_take_profit * confidence_factor * volatility_factor
        stop_loss = base_stop_loss * confidence_factor * volatility_factor
        trailing_stop = base_trailing_stop * confidence_factor
        
        # Ensure reasonable bounds
        take_profit = max(8.0, min(take_profit, 20.0))
        stop_loss = max(6.0, min(stop_loss, 15.0))
        trailing_stop = max(2.0, min(trailing_stop, 6.0))
        
        return {
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'trailing_stop': trailing_stop
        }
    
    def execute_entry(self, 
                     symbol: str,
                     quantity: float,
                     signal_type: str,
                     current_price: float = None) -> Dict[str, Any]:
        """
        Execute entry order with comprehensive logging
        
        Args:
            symbol: Trading symbol
            quantity: Position size
            signal_type: "BUY_LONG" or "BUY_SHORT"
            current_price: Current market price (optional)
            
        Returns:
            Execution result dictionary
        """
        try:
            if not self.client:
                return self._mock_execute_entry(symbol, quantity, signal_type, current_price)
            
            # Validate minimum quantity
            if not self._validate_minimum_quantity(symbol, quantity):
                return {
                    'status': 'FAILED',
                    'error': 'Quantity below minimum requirements',
                    'symbol': symbol,
                    'quantity': quantity
                }
            
            # Execute market order
            if signal_type == "BUY_LONG":
                order = self.client.order_market_buy(
                    symbol=symbol,
                    quantity=self._format_quantity(symbol, quantity)
                )
            else:  # BUY_SHORT (sell order)
                order = self.client.order_market_sell(
                    symbol=symbol,
                    quantity=self._format_quantity(symbol, quantity)
                )
            
            # Calculate average fill price
            fills = order.get('fills', [])
            if fills:
                total_qty = sum(float(fill['qty']) for fill in fills)
                total_cost = sum(float(fill['qty']) * float(fill['price']) for fill in fills)
                avg_price = total_cost / total_qty if total_qty > 0 else 0
            else:
                avg_price = current_price or 0
            
            result = {
                'status': 'SUCCESS',
                'symbol': symbol,
                'quantity': float(order.get('executedQty', quantity)),
                'entry_price': avg_price,
                'order_id': order.get('orderId'),
                'signal_type': signal_type,
                'timestamp': datetime.now().isoformat(),
                'commission': self._calculate_commission(fills)
            }
            
            # Log successful entry
            log_trade({
                **result,
                'trade_type': 'ENTRY',
                'status': 'FILLED'
            })
            
            return result
        
        except BinanceAPIException as e:
            error_result = {
                'status': 'FAILED',
                'error': f'Binance API Error: {e.message}',
                'symbol': symbol,
                'quantity': quantity,
                'signal_type': signal_type
            }
            
            log_trade({
                **error_result,
                'trade_type': 'ENTRY',
                'timestamp': datetime.now().isoformat()
            })
            
            return error_result
        
        except Exception as e:
            error_result = {
                'status': 'FAILED',
                'error': str(e),
                'symbol': symbol,
                'quantity': quantity,
                'signal_type': signal_type
            }
            
            log_trade({
                **error_result,
                'trade_type': 'ENTRY',
                'timestamp': datetime.now().isoformat()
            })
            
            return error_result
    
    def monitor_position_enhanced(self, 
                                entry_price: float,
                                symbol: str,
                                quantity: float,
                                signal_type: str,
                                confidence: float = 0.7,
                                volatility: float = 3.0,
                                max_hold_time_minutes: int = 240) -> Dict[str, Any]:
        """
        Enhanced position monitoring with multiple exit strategies
        
        Args:
            entry_price: Entry price of the position
            symbol: Trading symbol
            quantity: Position size
            signal_type: "BUY_LONG" or "BUY_SHORT"
            confidence: Strategy confidence for dynamic exits
            volatility: Market volatility for dynamic exits
            max_hold_time_minutes: Maximum hold time in minutes
            
        Returns:
            Exit result dictionary
        """
        start_time = datetime.now()
        max_hold_time = timedelta(minutes=max_hold_time_minutes)
        
        # Get dynamic exit levels
        exit_levels = self.get_dynamic_exit_levels(confidence, volatility)
        take_profit_pct = exit_levels['take_profit']
        stop_loss_pct = exit_levels['stop_loss']
        trailing_stop_pct = exit_levels['trailing_stop']
        
        # Initialize tracking variables
        highest_profit = 0.0
        trailing_stop_active = False
        trailing_stop_price = 0.0
        
        position_id = f"{symbol}_{int(start_time.timestamp())}"
        
        print(f"🔍 Monitoring position: {symbol} | Entry: ${entry_price:.6f} | TP: {take_profit_pct:.1f}% | SL: {stop_loss_pct:.1f}%")
        
        try:
            while True:
                current_time = datetime.now()
                time_held = current_time - start_time
                
                # Get current price
                current_price = self._get_current_price(symbol)
                if not current_price:
                    time.sleep(30)
                    continue
                
                # Calculate P&L
                if signal_type == "BUY_LONG":
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                else:  # BUY_SHORT
                    pnl_pct = ((entry_price - current_price) / entry_price) * 100
                
                pnl_usd = (pnl_pct / 100) * quantity * entry_price
                
                # Update highest profit for trailing stop
                if pnl_pct > highest_profit:
                    highest_profit = pnl_pct
                    
                    # Activate trailing stop when profitable
                    if pnl_pct > trailing_stop_pct and not trailing_stop_active:
                        trailing_stop_active = True
                        if signal_type == "BUY_LONG":
                            trailing_stop_price = current_price * (1 - trailing_stop_pct / 100)
                        else:
                            trailing_stop_price = current_price * (1 + trailing_stop_pct / 100)
                        print(f"🔄 Trailing stop activated at ${trailing_stop_price:.6f}")
                    
                    # Update trailing stop price
                    elif trailing_stop_active:
                        if signal_type == "BUY_LONG":
                            new_trailing_price = current_price * (1 - trailing_stop_pct / 100)
                            if new_trailing_price > trailing_stop_price:
                                trailing_stop_price = new_trailing_price
                        else:
                            new_trailing_price = current_price * (1 + trailing_stop_pct / 100)
                            if new_trailing_price < trailing_stop_price:
                                trailing_stop_price = new_trailing_price
                
                # Check exit conditions
                exit_reason = None
                
                # 1. Take Profit
                if pnl_pct >= take_profit_pct:
                    exit_reason = f"Take profit hit: {pnl_pct:.2f}% >= {take_profit_pct:.1f}%"
                
                # 2. Stop Loss
                elif pnl_pct <= -stop_loss_pct:
                    exit_reason = f"Stop loss hit: {pnl_pct:.2f}% <= -{stop_loss_pct:.1f}%"
                
                # 3. Trailing Stop
                elif trailing_stop_active:
                    if signal_type == "BUY_LONG" and current_price <= trailing_stop_price:
                        exit_reason = f"Trailing stop hit: ${current_price:.6f} <= ${trailing_stop_price:.6f}"
                    elif signal_type == "BUY_SHORT" and current_price >= trailing_stop_price:
                        exit_reason = f"Trailing stop hit: ${current_price:.6f} >= ${trailing_stop_price:.6f}"
                
                # 4. Time-based Exit
                elif time_held >= max_hold_time:
                    exit_reason = f"Time limit reached: {time_held.total_seconds()/60:.0f} minutes"
                
                # 5. Emergency Exit (>15% adverse move)
                elif pnl_pct <= -self.emergency_exit_threshold:
                    exit_reason = f"Emergency exit: {pnl_pct:.2f}% loss"
                
                # 6. Emergency Exit (>15% favorable move - lock in profits)
                elif pnl_pct >= self.emergency_exit_threshold:
                    exit_reason = f"Emergency exit: {pnl_pct:.2f}% profit"
                
                # Print status update every minute
                if int(time_held.total_seconds()) % 60 == 0:
                    print(f"📊 {symbol}: P&L {pnl_pct:+.2f}% | ${pnl_usd:+.2f} | Time: {int(time_held.total_seconds()/60)}m")
                
                # Exit if condition met
                if exit_reason:
                    print(f"🚪 Exiting position: {exit_reason}")
                    exit_result = self.execute_exit(
                        symbol=symbol,
                        quantity=quantity,
                        exit_price=current_price,
                        entry_price=entry_price,
                        reason=exit_reason,
                        signal_type=signal_type
                    )
                    
                    # Add monitoring stats to result
                    exit_result.update({
                        'time_held_minutes': time_held.total_seconds() / 60,
                        'highest_profit_pct': highest_profit,
                        'final_pnl_pct': pnl_pct,
                        'final_pnl_usd': pnl_usd,
                        'trailing_stop_used': trailing_stop_active,
                        'exit_levels_used': exit_levels
                    })
                    
                    return exit_result
                
                # Wait before next check
                time.sleep(10)  # Check every 10 seconds
        
        except KeyboardInterrupt:
            print("🛑 Monitoring interrupted by user")
            return self.execute_exit(symbol, quantity, None, entry_price, "User interruption", signal_type)
        
        except Exception as e:
            print(f"❌ Error monitoring position: {e}")
            return self.execute_exit(symbol, quantity, None, entry_price, f"Error: {e}", signal_type)
    
    def execute_exit(self, 
                    symbol: str,
                    quantity: float,
                    exit_price: float,
                    entry_price: float,
                    reason: str,
                    signal_type: str = "BUY_LONG") -> Dict[str, Any]:
        """
        Execute exit order with P&L calculation
        
        Args:
            symbol: Trading symbol
            quantity: Position size to close
            exit_price: Exit price (None for market price)
            entry_price: Original entry price
            reason: Exit reason
            signal_type: Original signal type
            
        Returns:
            Exit result dictionary
        """
        try:
            if not self.client:
                return self._mock_execute_exit(symbol, quantity, exit_price, entry_price, reason, signal_type)
            
            # Execute market order to close position
            if signal_type == "BUY_LONG":
                # Close long position with sell order
                order = self.client.order_market_sell(
                    symbol=symbol,
                    quantity=self._format_quantity(symbol, quantity)
                )
            else:
                # Close short position with buy order
                order = self.client.order_market_buy(
                    symbol=symbol,
                    quantity=self._format_quantity(symbol, quantity)
                )
            
            # Calculate actual exit price from fills
            fills = order.get('fills', [])
            if fills:
                total_qty = sum(float(fill['qty']) for fill in fills)
                total_cost = sum(float(fill['qty']) * float(fill['price']) for fill in fills)
                actual_exit_price = total_cost / total_qty if total_qty > 0 else exit_price
            else:
                actual_exit_price = exit_price or entry_price
            
            # Calculate P&L
            if signal_type == "BUY_LONG":
                pnl_pct = ((actual_exit_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - actual_exit_price) / entry_price) * 100
            
            pnl_usd = (pnl_pct / 100) * quantity * entry_price
            commission = self._calculate_commission(fills)
            net_pnl_usd = pnl_usd - commission
            
            result = {
                'status': 'SUCCESS',
                'symbol': symbol,
                'quantity': float(order.get('executedQty', quantity)),
                'entry_price': entry_price,
                'exit_price': actual_exit_price,
                'pnl_percent': pnl_pct,
                'pnl_usd': pnl_usd,
                'commission': commission,
                'net_pnl_usd': net_pnl_usd,
                'reason': reason,
                'order_id': order.get('orderId'),
                'timestamp': datetime.now().isoformat(),
                'signal_type': signal_type
            }
            
            # Log successful exit
            log_trade({
                **result,
                'trade_type': 'EXIT',
                'status': 'FILLED'
            })
            
            print(f"✅ Position closed: {symbol} | P&L: {pnl_pct:+.2f}% (${net_pnl_usd:+.2f}) | {reason}")
            
            return result
        
        except Exception as e:
            error_result = {
                'status': 'FAILED',
                'error': str(e),
                'symbol': symbol,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            
            log_trade({
                **error_result,
                'trade_type': 'EXIT'
            })
            
            print(f"❌ Failed to close position: {e}")
            return error_result
    
    def get_account_balance(self, asset: str = 'USDT') -> float:
        """
        Get account balance for specified asset
        
        Args:
            asset: Asset symbol (default: USDT)
            
        Returns:
            Account balance
        """
        try:
            if not self.client:
                # Return mock balance for testing
                return 10000.0
            
            account = self.client.get_account()
            
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            
            return 0.0
        
        except Exception as e:
            print(f"⚠️ Error getting account balance: {e}")
            return 0.0
    
    def calculate_portfolio_metrics(self, trades_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate comprehensive portfolio metrics
        
        Args:
            trades_log: List of completed trades
            
        Returns:
            Portfolio metrics dictionary
        """
        if not trades_log:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl_percent': 0.0,
                'total_pnl_usd': 0.0,
                'average_win': 0.0,
                'average_loss': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }
        
        # Separate wins and losses
        wins = [trade for trade in trades_log if trade.get('pnl_percent', 0) > 0]
        losses = [trade for trade in trades_log if trade.get('pnl_percent', 0) < 0]
        
        # Basic metrics
        total_trades = len(trades_log)
        win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
        
        total_pnl_percent = sum(trade.get('pnl_percent', 0) for trade in trades_log)
        total_pnl_usd = sum(trade.get('net_pnl_usd', 0) for trade in trades_log)
        
        # Win/Loss analysis
        average_win = sum(trade.get('pnl_percent', 0) for trade in wins) / len(wins) if wins else 0
        average_loss = sum(trade.get('pnl_percent', 0) for trade in losses) / len(losses) if losses else 0
        
        # Profit factor
        total_wins = sum(trade.get('pnl_percent', 0) for trade in wins)
        total_losses = abs(sum(trade.get('pnl_percent', 0) for trade in losses))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Risk metrics
        returns = [trade.get('pnl_percent', 0) for trade in trades_log]
        avg_return = sum(returns) / len(returns) if returns else 0
        
        # Standard deviation for Sharpe ratio
        if len(returns) > 1:
            variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
            std_dev = variance ** 0.5
            sharpe_ratio = avg_return / std_dev if std_dev > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        cumulative_returns = []
        running_total = 0
        for trade in trades_log:
            running_total += trade.get('pnl_percent', 0)
            cumulative_returns.append(running_total)
        
        if cumulative_returns:
            peak = cumulative_returns[0]
            max_drawdown = 0
            for value in cumulative_returns:
                if value > peak:
                    peak = value
                drawdown = peak - value
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        else:
            max_drawdown = 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl_percent': total_pnl_percent,
            'total_pnl_usd': total_pnl_usd,
            'average_win': average_win,
            'average_loss': abs(average_loss),
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'best_trade': max(returns) if returns else 0,
            'worst_trade': min(returns) if returns else 0
        }
    
    # Helper methods
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for symbol"""
        try:
            if not self.client:
                # Return mock price for testing
                import random
                base_prices = {
                    'BTCUSDT': 50000, 'ETHUSDT': 3000, 'BNBUSDT': 300,
                    'ADAUSDT': 0.5, 'SOLUSDT': 100
                }
                base_price = base_prices.get(symbol, 100)
                return base_price * (1 + random.uniform(-0.01, 0.01))
            
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        
        except Exception as e:
            print(f"⚠️ Error getting price for {symbol}: {e}")
            return None
    
    def _validate_minimum_quantity(self, symbol: str, quantity: float) -> bool:
        """Validate quantity meets minimum requirements"""
        # This would check against exchange info in real implementation
        return quantity > 0.0001  # Basic validation
    
    def _format_quantity(self, symbol: str, quantity: float) -> str:
        """Format quantity according to symbol precision"""
        # This would use exchange info to get proper precision
        if 'BTC' in symbol:
            return f"{quantity:.6f}"
        elif 'ETH' in symbol:
            return f"{quantity:.5f}"
        else:
            return f"{quantity:.4f}"
    
    def _calculate_commission(self, fills: List[Dict]) -> float:
        """Calculate total commission from order fills"""
        if not fills:
            return 0.0
        
        total_commission = 0.0
        for fill in fills:
            commission = float(fill.get('commission', 0))
            # Convert to USDT if needed (simplified)
            total_commission += commission
        
        return total_commission
    
    def _mock_execute_entry(self, symbol: str, quantity: float, signal_type: str, current_price: float) -> Dict[str, Any]:
        """Mock entry execution for testing"""
        import random
        
        price = current_price or 100.0
        # Simulate slight slippage
        actual_price = price * (1 + random.uniform(-0.001, 0.001))
        
        return {
            'status': 'SUCCESS',
            'symbol': symbol,
            'quantity': quantity,
            'entry_price': actual_price,
            'order_id': f"mock_{int(time.time())}",
            'signal_type': signal_type,
            'timestamp': datetime.now().isoformat(),
            'commission': quantity * actual_price * 0.001  # 0.1% commission
        }
    
    def _mock_execute_exit(self, symbol: str, quantity: float, exit_price: float, entry_price: float, reason: str, signal_type: str) -> Dict[str, Any]:
        """Mock exit execution for testing"""
        import random
        
        actual_exit_price = exit_price or (entry_price * (1 + random.uniform(-0.05, 0.05)))
        
        # Calculate P&L
        if signal_type == "BUY_LONG":
            pnl_pct = ((actual_exit_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - actual_exit_price) / entry_price) * 100
        
        pnl_usd = (pnl_pct / 100) * quantity * entry_price
        commission = quantity * actual_exit_price * 0.001
        
        return {
            'status': 'SUCCESS',
            'symbol': symbol,
            'quantity': quantity,
            'entry_price': entry_price,
            'exit_price': actual_exit_price,
            'pnl_percent': pnl_pct,
            'pnl_usd': pnl_usd,
            'commission': commission,
            'net_pnl_usd': pnl_usd - commission,
            'reason': reason,
            'order_id': f"mock_exit_{int(time.time())}",
            'timestamp': datetime.now().isoformat(),
            'signal_type': signal_type
        }

# Legacy compatibility functions
def monitor_position(entry_price: float, symbol: str, client: Client, 
                    quantity: float = 0.001, confidence: float = 0.7) -> Dict[str, Any]:
    """Legacy function for backwards compatibility"""
    trader = EnhancedTrader(client)
    return trader.monitor_position_enhanced(
        entry_price=entry_price,
        symbol=symbol,
        quantity=quantity,
        signal_type="BUY_LONG",
        confidence=confidence
    )

def execute_entry(client: Client, symbol: str, quantity: float, signal_type: str) -> Dict[str, Any]:
    """Legacy function for backwards compatibility"""
    trader = EnhancedTrader(client)
    return trader.execute_entry(symbol, quantity, signal_type)

def execute_exit(client: Client, symbol: str, quantity: float, exit_price: float, 
                entry_price: float, reason: str) -> Dict[str, Any]:
    """Legacy function for backwards compatibility"""
    trader = EnhancedTrader(client)
    return trader.execute_exit(symbol, quantity, exit_price, entry_price, reason)

def get_account_balance(client: Client, asset: str = 'USDT') -> float:
    """Legacy function for backwards compatibility"""
    trader = EnhancedTrader(client)
    return trader.get_account_balance(asset)

def calculate_dynamic_position_size(account_balance: float, base_quantity: float, 
                                  confidence: float, volatility: float, 
                                  risk_percentage: float = 0.015) -> float:
    """Legacy function for backwards compatibility"""
    trader = EnhancedTrader()
    return trader.calculate_dynamic_position_size(
        account_balance, base_quantity, confidence, volatility, risk_percentage
    )

def validate_trade_parameters(symbol: str, quantity: float, price: float = None) -> Tuple[bool, str]:
    """Validate trade parameters before execution"""
    if not symbol:
        return False, "Symbol is required"
    
    if quantity <= 0:
        return False, "Quantity must be positive"
    
    if not symbol.endswith('USDT'):
        return False, "Only USDT pairs supported"
    
    if price is not None and price <= 0:
        return False, "Price must be positive"
    
    return True, ""

# Example usage and testing
if __name__ == "__main__":
    print("🚀 Enhanced Trader Module Test")
    print("=" * 50)
    
    # Initialize trader
    trader = EnhancedTrader()
    
    # Test dynamic position sizing
    account_balance = 10000.0
    base_quantity = 0.001
    confidence = 0.8
    volatility = 4.5
    
    position_size = trader.calculate_dynamic_position_size(
        account_balance, base_quantity, confidence, volatility
    )
    
    print(f"Account Balance: ${account_balance:,.2f}")
    print(f"Base Quantity: {base_quantity}")
    print(f"Confidence: {confidence:.1%}")
    print(f"Volatility: {volatility:.1f}%")
    print(f"Calculated Position Size: {position_size:.6f}")
    
    # Test dynamic exit levels
    exit_levels = trader.get_dynamic_exit_levels(confidence, volatility)
    print(f"\nDynamic Exit Levels:")
    print(f"Take Profit: {exit_levels['take_profit']:.1f}%")
    print(f"Stop Loss: {exit_levels['stop_loss']:.1f}%")
    print(f"Trailing Stop: {exit_levels['trailing_stop']:.1f}%")
    
    # Test mock trade execution
    print(f"\n🔄 Testing Mock Trade Execution:")
    
    entry_result = trader.execute_entry(
        symbol="BTCUSDT",
        quantity=position_size,
        signal_type="BUY_LONG",
        current_price=50000.0
    )
    
    print(f"Entry Result: {entry_result['status']}")
    if entry_result['status'] == 'SUCCESS':
        print(f"Entry Price: ${entry_result['entry_price']:.2f}")
        print(f"Quantity: {entry_result['quantity']:.6f}")
        
        # Test position monitoring (abbreviated for demo)
        print(f"\n📊 Starting Position Monitoring...")
        print(f"(This would normally run until exit conditions are met)")
        
        # Simulate exit after some conditions
        exit_result = trader.execute_exit(
            symbol="BTCUSDT",
            quantity=entry_result['quantity'],
            exit_price=51000.0,  # 2% profit
            entry_price=entry_result['entry_price'],
            reason="Test exit",
            signal_type="BUY_LONG"
        )
        
        print(f"Exit Result: {exit_result['status']}")
        if exit_result['status'] == 'SUCCESS':
            print(f"P&L: {exit_result['pnl_percent']:+.2f}%")
            print(f"P&L USD: ${exit_result['net_pnl_usd']:+.2f}")
    
    print("\n✅ Enhanced Trader Module Test Complete")