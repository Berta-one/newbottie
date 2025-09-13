#!/usr/bin/env python3
"""
Simple Virtual Trading - No crashes, just score keeping
"""

import time
from datetime import datetime

class SimpleVirtualTrader:
    """Simple virtual trading that cannot crash"""
    
    def __init__(self):
        self.balance = 10000.0
        self.trades = []
        self.positions = {}
        
    def execute_virtual_trade(self, signal):
        """Execute simple virtual trade"""
        try:
            symbol = signal['symbol']
            signal_type = signal['signal']
            price = signal.get('price', 0)
            confidence = signal.get('conf', 0.5)
            
            if signal_type == 'BUY' and self.balance > 100:
                # Virtual BUY
                trade_amount = min(200, self.balance * 0.1)
                quantity = trade_amount / price
                
                self.balance -= trade_amount
                
                if symbol in self.positions:
                    self.positions[symbol]['quantity'] += quantity
                else:
                    self.positions[symbol] = {'quantity': quantity, 'avg_price': price}
                
                trade = {
                    'id': f"virtual_{len(self.trades)}",
                    'symbol': symbol,
                    'side': 'buy',
                    'quantity': quantity,
                    'price': price,
                    'value': trade_amount,
                    'confidence': confidence,
                    'timestamp': time.time(),
                    'virtual': True
                }
                
                self.trades.append(trade)
                return trade
                
            elif signal_type == 'SELL' and symbol in self.positions:
                # Virtual SELL
                pos = self.positions[symbol]
                sell_qty = pos['quantity'] * 0.5  # Sell 50%
                sell_value = sell_qty * price
                
                pos['quantity'] -= sell_qty
                if pos['quantity'] <= 0.001:
                    del self.positions[symbol]
                
                self.balance += sell_value
                
                trade = {
                    'id': f"virtual_{len(self.trades)}",
                    'symbol': symbol,
                    'side': 'sell',
                    'quantity': sell_qty,
                    'price': price,
                    'value': sell_value,
                    'confidence': confidence,
                    'timestamp': time.time(),
                    'virtual': True
                }
                
                self.trades.append(trade)
                return trade
            
            return None
            
        except Exception as e:
            print(f"❌ Simple virtual trade error: {e}")
            return None
    
    def get_summary(self):
        """Get simple portfolio summary"""
        try:
            total_trades = len(self.trades)
            winning_trades = sum(1 for t in self.trades if t.get('value', 0) > 100)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'balance': round(self.balance, 2),
                'positions': len(self.positions),
                'total_trades': total_trades,
                'win_rate': round(win_rate, 1),
                'recent_trades': self.trades[-5:] if self.trades else []
            }
        except Exception as e:
            return {'error': str(e)}

# Global simple virtual trader
simple_virtual = SimpleVirtualTrader()