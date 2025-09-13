#!/usr/bin/env python3
"""
Virtual Trading Engine - Real market data, virtual trades, real performance tracking
Uses WebSocket price feeds to avoid API abuse while maintaining realistic trading simulation
"""

import time
import json
import asyncio
import websockets
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class VirtualTrade:
    """Virtual trade execution record"""
    id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    timestamp: float
    confidence: float
    signal_type: str  # 'traditional', 'atomic_swap', 'quantum'
    pnl: float = 0.0
    pnl_percentage: float = 0.0
    profitable: bool = False

class VirtualPortfolio:
    """Virtual portfolio tracking with real price updates"""
    
    def __init__(self, starting_balance: float = 10000.0):
        self.starting_balance = starting_balance
        self.current_balance = starting_balance
        self.virtual_positions = {}  # symbol -> {quantity, avg_price, total_cost}
        self.executed_trades = []
        self.price_feed = {}  # Real-time prices from WebSocket
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'roi': 0.0,
            'sharpe_ratio': 0.0
        }
        
    def update_price(self, symbol: str, price: float):
        """Update real-time price from WebSocket feed"""
        self.price_feed[symbol] = {
            'price': price,
            'timestamp': time.time()
        }
        
        # Update P&L for existing positions
        self._update_position_pnl()
    
    def _update_position_pnl(self):
        """Update P&L for all positions with current prices"""
        total_pnl = 0.0
        
        for symbol, position in self.virtual_positions.items():
            if symbol in self.price_feed:
                current_price = self.price_feed[symbol]['price']
                quantity = position['quantity']
                avg_price = position['avg_price']
                
                # Calculate unrealized P&L
                pnl = (current_price - avg_price) * quantity
                pnl_percentage = ((current_price - avg_price) / avg_price) * 100
                
                position['current_price'] = current_price
                position['pnl'] = pnl
                position['pnl_percentage'] = pnl_percentage
                position['market_value'] = current_price * quantity
                
                total_pnl += pnl
        
        self.performance_metrics['total_pnl'] = total_pnl
        self.performance_metrics['roi'] = (total_pnl / self.starting_balance) * 100
    
    def execute_virtual_trade(self, signal: Dict[str, Any]) -> VirtualTrade:
        """Execute virtual trade based on signal"""
        try:
            symbol = signal['symbol']
            signal_type = signal['signal']
            confidence = signal.get('conf', 0.5)
            price = signal.get('price', 0)
            signal_method = signal.get('type', 'traditional')
            
            if price <= 0:
                return None
            
            # Calculate position size based on confidence and available balance
            trade_amount = min(500, self.current_balance * 0.1 * confidence)  # Max $500 or 10% of balance
            
            if signal_type == 'BUY':
                if self.current_balance < trade_amount:
                    return None  # Insufficient balance
                
                quantity = trade_amount / price
                
                # Update virtual portfolio
                if symbol in self.virtual_positions:
                    # Add to existing position
                    pos = self.virtual_positions[symbol]
                    total_quantity = pos['quantity'] + quantity
                    total_cost = pos['total_cost'] + trade_amount
                    pos['quantity'] = total_quantity
                    pos['avg_price'] = total_cost / total_quantity
                    pos['total_cost'] = total_cost
                else:
                    # New position
                    self.virtual_positions[symbol] = {
                        'quantity': quantity,
                        'avg_price': price,
                        'total_cost': trade_amount,
                        'current_price': price,
                        'pnl': 0.0,
                        'pnl_percentage': 0.0
                    }
                
                self.current_balance -= trade_amount
                
            elif signal_type == 'SELL':
                if symbol not in self.virtual_positions:
                    return None  # No position to sell
                
                position = self.virtual_positions[symbol]
                quantity = position['quantity'] * 0.5  # Sell 50% of position
                trade_value = quantity * price
                
                # Update position
                position['quantity'] -= quantity
                position['total_cost'] -= (position['total_cost'] * 0.5)
                
                if position['quantity'] <= 0.001:
                    del self.virtual_positions[symbol]  # Close position
                
                self.current_balance += trade_value
                
            elif signal_type.startswith('SWAP_TO_'):
                # Virtual atomic swap
                from_asset = signal.get('from_asset', symbol.split('/')[0])
                to_asset = signal.get('to_asset', symbol.split('/')[1])
                
                # For simplicity, treat as sell from_asset, buy to_asset
                from_symbol = f"{from_asset}/USDT"
                to_symbol = f"{to_asset}/USDT"
                
                if from_symbol in self.virtual_positions:
                    from_pos = self.virtual_positions[from_symbol]
                    swap_quantity = from_pos['quantity'] * 0.3  # Swap 30%
                    swap_value = swap_quantity * price
                    
                    # Reduce from_asset position
                    from_pos['quantity'] -= swap_quantity
                    if from_pos['quantity'] <= 0.001:
                        del self.virtual_positions[from_symbol]
                    
                    # Add to_asset position (estimate price)
                    to_price = price * 0.98  # Assume small spread
                    to_quantity = swap_value / to_price
                    
                    if to_symbol in self.virtual_positions:
                        to_pos = self.virtual_positions[to_symbol]
                        total_qty = to_pos['quantity'] + to_quantity
                        total_cost = to_pos['total_cost'] + swap_value
                        to_pos['quantity'] = total_qty
                        to_pos['avg_price'] = total_cost / total_qty
                        to_pos['total_cost'] = total_cost
                    else:
                        self.virtual_positions[to_symbol] = {
                            'quantity': to_quantity,
                            'avg_price': to_price,
                            'total_cost': swap_value,
                            'current_price': to_price
                        }
                    
                    quantity = swap_quantity
                else:
                    return None  # No position to swap
            
            else:
                return None  # HOLD signals don't execute
            
            # Create trade record
            virtual_trade = VirtualTrade(
                id=f"virtual_{int(time.time())}_{len(self.executed_trades)}",
                symbol=symbol,
                side=signal_type.lower(),
                quantity=quantity,
                entry_price=price,
                current_price=price,
                timestamp=time.time(),
                confidence=confidence,
                signal_type=signal_method
            )
            
            self.executed_trades.append(virtual_trade)
            self.performance_metrics['total_trades'] += 1
            
            # Keep only recent trades
            if len(self.executed_trades) > 200:
                self.executed_trades = self.executed_trades[-100:]
            
            print(f"💰 VIRTUAL TRADE: {signal_type} {quantity:.6f} {symbol} @ ${price:,.2f} (confidence: {confidence:.1%})")
            
            return virtual_trade
            
        except Exception as e:
            print(f"❌ Virtual trade error: {e}")
            return None
    
    def calculate_performance(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            if not self.executed_trades:
                return self.performance_metrics
            
            # Update P&L for all positions
            self._update_position_pnl()
            
            # Calculate trade performance
            profitable_trades = 0
            total_realized_pnl = 0.0
            
            for trade in self.executed_trades:
                # Update trade P&L with current price
                if trade.symbol in self.price_feed:
                    current_price = self.price_feed[trade.symbol]['price']
                    trade.current_price = current_price
                    
                    if trade.side == 'buy':
                        trade.pnl = (current_price - trade.entry_price) * trade.quantity
                    elif trade.side == 'sell':
                        trade.pnl = (trade.entry_price - current_price) * trade.quantity
                    
                    trade.pnl_percentage = (trade.pnl / (trade.entry_price * trade.quantity)) * 100
                    trade.profitable = trade.pnl > 0
                    
                    if trade.profitable:
                        profitable_trades += 1
                    
                    total_realized_pnl += trade.pnl
            
            # Update performance metrics
            self.performance_metrics.update({
                'total_trades': len(self.executed_trades),
                'winning_trades': profitable_trades,
                'losing_trades': len(self.executed_trades) - profitable_trades,
                'win_rate': (profitable_trades / len(self.executed_trades)) * 100 if self.executed_trades else 0,
                'total_pnl': self.performance_metrics['total_pnl'],  # Unrealized from positions
                'realized_pnl': total_realized_pnl,
                'roi': ((self.current_balance + self.performance_metrics['total_pnl'] - self.starting_balance) / self.starting_balance) * 100,
                'total_portfolio_value': self.current_balance + sum(pos.get('market_value', 0) for pos in self.virtual_positions.values())
            })
            
            return self.performance_metrics
            
        except Exception as e:
            print(f"❌ Performance calculation error: {e}")
            return self.performance_metrics
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get complete portfolio summary"""
        try:
            self.calculate_performance()
            
            return {
                'balance': {
                    'starting_balance': self.starting_balance,
                    'current_cash': round(self.current_balance, 2),
                    'position_value': round(sum(pos.get('market_value', 0) for pos in self.virtual_positions.values()), 2),
                    'total_portfolio_value': round(self.performance_metrics['total_portfolio_value'], 2)
                },
                'positions': dict(self.virtual_positions),
                'performance': self.performance_metrics,
                'recent_trades': [
                    {
                        'id': trade.id,
                        'symbol': trade.symbol,
                        'side': trade.side,
                        'quantity': trade.quantity,
                        'entry_price': trade.entry_price,
                        'current_price': trade.current_price,
                        'pnl': round(trade.pnl, 2),
                        'pnl_percentage': round(trade.pnl_percentage, 2),
                        'profitable': trade.profitable,
                        'confidence': trade.confidence,
                        'signal_type': trade.signal_type,
                        'timestamp': trade.timestamp
                    }
                    for trade in self.executed_trades[-20:]
                ],
                'last_updated': time.time()
            }
            
        except Exception as e:
            return {'error': f'Portfolio summary failed: {e}'}

class WebSocketPriceFeed:
    """WebSocket price feed for real-time market data"""
    
    def __init__(self, portfolio: VirtualPortfolio):
        self.portfolio = portfolio
        self.connected = False
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT']
        
    async def connect_binance_stream(self):
        """Connect to Binance WebSocket for real-time prices"""
        try:
            # Binance WebSocket URL for ticker streams
            streams = [f"{symbol.lower().replace('/', '')}@ticker" for symbol in self.symbols]
            ws_url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"
            
            async with websockets.connect(ws_url) as websocket:
                self.connected = True
                print("✅ WebSocket connected to Binance price feed")
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        # Handle single ticker or combined stream
                        if isinstance(data, list):
                            for ticker in data:
                                self._process_ticker(ticker)
                        else:
                            self._process_ticker(data)
                            
                    except Exception as e:
                        print(f"❌ WebSocket message error: {e}")
                        
        except Exception as e:
            print(f"❌ WebSocket connection error: {e}")
            self.connected = False
    
    def _process_ticker(self, ticker_data):
        """Process ticker data and update portfolio"""
        try:
            symbol = ticker_data.get('s', '').replace('USDT', '/USDT')
            price = float(ticker_data.get('c', 0))  # Current price
            
            if symbol in self.symbols and price > 0:
                self.portfolio.update_price(symbol, price)
                
        except Exception as e:
            print(f"❌ Ticker processing error: {e}")

class VirtualTradingEngine:
    """Complete virtual trading engine with real market data"""
    
    def __init__(self):
        self.portfolio = VirtualPortfolio()
        self.price_feed = WebSocketPriceFeed(self.portfolio)
        self.signal_trackers = {
            'traditional': VirtualPortfolio(10000),
            'quantum': VirtualPortfolio(10000), 
            'sentiment': VirtualPortfolio(10000)
        }
        self.last_execution_check = 0
        
    async def start_price_feed(self):
        """Start real-time price feed"""
        try:
            await self.price_feed.connect_binance_stream()
        except Exception as e:
            print(f"❌ Price feed error: {e}")
    
    def execute_virtual_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute virtual trade on signal"""
        try:
            # Execute on main portfolio
            main_trade = self.portfolio.execute_virtual_trade(signal)
            
            # Execute on individual signal type trackers for comparison
            signal_type = signal.get('type', 'traditional')
            if signal_type in self.signal_trackers:
                tracker_trade = self.signal_trackers[signal_type].execute_virtual_trade(signal)
            
            if main_trade:
                return {
                    'executed': True,
                    'trade': {
                        'id': main_trade.id,
                        'symbol': main_trade.symbol,
                        'side': main_trade.side,
                        'quantity': main_trade.quantity,
                        'price': main_trade.entry_price,
                        'confidence': main_trade.confidence,
                        'signal_type': main_trade.signal_type,
                        'timestamp': main_trade.timestamp,
                        'virtual': True
                    },
                    'portfolio_after': self.portfolio.current_balance,
                    'positions_count': len(self.portfolio.virtual_positions)
                }
            else:
                return {'executed': False, 'reason': 'Trade conditions not met'}
                
        except Exception as e:
            return {'executed': False, 'error': str(e)}
    
    def get_performance_comparison(self) -> Dict[str, Any]:
        """Compare performance of different signal types"""
        try:
            main_perf = self.portfolio.calculate_performance()
            
            comparison = {
                'main_portfolio': main_perf,
                'signal_type_comparison': {}
            }
            
            for signal_type, tracker in self.signal_trackers.items():
                tracker_perf = tracker.calculate_performance()
                comparison['signal_type_comparison'][signal_type] = tracker_perf
            
            # Rank signal types by performance
            rankings = []
            for signal_type, perf in comparison['signal_type_comparison'].items():
                rankings.append({
                    'signal_type': signal_type,
                    'roi': perf['roi'],
                    'win_rate': perf['win_rate'],
                    'total_trades': perf['total_trades'],
                    'performance_score': (perf['win_rate'] / 100) * 0.6 + (max(0, perf['roi']) / 100) * 0.4
                })
            
            rankings.sort(key=lambda x: x['performance_score'], reverse=True)
            comparison['performance_rankings'] = rankings
            
            return comparison
            
        except Exception as e:
            return {'error': f'Performance comparison failed: {e}'}

# Global virtual trading engine
virtual_engine = VirtualTradingEngine()