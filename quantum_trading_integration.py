#!/usr/bin/env python3
"""
Quantum Trading Integration
===========================

Integration module for quantum trading engine with live trading capabilities.
Provides position management, trade execution, and performance tracking.

Company: Rondanini Publishing Ltd.
Website: https://www.rondanini.net

MIT License
Copyright (c) 2025 Rondanini Publishing Ltd.
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False

class QuantumTrader:
    """
    Quantum trader that executes trades based on quantum analysis results.
    Manages positions, tracks performance, and provides trading functionality.
    """
    
    def __init__(self, binance_client: Optional[Client] = None):
        self.client = binance_client
        self.active_quantum_positions = {}
        self.closed_positions = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl_pct': 0.0,
            'total_pnl_usd': 0.0
        }
        
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Initialize quantum trades log
        self.quantum_trades_log = 'logs/quantum_trades.csv'
        self._initialize_quantum_log()
    
    def _initialize_quantum_log(self):
        """Initialize quantum trades CSV log file"""
        if not os.path.exists(self.quantum_trades_log):
            with open(self.quantum_trades_log, 'w') as f:
                f.write("timestamp,position_id,symbol,direction,entry_price,quantity,quantum_confidence,strategy,status,pnl_pct,pnl_usd,exit_price,exit_time,exit_reason\n")
    
    def execute_quantum_signal(self, quantum_result: Dict[str, Any], symbol: str, 
                             manual_override: bool = False) -> Dict[str, Any]:
        """
        Execute a quantum trading signal.
        
        Args:
            quantum_result: Dictionary containing quantum analysis results
            symbol: Trading symbol (e.g., 'BTCUSDT')
            manual_override: Allow trading with lower confidence
            
        Returns:
            Dictionary with execution results
        """
        
        # Extract quantum parameters
        signal = quantum_result.get('quantum_signal', 'HOLD')
        confidence = quantum_result.get('quantum_confidence', 0.0)
        position_size = quantum_result.get('quantum_position_size', 0.0)
        
        # Safety checks
        if signal == 'HOLD':
            return {
                'status': 'HOLD',
                'reason': 'Quantum signal is HOLD - no action taken',
                'signal': signal,
                'confidence': confidence
            }
        
        if confidence < 0.5 and not manual_override:
            return {
                'status': 'SKIPPED',
                'reason': f'Quantum confidence too low: {confidence:.1%}',
                'signal': signal,
                'confidence': confidence
            }
        
        if not self.client:
            # Demo mode - simulate trade
            return self._simulate_trade(quantum_result, symbol)
        
        # Live trading
        try:
            return self._execute_live_trade(quantum_result, symbol)
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Trade execution failed: {str(e)}',
                'signal': signal,
                'confidence': confidence
            }
    
    def _simulate_trade(self, quantum_result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Simulate a quantum trade for demo purposes"""
        
        # Generate position ID
        position_id = str(uuid.uuid4())
        
        # Mock current price
        mock_prices = {
            'BTCUSDT': 50000.0,
            'ETHUSDT': 3000.0,
            'BNBUSDT': 400.0,
            'ADAUSDT': 1.5,
            'SOLUSDT': 100.0,
            'DOGEUSDT': 0.3
        }
        
        entry_price = mock_prices.get(symbol, 1000.0)
        quantity = quantum_result.get('quantum_position_size', 100.0) / entry_price
        
        # Create position
        position = {
            'position_id': position_id,
            'symbol': symbol,
            'direction': quantum_result.get('quantum_signal', 'BUY_LONG'),
            'entry_price': entry_price,
            'quantity': quantity,
            'quantum_confidence': quantum_result.get('quantum_confidence', 0.5),
            'strategy': 'Quantum',
            'entry_time': datetime.now(),
            'stop_loss': quantum_result.get('quantum_stop_loss', 8.0),
            'take_profit': quantum_result.get('quantum_take_profit', 12.0),
            'holding_time': quantum_result.get('quantum_holding_time', 120)
        }
        
        # Add to active positions
        self.active_quantum_positions[position_id] = position
        
        # Log the trade
        self._log_quantum_trade(position, 'ENTRY')
        
        return {
            'status': 'SUCCESS',
            'position_id': position_id,
            'entry_price': entry_price,
            'quantity': quantity,
            'symbol': symbol,
            'direction': position['direction'],
            'quantum_confidence': position['quantum_confidence'],
            'message': 'Demo trade executed successfully'
        }
    
    def _execute_live_trade(self, quantum_result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Execute a live trade using Binance API"""
        
        if not BINANCE_AVAILABLE:
            return {
                'status': 'ERROR',
                'message': 'Binance library not available for live trading'
            }
        
        try:
            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            # Calculate quantity based on position size
            position_size_usd = quantum_result.get('quantum_position_size', 100.0)
            quantity = position_size_usd / current_price
            
            # Round quantity to appropriate precision
            quantity = round(quantity, 8)
            
            signal = quantum_result.get('quantum_signal', 'BUY_LONG')
            side = 'BUY' if signal == 'BUY_LONG' else 'SELL'
            
            # Place market order
            order = self.client.order_market(
                symbol=symbol,
                side=side,
                quantity=quantity
            )
            
            # Generate position ID
            position_id = str(uuid.uuid4())
            
            # Create position record
            position = {
                'position_id': position_id,
                'symbol': symbol,
                'direction': signal,
                'entry_price': current_price,
                'quantity': quantity,
                'quantum_confidence': quantum_result.get('quantum_confidence', 0.5),
                'strategy': 'Quantum',
                'entry_time': datetime.now(),
                'stop_loss': quantum_result.get('quantum_stop_loss', 8.0),
                'take_profit': quantum_result.get('quantum_take_profit', 12.0),
                'holding_time': quantum_result.get('quantum_holding_time', 120),
                'binance_order_id': order['orderId']
            }
            
            # Add to active positions
            self.active_quantum_positions[position_id] = position
            
            # Log the trade
            self._log_quantum_trade(position, 'ENTRY')
            
            return {
                'status': 'SUCCESS',
                'position_id': position_id,
                'entry_price': current_price,
                'quantity': quantity,
                'symbol': symbol,
                'direction': signal,
                'quantum_confidence': position['quantum_confidence'],
                'binance_order_id': order['orderId'],
                'message': 'Live trade executed successfully'
            }
            
        except BinanceAPIException as e:
            return {
                'status': 'ERROR',
                'message': f'Binance API error: {e.message}',
                'code': e.code
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Unexpected error: {str(e)}'
            }
    
    def monitor_quantum_positions(self) -> Dict[str, Any]:
        """Monitor all active quantum positions and execute exits if needed"""
        
        if not self.active_quantum_positions:
            return {
                'status': 'NO_POSITIONS',
                'message': 'No active quantum positions to monitor'
            }
        
        results = []
        closed_count = 0
        
        for position_id, position in list(self.active_quantum_positions.items()):
            # Get current price
            current_price = self.get_current_price(position['symbol'])
            
            if current_price is None:
                continue
            
            # Calculate P&L
            pnl_data = self.calculate_position_pnl(position, current_price)
            
            # Check exit conditions
            should_exit, exit_reason = self._check_exit_conditions(position, current_price, pnl_data)
            
            if should_exit:
                # Close position
                exit_result = self._close_position(position_id, position, current_price, exit_reason)
                results.append(exit_result)
                closed_count += 1
            else:
                # Continue monitoring
                results.append({
                    'position_id': position_id,
                    'symbol': position['symbol'],
                    'direction': position['direction'],
                    'current_pnl_pct': pnl_data['pnl_pct'],
                    'current_pnl_usd': pnl_data['pnl_usd'],
                    'time_held_minutes': pnl_data['time_held_minutes'],
                    'action': 'MONITORING'
                })
        
        return {
            'status': 'SUCCESS',
            'monitored': len(results),
            'closed': closed_count,
            'results': results
        }
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            if self.client:
                ticker = self.client.get_symbol_ticker(symbol=symbol)
                return float(ticker['price'])
            else:
                # Mock prices for demo
                mock_prices = {
                    'BTCUSDT': 50000.0,
                    'ETHUSDT': 3000.0,
                    'BNBUSDT': 400.0,
                    'ADAUSDT': 1.5,
                    'SOLUSDT': 100.0,
                    'DOGEUSDT': 0.3
                }
                return mock_prices.get(symbol, 1000.0)
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return None
    
    def calculate_position_pnl(self, position: Dict[str, Any], current_price: float) -> Dict[str, Any]:
        """Calculate P&L for a position"""
        
        entry_price = position['entry_price']
        direction = position['direction']
        
        # Calculate percentage change
        if direction == 'BUY_LONG':
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # BUY_SHORT
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Calculate USD P&L
        quantity = position['quantity']
        pnl_usd = (current_price - entry_price) * quantity
        if direction == 'BUY_SHORT':
            pnl_usd = -pnl_usd
        
        # Calculate time held
        entry_time = position['entry_time']
        if isinstance(entry_time, str):
            entry_time = datetime.fromisoformat(entry_time)
        
        time_held = datetime.now() - entry_time
        time_held_minutes = time_held.total_seconds() / 60
        
        return {
            'pnl_pct': pnl_pct,
            'pnl_usd': pnl_usd,
            'time_held_minutes': time_held_minutes,
            'current_price': current_price
        }
    
    def _check_exit_conditions(self, position: Dict[str, Any], current_price: float, 
                             pnl_data: Dict[str, Any]) -> tuple:
        """Check if position should be exited"""
        
        pnl_pct = pnl_data['pnl_pct']
        time_held_minutes = pnl_data['time_held_minutes']
        
        # Stop loss
        if pnl_pct <= -position['stop_loss']:
            return True, 'STOP_LOSS'
        
        # Take profit
        if pnl_pct >= position['take_profit']:
            return True, 'TAKE_PROFIT'
        
        # Time limit
        if time_held_minutes >= position['holding_time']:
            return True, 'TIME_LIMIT'
        
        # Emergency exit (large adverse move)
        if pnl_pct <= -20.0:
            return True, 'EMERGENCY_EXIT'
        
        return False, None
    
    def _close_position(self, position_id: str, position: Dict[str, Any], 
                       exit_price: float, exit_reason: str) -> Dict[str, Any]:
        """Close a quantum position"""
        
        try:
            # Calculate final P&L
            pnl_data = self.calculate_position_pnl(position, exit_price)
            
            # Execute exit order if live trading
            if self.client:
                symbol = position['symbol']
                quantity = position['quantity']
                direction = position['direction']
                
                # Reverse the original order
                side = 'SELL' if direction == 'BUY_LONG' else 'BUY'
                
                try:
                    exit_order = self.client.order_market(
                        symbol=symbol,
                        side=side,
                        quantity=quantity
                    )
                    exit_order_id = exit_order['orderId']
                except Exception as e:
                    exit_order_id = None
                    print(f"Failed to execute exit order: {e}")
            else:
                exit_order_id = None
            
            # Update position with exit info
            position['exit_price'] = exit_price
            position['exit_time'] = datetime.now()
            position['exit_reason'] = exit_reason
            position['pnl_pct'] = pnl_data['pnl_pct']
            position['pnl_usd'] = pnl_data['pnl_usd']
            position['exit_order_id'] = exit_order_id
            
            # Move to closed positions
            self.closed_positions.append(position)
            
            # Remove from active positions
            del self.active_quantum_positions[position_id]
            
            # Log the exit
            self._log_quantum_trade(position, 'EXIT')
            
            # Update performance metrics
            self._update_performance_metrics(position)
            
            return {
                'position_id': position_id,
                'symbol': position['symbol'],
                'direction': position['direction'],
                'pnl_pct': pnl_data['pnl_pct'],
                'pnl_usd': pnl_data['pnl_usd'],
                'exit_reason': exit_reason,
                'action': 'CLOSED'
            }
            
        except Exception as e:
            return {
                'position_id': position_id,
                'symbol': position['symbol'],
                'error': str(e),
                'action': 'CLOSE_FAILED'
            }
    
    def _log_quantum_trade(self, position: Dict[str, Any], action: str):
        """Log quantum trade to CSV file"""
        
        try:
            with open(self.quantum_trades_log, 'a') as f:
                timestamp = datetime.now().isoformat()
                position_id = position['position_id']
                symbol = position['symbol']
                direction = position['direction']
                entry_price = position['entry_price']
                quantity = position['quantity']
                quantum_confidence = position['quantum_confidence']
                strategy = position['strategy']
                
                if action == 'ENTRY':
                    f.write(f"{timestamp},{position_id},{symbol},{direction},{entry_price},{quantity},{quantum_confidence},{strategy},ENTRY,,,,,\n")
                elif action == 'EXIT':
                    exit_price = position.get('exit_price', '')
                    exit_time = position.get('exit_time', '')
                    exit_reason = position.get('exit_reason', '')
                    pnl_pct = position.get('pnl_pct', 0.0)
                    pnl_usd = position.get('pnl_usd', 0.0)
                    
                    if isinstance(exit_time, datetime):
                        exit_time = exit_time.isoformat()
                    
                    f.write(f"{timestamp},{position_id},{symbol},{direction},{entry_price},{quantity},{quantum_confidence},{strategy},EXIT,{pnl_pct},{pnl_usd},{exit_price},{exit_time},{exit_reason}\n")
                    
        except Exception as e:
            print(f"Error logging quantum trade: {e}")
    
    def _update_performance_metrics(self, position: Dict[str, Any]):
        """Update performance metrics after closing a position"""
        
        pnl_pct = position.get('pnl_pct', 0.0)
        pnl_usd = position.get('pnl_usd', 0.0)
        
        self.performance_metrics['total_trades'] += 1
        self.performance_metrics['total_pnl_pct'] += pnl_pct
        self.performance_metrics['total_pnl_usd'] += pnl_usd
        
        if pnl_pct > 0:
            self.performance_metrics['winning_trades'] += 1
        else:
            self.performance_metrics['losing_trades'] += 1
    
    def get_quantum_performance(self) -> Dict[str, Any]:
        """Get quantum trading performance metrics"""
        
        try:
            total_trades = self.performance_metrics['total_trades']
            
            if total_trades == 0:
                return {
                    'status': 'NO_DATA',
                    'message': 'No quantum trades completed yet',
                    'total_trades': 0,
                    'active_trades': len(self.active_quantum_positions)
                }
            
            winning_trades = self.performance_metrics['winning_trades']
            losing_trades = self.performance_metrics['losing_trades']
            total_pnl_pct = self.performance_metrics['total_pnl_pct']
            total_pnl_usd = self.performance_metrics['total_pnl_usd']
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
            avg_pnl_per_trade = total_pnl_pct / total_trades if total_trades > 0 else 0.0
            
            # Calculate average quantum confidence
            avg_quantum_confidence = 0.0
            if self.closed_positions:
                total_confidence = sum(pos.get('quantum_confidence', 0.5) for pos in self.closed_positions)
                avg_quantum_confidence = total_confidence / len(self.closed_positions)
            
            return {
                'status': 'SUCCESS',
                'total_trades': total_trades,
                'closed_trades': len(self.closed_positions),
                'active_trades': len(self.active_quantum_positions),
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_pnl_pct': total_pnl_pct,
                'total_pnl_usd': total_pnl_usd,
                'avg_pnl_per_trade': avg_pnl_per_trade,
                'avg_quantum_confidence': avg_quantum_confidence
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'message': f'Error calculating performance: {str(e)}',
                'total_trades': self.performance_metrics['total_trades'],
                'active_trades': len(self.active_quantum_positions)
            }

def get_quantum_trader(binance_client: Optional[Client] = None) -> QuantumTrader:
    """
    Factory function to create and return a QuantumTrader instance.
    
    Args:
        binance_client: Optional Binance client for live trading
        
    Returns:
        QuantumTrader instance
    """
    return QuantumTrader(binance_client)

# Test function
def test_quantum_trader():
    """Test the quantum trader with sample data"""
    
    # Create trader (demo mode)
    trader = get_quantum_trader()
    
    # Sample quantum result
    quantum_result = {
        'quantum_signal': 'BUY_LONG',
        'quantum_confidence': 0.75,
        'quantum_position_size': 1000.0,
        'quantum_stop_loss': 8.0,
        'quantum_take_profit': 12.0,
        'quantum_holding_time': 120
    }
    
    # Execute trade
    result = trader.execute_quantum_signal(quantum_result, 'BTCUSDT')
    
    print("🔬 Quantum Trader Test Results:")
    print(f"Status: {result['status']}")
    print(f"Position ID: {result.get('position_id', 'N/A')}")
    print(f"Entry Price: ${result.get('entry_price', 0):,.2f}")
    print("✅ Quantum trader working correctly!")
    
    return result

if __name__ == "__main__":
    test_quantum_trader()
